import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

APP_NAME = os.getenv("APP_NAME", "QueueLess")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./queueless.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine_kwargs = {
    "connect_args": connect_args,
    "pool_pre_ping": True,
}

if not DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 5,
        "pool_recycle": 1800,
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

class Service(Base):
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    location: Mapped[str] = mapped_column(String(100))
    average_minutes: Mapped[int] = mapped_column(Integer, default=3)

class Token(Base):
    __tablename__ = "tokens"

    _table_args_ = (
        UniqueConstraint(
            "service_id",
            "token_number",
            name="uq_token_service_number"
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    token_number: Mapped[int] = mapped_column(Integer)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="waiting", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    called_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

Base.metadata.create_all(engine)

def seed_services() -> None:
    with SessionLocal() as db:
        if db.scalar(select(Service.id).limit(1)) is not None:
            return
        db.add_all([
            Service(name="Bill", location="Reception", average_minutes=4),
            Service(name="Certificate Section", location="Counter 1", average_minutes=3),
            Service(name="Aadhar verify", location="Counter 1", average_minutes=5),
            Service(name="E-seva", location="Counter 2", average_minutes=2),
            Service(name="Banking", location="Counrter 3", average_minutes=2),
        ])
        db.commit()

seed_services()
app = FastAPI(title=APP_NAME, version="1.0.0")
frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/frontend", StaticFiles(directory=str(frontend_dir)), name="frontend")
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
Instrumentator().instrument(app).expose(app)

class TokenCreate(BaseModel):
    service_id: int = Field(gt=0)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
        return {
            "status": "ok",
            "service": APP_NAME,
            "database": "ok"
        }
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )

@app.get("/api/services")
def services(db: Session = Depends(get_db)):
    rows = db.scalars(select(Service).order_by(Service.id)).all()
    return [{"id": s.id, "name": s.name, "location": s.location, "average_minutes": s.average_minutes} for s in rows]

@app.post("/api/tokens")
def create_token(payload: TokenCreate, db: Session = Depends(get_db)):
    service = db.get(Service, payload.service_id)
    if not service:
        raise HTTPException(404, "Service not found")
    last = db.scalar(select(func.max(Token.token_number)).where(Token.service_id == service.id)) or 0
    token = Token(token_number=last + 1, service_id=service.id)
    db.add(token); db.commit(); db.refresh(token)
    position = db.scalar(select(func.count(Token.id)).where(Token.service_id == service.id, Token.status == "waiting", Token.id <= token.id)) or 1
    return {"id": token.id, "token": f"A{token.token_number:02d}", "service_id": service.id, "service": service.name, "status": token.status, "people_ahead": max(0, position - 1), "estimated_wait_minutes": max(0, position - 1) * service.average_minutes}

@app.get("/api/queues/{service_id}")
def queue_status(service_id: int, db: Session = Depends(get_db)):
    service = db.get(Service, service_id)
    if not service: raise HTTPException(404, "Service not found")
    current = db.scalar(select(Token).where(Token.service_id == service_id, Token.status == "serving").order_by(Token.token_number.desc()))
    waiting = db.scalars(select(Token).where(Token.service_id == service_id, Token.status == "waiting").order_by(Token.token_number)).all()
    return {"service_id": service_id, "service": service.name, "current_token": f"A{current.token_number:02d}" if current else None, "waiting_count": len(waiting), "waiting_tokens": [f"A{x.token_number:02d}" for x in waiting], "average_minutes": service.average_minutes}

@app.post("/api/queues/{service_id}/next")
def call_next(service_id: int, db: Session = Depends(get_db)):
    service = db.get(Service, service_id)
    if not service: raise HTTPException(404, "Service not found")
    current = db.scalar(select(Token).where(Token.service_id == service_id, Token.status == "serving").order_by(Token.token_number.desc()))
    if current:
        current.status = "completed"; current.completed_at = datetime.now(timezone.utc)
    next_token = db.scalar(select(Token).where(Token.service_id == service_id, Token.status == "waiting").order_by(Token.token_number))
    if not next_token:
        db.commit(); return {"message": "Queue is empty", "current_token": None}
    next_token.status = "serving"; next_token.called_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Next customer called", "current_token": f"A{next_token.token_number:02d}", "token_id": next_token.id}

@app.post("/api/tokens/{token_id}/cancel")
def cancel_token(token_id: int, db: Session = Depends(get_db)):
    token = db.get(Token, token_id)
    if not token: raise HTTPException(404, "Token not found")
    if token.status != "waiting": raise HTTPException(400, "Only waiting tokens can be cancelled")
    token.status = "cancelled"; db.commit()
    return {"message": "Token cancelled"}

@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    waiting = db.scalar(select(func.count(Token.id)).where(Token.status == "waiting")) or 0
    serving = db.scalar(select(func.count(Token.id)).where(Token.status == "serving")) or 0
    completed = db.scalar(select(func.count(Token.id)).where(Token.status == "completed")) or 0
    return {"waiting": waiting, "serving": serving, "completed": completed, "total": waiting + serving + completed}

@app.get("/")
def root():
    from fastapi.responses import FileResponse
    return FileResponse(frontend_dir / "index.html")
