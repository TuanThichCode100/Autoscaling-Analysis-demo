import asyncio
import time
import random
import redis
import os
from fastapi import FastAPI, Request, BackgroundTasks, Response
from fastapi.responses import PlainTextResponse

app = FastAPI()

# --- CẤU HÌNH REDIS ---
REDIS_HOST = os.getenv('REDIS_HOST', 'redis_service')
try:
    pool = redis.ConnectionPool(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
    r = redis.Redis(connection_pool=pool)
except Exception as e:
    print(f"❌ Redis Connection Error: {e}")

# --- CẤU HÌNH SỨC CHỊU ĐỰNG ---
SOFT_LIMIT = int(os.getenv("SOFT_LIMIT", 50)) 
HARD_LIMIT = int(os.getenv("HARD_LIMIT", 5000)) # Tăng từ 1000 lên 5000 để chịu Spike
CURRENT_LOAD = 0 

FAKE_HOSTS = ["199.72.81.55", "unicomp6.unicomp.net", "d104.esrin.esa.it", "gw1.nasa.gov"]

# --- METADATA NÂNG CẤP (FILE TO HƠN, THÊM ĐƯỜNG DẪN LỖI) ---
ENDPOINTS_METADATA = {
    # 1. FILE NẶNG (Test Băng thông - Throughput)
    # Ảnh siêu nặng 1MB (Giảm từ 5MB)
    "/images/NASA-logosmall.gif": {"type": "image", "size": 1_000_000}, 
    # Ảnh vừa 300KB
    "/images/KSC-logosmall.gif":  {"type": "image", "size": 300_000},
    # Ảnh nhẹ 100KB
    "/history/apollo/images/apollo-logo1.gif": {"type": "image", "size": 100_000},
    
    # 2. FILE NHẸ (Test RPS)
    "/shuttle/missions/sts-71/mission-sts-71.html": {"type": "html", "size": 15000},
    "/shuttle/countdown/": {"type": "html", "size": 10000},
    "/htbin/cdt_main.pl":  {"type": "cgi", "size": 5000}, 
    "/cgi-bin/geturlstats.pl": {"type": "cgi", "size": 2000},

    # 3. ĐƯỜNG DẪN GÂY LỖI (Test Error Rate đa dạng)
    "/error/404": {"type": "error", "status": 404, "size": 0},
    "/error/401": {"type": "error", "status": 401, "size": 0},
    "/error/500": {"type": "error", "status": 500, "size": 0},
}

async def simulate_realistic_latency(request_type: str):
    global CURRENT_LOAD
    
    # --- CHẾ ĐỘ HIỆU NĂNG CAO (HIGH PERFORMANCE MOCK) ---
    # Để đạt RPS cao (Spike Test), ta cần API phản hồi cực nhanh.
    # Không dùng logic "càng tải càng chậm" nữa, vì nó sẽ làm nghẽn cổ chai ở Client (Locust).
    
    base = 0.01 # 10ms mặc định siêu nhanh
    
    if request_type == "image": 
        base = 0.05  # Ảnh thì chậm hơn chút xíu (50ms)
    elif request_type == "error":
        base = 0.005 # Lỗi thì trả về ngay lập tức (5ms)
    
    # Chỉ thêm jitter cực nhỏ để không biểu đồ không bị thẳng đuột
    jitter = random.uniform(0, 0.01)
    
    return base + jitter

@app.api_route("/{path_name:path}", methods=["GET", "POST", "HEAD", "DELETE", "PUT"])
async def catch_all(request: Request, path_name: str, background_tasks: BackgroundTasks):
    global CURRENT_LOAD
    path = "/" + path_name
    
    # --- 1. HARD LIMIT (Lỗi 503 Overload) ---
    if CURRENT_LOAD >= HARD_LIMIT:
        error_log = {
            "host": "server-overloaded",
            "request": f"{request.method} {path} HTTP/1.0",
            "status": "503",
            "bytes": "0",
            "timestamp": str(time.time()),
            "latency": "0",
            "active_requests": str(CURRENT_LOAD)
        }
        background_tasks.add_task(r.xadd, "api_stream", error_log, maxlen=100000)
        return Response("Server Overloaded", status_code=503)

    CURRENT_LOAD += 1
    try:
        # Lấy metadata, mặc định là html nhỏ
        metadata = ENDPOINTS_METADATA.get(path, {"type": "html", "size": 2000})
        
        # Xử lý độ trễ
        latency = await simulate_realistic_latency(metadata['type'])
        await asyncio.sleep(latency)
        
        # --- XÁC ĐỊNH STATUS CODE ---
        # 1. Lỗi định sẵn (nếu gọi vào endpoint /error/...)
        if "status" in metadata:
            status_code = metadata["status"]
            content_size = 0
        # 2. Lỗi ngẫu nhiên (Random Chaos - 1%)
        elif random.random() < 0.01:
            status_code = 500
            content_size = 0
        # 3. Thành công
        else:
            status_code = 200
            content_size = metadata['size'] + random.randint(-100, 100)

        # --- GHI LOG VÀO REDIS ---
        # Ghi 100% Request (Bỏ Sampling) để hiển thị đúng RPS thực tế
        if True: 
            log_data = {
                "host": random.choice(FAKE_HOSTS),
                "request": f"{request.method} {path} HTTP/1.0",
                "status": str(status_code),
                "bytes": str(content_size),
                "timestamp": str(time.time()),
                "latency": str(round(latency * 1000, 2)),
                "active_requests": str(CURRENT_LOAD)
            }
            background_tasks.add_task(r.xadd, "api_stream", log_data, maxlen=100000)

        # Trả về Response
        if status_code != 200:
            return Response(status_code=status_code)
            
        if metadata['type'] == 'image':
             # Trả về dummy bytes để tạo traffic mạng thật (giúp docker stats hiển thị đúng)
             # Chỉ trả về 1 phần nhỏ nếu file quá lớn để tránh nghẽn Python, 
             # hoặc trả full nếu muốn test mạng thật. Ở đây trả full.
             return Response(content=b'x' * content_size, media_type="image/gif")
        
        return PlainTextResponse("NASA Mock Response", status_code=status_code)

    finally:
        CURRENT_LOAD -= 1