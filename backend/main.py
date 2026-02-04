import asyncio
import logging
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import service kết nối InfluxDB & Locust
from services.autoscaler import run_autoscaling_cycle, get_current_replicas
from services.influx import influx_service
from services.locust_service import locust_service

# Cấu hình Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BackendAPI")

app = FastAPI()

# --- CẤU HÌNH CORS (Để Frontend gọi được) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- TRẠNG THÁI HỆ THỐNG (Lưu tạm trong RAM) ---
system_state = {
    "current_rps": 0,
    "current_latency": 0,
    "replicas": 1,
    "status": "Healthy"
}

# --- BACKGROUND TASK: AUTOSCALING LOOP ---
@app.on_event("startup")
async def start_autoscaler_loop():
    """Vòng lặp chạy ngầm: 10s một lần"""
    asyncio.create_task(autoscaler_worker())

async def autoscaler_worker():
    logger.info("🚀 Autoscaler Background Worker đã khởi động!")
    while True:
        try:
            # Kiểm tra xem InfluxDB đã sẵn sàng chưa
            if influx_service.client is None:
                logger.warning("⚠️ InfluxDB chưa sẵn sàng, bỏ qua cycle này...")
                await asyncio.sleep(10)
                continue

            # 🔥 FIX: Chạy tác vụ blocking trong thread riêng để không đóng băng server
            # 1. Lấy metrics thật từ InfluxDB (30s gần nhất)
            metrics = await asyncio.to_thread(influx_service.get_realtime_metrics, time_range="-30s")
            rps = metrics.get("rps", 0)
            latency = metrics.get("latency", 0)

            # 2. Cập nhật state toàn cục
            system_state["current_rps"] = rps
            system_state["current_latency"] = latency

            # 3. Chạy logic Autoscaling (hàm này cũng blocking vì gọi subprocess)
            new_replicas = await asyncio.to_thread(run_autoscaling_cycle, rps)
            system_state["replicas"] = new_replicas

        except Exception as e:
            logger.error(f"⚠️ Lỗi trong vòng lặp Autoscaler: {e}")
            import traceback
            logger.error(traceback.format_exc())

        await asyncio.sleep(10)

# --- CÁC API ENDPOINT (CỬA NGÕ) ---

@app.get("/")
def root():
    """Root endpoint"""
    return {"status": "Backend is running"}

@app.get("/health")
def health_check():
    """Health check endpoint for Docker and monitoring"""
    return {
        "status": "healthy",
        "service": "autoscaler-backend"
    }

@app.get("/api/status")
async def get_system_status():
    """
    API 1: Trả về trạng thái hiện tại (RPS, Replicas, Latency)
    Dùng cho: Các thẻ số liệu (Cards) bên phải màn hình
    """
    try:
        # Lấy số replica thực tế từ Docker
        real_replicas = await asyncio.to_thread(get_current_replicas)
        system_state["replicas"] = real_replicas
    except Exception as e:
        logger.warning(f"⚠️ Không thể lấy replica count: {e}")
        # Giữ nguyên giá trị hiện tại nếu lỗi

    return system_state

@app.get("/api/logs")
async def get_access_logs():
    """
    API 2: Trả về danh sách Log mới nhất
    Dùng cho: Cột 'Access Logs' bên trái màn hình
    """
    try:
        # 🔥 FIX: Chạy tác vụ blocking trong thread riêng
        return await asyncio.to_thread(influx_service.get_recent_logs, limit=50)
    except Exception as e:
        logger.error(f"⚠️ Lỗi lấy logs: {e}")
        return []

@app.get("/api/metrics/history")
async def get_historical_data():
    """
    API 3: Trả về dữ liệu lịch sử để vẽ biểu đồ
    Dùng cho: Biểu đồ đường (Line Chart)
    """
    try:
        # 🔥 FIX: Chạy tác vụ blocking trong thread riêng
        return await asyncio.to_thread(influx_service.get_chart_data, range_start="-30m")
    except Exception as e:
        logger.error(f"⚠️ Lỗi lấy metrics history: {e}")
        return []

# --- API CONTROL: STORM TRIGGER ---
class StormRequest(BaseModel):
    enabled: bool

@app.post("/api/control/storm")
async def toggle_storm(request: StormRequest):
    """
    Kích hoạt hoặc dừng Traffic Storm (Gọi Locust)
    """
    if request.enabled:
        logger.warning("⚡ USER TRIGGERED STORM! SCALING LOCUST UP...")
        # 2000 users, 200 spawn rate -> Spike cực gắt
        success = await asyncio.to_thread(locust_service.start_storm, 2000, 200)
        return {"status": "storm_started", "success": success}
    else:
        logger.info("cloudy 🌥️ USER STOPPED STORM. RESETTING LOCUST...")
        # Về 50 users, 5 spawn rate -> Normal load
        success = await asyncio.to_thread(locust_service.stop_storm, 50, 5)
        return {"status": "storm_stopped", "success": success}