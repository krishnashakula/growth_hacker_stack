FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN python -m pip install --upgrade pip &&        pip install --no-cache-dir fastapi praw schedule requests psycopg2-binary uvicorn python-json-logger prometheus-client
CMD ["uvicorn","service.trending_service.main:app","--host","0.0.0.0","--port","8000"]
