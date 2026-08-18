"""QueueLess event-driven serverless function."""

import logging
from typing import Any

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("queueless-serverless")

app = FastAPI(title="QueueLess Serverless")


def handle(event: dict[str, Any]) -> dict[str, Any]:
    token = event.get("token", "unknown")
    duration = float(event.get("service_time_seconds", 0))
    counter = event.get("counter", "unknown")

    result = {
        "event": "queue.completed",
        "token": token,
        "counter": counter,
        "service_time_seconds": duration,
        "metric": "service_duration",
    }

    logger.info(
        "Queue completed token=%s duration=%s counter=%s",
        token,
        duration,
        counter,
    )

    return result


@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "queueless-serverless",
    }


@app.post("/")
def event_handler(event: dict[str, Any]):
    return handle(event)