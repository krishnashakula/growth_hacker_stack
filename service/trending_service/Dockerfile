FROM python:3.11-slim
WORKDIR /app

# 1. base deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2.  tweak pip cache for torch wheel only (optional)
# RUN pip install --no-cache-dir torch==2.2.2+cpu -f https://download.pytorch.org/whl/torch_stable.html

COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
