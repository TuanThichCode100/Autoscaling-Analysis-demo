FROM python:3.9-slim

WORKDIR /mnt/locust
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Mở port 8089 cho giao diện web của Locust
EXPOSE 8089

# Lệnh chạy mặc định
CMD ["locust", "-f", "locustfile.py"]