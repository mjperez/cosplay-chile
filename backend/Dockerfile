FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

EXPOSE 8000
# Migra, carga el seed solo si la base está vacía y levanta la API
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
