FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    API_HOST=0.0.0.0

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Railway прокидывает порт через $PORT. Читаем его, если задан.
CMD ["sh", "-c", "API_PORT=${PORT:-${API_PORT:-8080}} python -m app.main"]
