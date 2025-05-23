FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
CMD ["uvicorn","service.trending_service.main:app","--host","0.0.0.0","--port","8000"]
