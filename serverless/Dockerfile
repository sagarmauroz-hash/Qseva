FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY serverless/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY serverless/function.py ./function.py

EXPOSE 8080

RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/').read()" || exit 1

CMD ["uvicorn", "function:app", "--host", "0.0.0.0", "--port", "8080"]
