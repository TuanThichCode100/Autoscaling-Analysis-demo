import math
import subprocess
import logging
import time

# Cấu hình Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Autoscaler")

# --- THAM SỐ CẤU HÌNH (Dựa trên PDF) ---
CAPACITY_PER_POD = 50       # C: Capacity hiệu dụng (RPS/pod)
MIN_REPLICAS = 1
MAX_REPLICAS = 10
BUFFER_K = 0.1             # k: Hệ số buffer (10%)
ANOMALY_THRESHOLD = 0.15    # epsilon: Ngưỡng sai số dự báo (15%) để fallback về Reactive
SCALE_DOWN_COOLDOWN = 60    # Cooldown khi scale down (giây) - Tránh flapping

# --- STATE MANAGEMENT (Toàn cục) ---
autoscaler_state = {
    "last_scale_down_time": 0,
    "last_scale_up_time": 0
}

def get_current_replicas(service_name="api"):
    """
    Đếm số container đang chạy của service 'api'
    """
    try:
        import shutil
        if not shutil.which("docker"):
            logger.warning("⚠️ Docker CLI không có sẵn, trả về giá trị mặc định")
            return 1
            
        cmd = "docker ps --format '{{.Names}}' | grep 'autoscaler-mock-api' | wc -l"
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=5)
        count = int(result.strip())
        return max(1, count)
    except Exception as e:
        logger.warning(f"⚠️ Lỗi đếm replica: {e}, trả về 1")
        return 1

def scale_service(service_name, replicas):
    """
    Gọi Docker Compose để scale
    """
    try:
        import shutil
        if not shutil.which("docker"):
            logger.warning("⚠️ Docker CLI không có sẵn, không thể scale")
            return False
            
        replicas = max(MIN_REPLICAS, min(replicas, MAX_REPLICAS))
        
        logger.info(f"⚖️ EXECUTE: Scaling {service_name} lên {replicas} replicas...")
        
        # --scale api=... --no-recreate để giữ các container cũ nếu không đổi config
        subprocess.run([
            "docker", "compose", "up", "-d", "--scale", f"api={replicas}", "--no-recreate"
        ], check=True, timeout=30, stderr=subprocess.PIPE)
        
        return True
    except Exception as e:
        logger.error(f"❌ Lỗi khi scale: {e}")
        return False

# --- LOGIC MỚI THEO PDF ---

def predict_next_rps(current_rps):
    """
    Giả lập module Forecast (Prophet/LSTM).
    Hiện tại dùng Naive Forecast: Dự báo = Hiện tại +/- nhiễu nhẹ
    Thực tế: Hàm này sẽ gọi ra service AI hoặc load model .pkl
    """
    # TODO: Tích hợp model ML thật ở đây
    # Giả sử dự báo tăng nhẹ xu hướng (reactive simulation)
    return current_rps * 1.0 

def calculate_proactive_replicas(forecast_rps):
    """
    Công thức 2.1 & 2.2 trong PDF:
    replicas = ceil( (Forecast / C) * (1 + k) )
    """
    if forecast_rps <= 0: return MIN_REPLICAS
    
    raw_needed = forecast_rps / CAPACITY_PER_POD
    with_buffer = raw_needed * (1 + BUFFER_K)
    return math.ceil(with_buffer)

def calculate_reactive_replicas(current_rps):
    """
    Công thức 2.3 trong PDF (Fallback HPA):
    replicas = ceil( Current / Capacity )
    """
    if current_rps <= 0: return MIN_REPLICAS
    return math.ceil(current_rps / CAPACITY_PER_POD)

def check_anomaly(current_rps, forecast_rps):
    """
    Công thức 2.4.3: Kiểm tra độ tin cậy của forecast
    |y_t - y_hat| / y_t > epsilon
    """
    if current_rps == 0: return False # Tránh chia cho 0
    
    deviation = abs(current_rps - forecast_rps) / current_rps
    return deviation > ANOMALY_THRESHOLD

def run_autoscaling_cycle(current_rps):
    """
    Hàm chính điều phối Autoscaling Cycle
    """
    global autoscaler_state
    
    current_time = time.time()
    current_replicas = get_current_replicas()
    
    # 1. Dự báo (Forecast)
    forecast_rps = predict_next_rps(current_rps)
    
    # 2. Kiểm tra Anomaly để chọn chiến thuật
    is_anomaly = check_anomaly(current_rps, forecast_rps)
    
    if is_anomaly:
        # Fallback về Reactive HPA
        mode = "REACTIVE (Fallback)"
        desired_replicas = calculate_reactive_replicas(current_rps)
        logger.warning(f"⚠️ Phát hiện bất thường (Dev={abs(current_rps - forecast_rps)/current_rps:.2f}), chuyển sang mode Reactive")
    else:
        # Sử dụng Proactive (theo giấy)
        mode = "PROACTIVE"
        desired_replicas = calculate_proactive_replicas(forecast_rps)
    
    # Kẹp trong giới hạn Min/Max
    desired_replicas = max(MIN_REPLICAS, min(desired_replicas, MAX_REPLICAS))
    
    # 3. Logic Hysteresis / Cooldown (Mục 1.1 PDF)
    
    # Case A: Scale Up (Phản ứng nhanh)
    if desired_replicas > current_replicas:
        logger.info(f"📊 {mode}: RPS={current_rps} (Forecast={forecast_rps}) | Cần tăng {current_replicas} -> {desired_replicas}")
        scale_service("api", desired_replicas)
        autoscaler_state["last_scale_up_time"] = current_time
        return desired_replicas
        
    # Case B: Scale Down (Phản ứng chậm - Cooldown)
    elif desired_replicas < current_replicas:
        time_since_down = current_time - autoscaler_state["last_scale_down_time"]
        
        if time_since_down < SCALE_DOWN_COOLDOWN:
            logger.info(f"⏳ Đang Cooldown (còn {int(SCALE_DOWN_COOLDOWN - time_since_down)}s), giữ {current_replicas} replicas (Mục tiêu: {desired_replicas})")
            return current_replicas
        else:
            logger.info(f"📉 {mode}: RPS giảm, cooldown đã xong. Giảm {current_replicas} -> {desired_replicas}")
            scale_service("api", desired_replicas)
            autoscaler_state["last_scale_down_time"] = current_time
            return desired_replicas
            
    # Case C: Giữ nguyên
    else:
        # logger.info(f"✅ Ổn định. RPS={current_rps} | Replicas={current_replicas}")
        pass
        
    return current_replicas