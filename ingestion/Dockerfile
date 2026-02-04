FROM python:3.9-slim
WORKDIR /app

# Tắt buffer để log hiện ngay lập tức ra console
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python", "worker.py"]
