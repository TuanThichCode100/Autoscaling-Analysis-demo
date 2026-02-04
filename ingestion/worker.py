import os
import time
import redis
import json
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import WriteOptions

# --- CẤU HÌNH ---
REDIS_HOST = os.getenv('REDIS_HOST', 'redis_service') 
INFLUX_HOST = os.getenv('INFLUX_HOST', 'influxdb')
INFLUX_URL = f"http://{INFLUX_HOST}:8086"
INFLUX_TOKEN = os.getenv('INFLUXDB_INIT_ADMIN_TOKEN') 
INFLUX_ORG = os.getenv('INFLUXDB_INIT_ORG', 'HUS')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET', 'api_metrics')

print(f"🚀 Ingestor Worker đang khởi động...")
print(f"--- Influx Target: {INFLUX_URL}")

# --- 1. CLASS CALLBACK ĐỂ BẮT LỖI GHI ---
class BatchingCallback(object):
    def success(self, conf: (str, str, str), data: str):
        pass 

    def error(self, conf: (str, str, str), data: str, exception: Exception):
        print(f"❌ INFLUX WRITE ERROR: {exception}")

    def retry(self, conf: (str, str, str), data: str, exception: Exception):
        print(f"⚠️ Retrying due to: {exception}")

# --- 2. KẾT NỐI ---
try:
    pool = redis.ConnectionPool(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    r.ping()
    print("✅ Redis Connected!")
except Exception as e:
    print(f"❌ Redis Error: {e}")
    exit(1)

try:
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    
    # Đăng ký Callback bắt lỗi
    callback = BatchingCallback()
    
    write_api = client.write_api(write_options=WriteOptions(
        batch_size=100,      # Giảm batch để ghi nhanh hơn (Low latency)
        flush_interval=100,  # Flush mỗi 100ms (Gần như realtime)
        jitter_interval=0,
        retry_interval=5000
    ), success_callback=callback.success, error_callback=callback.error, retry_callback=callback.retry)
    
    print("✅ InfluxDB Connected!")
except Exception as e:
    print(f"❌ InfluxDB Client Error: {e}")
    exit(1)

# --- 3. VÒNG LẶP ---
last_id = '0' # Đọc từ đầu

print("🎧 Worker bắt đầu vét sạch Redis...")

while True:
    try:
        # Tăng count lên 500 để kịp hớp hết nước lũ khi Spike
        response = r.xread({"api_stream": last_id}, count=500, block=2000)
        
        if response:
            stream_key, messages = response[0]
            processed_count = 0
            
            for message_id, data in messages:
                try:
                    # Parse dữ liệu
                    latency = float(data.get('latency', 0))
                    status = str(data.get('status', '200'))
                    
                    # 🔥 [ĐÃ SỬA]: Ép về int để khớp với schema Integer của InfluxDB
                    # Dùng int(float(...)) để an toàn nếu dữ liệu gốc lỡ là string "123.0"
                    try:
                        bytes_val = int(float(data.get('bytes', 0)))
                    except ValueError:
                        bytes_val = 0
                    
                    # Lấy timestamp gốc
                    ts_raw = data.get('timestamp')
                    if ts_raw:
                        record_time = datetime.fromtimestamp(float(ts_raw))
                    else:
                        record_time = datetime.utcnow()

                    request_str = data.get('request', '')
                    if len(request_str.split()) >= 2:
                        method = request_str.split()[0]
                        endpoint = request_str.split()[1]
                    else:
                        method = 'UNKNOWN'
                        endpoint = 'unknown_path'

                    host = data.get('host', 'unknown_host')

                    point = Point("api_requests") \
                        .tag("endpoint", endpoint) \
                        .tag("method", method) \
                        .tag("status", status) \
                        .tag("host", host) \
                        .field("latency", latency) \
                        .field("count", 1) \
                        .field("bytes", bytes_val) \
                        .time(record_time) 
                    
                    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
                    processed_count += 1
                    
                except Exception as parse_err:
                    print(f"⚠️ Parse Error: {parse_err}")

                last_id = message_id
            
            print(f"⚡ Đã nạp {processed_count} logs (Last ID: {last_id})") 
                
    except Exception as e:
        print(f"❌ Runtime Error: {e}")
        time.sleep(1)