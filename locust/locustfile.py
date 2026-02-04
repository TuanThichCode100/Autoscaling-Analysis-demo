import math
import random
from locust import HttpUser, task, between, LoadTestShape

class WebsiteUser(HttpUser):
    # --- 🔥 THÊM CẤU HÌNH HOST Ở ĐÂY ---
    # Địa chỉ này trỏ đến container Mock API trong mạng Docker.
    # Lưu ý: "api" là tên service trong docker-compose.yml. 
    # Nếu service của bạn tên là "mock_api" hay "autoscaler-api" thì sửa lại cho khớp.
    host = "http://api:8000" 

    # Thời gian nghỉ thấp để tạo áp lực lớn (High RPS)
    wait_time = between(0.5, 1.5)

    # --- NHÓM 1: BÌNH THƯỜNG (XANH LÁ) ---
    @task(15)
    def view_homepage(self):
        self.client.get("/shuttle/countdown/", name="View Homepage")

    @task(10)
    def read_mission(self):
        self.client.get("/shuttle/missions/sts-71/mission-sts-71.html", name="Read Mission")

    # --- NHÓM 2: TẢI NẶNG (CAM - THROUGHPUT CAO) ---
    @task(5)
    def download_heavy_image(self):
        # Gọi file 5MB -> Throughput sẽ nhảy vọt
        self.client.get("/images/NASA-logosmall.gif", name="Download 5MB Image")

    @task(5)
    def download_medium_image(self):
        # Gọi file 1.5MB
        self.client.get("/images/KSC-logosmall.gif", name="Download 1.5MB Image")

    # --- NHÓM 3: WRITE DATA (TÍM) ---
    @task(3)
    def upload_observation(self):
        self.client.post("/api/upload", json={"content": "x"*500}, name="Upload Data")

    # --- NHÓM 4: LỖI CHỦ ĐÍCH (ĐỎ / VÀNG) ---
    @task(1)
    def broken_link(self):
        # Tạo lỗi 404 (Not Found)
        with self.client.get("/error/404", catch_response=True, name="Broken Link (404)") as response:
            if response.status_code == 404:
                response.failure("Resource Missing") 
                
    @task(1)
    def unauthorized_access(self):
        # Tạo lỗi 401 (Unauthorized)
        with self.client.get("/error/401", catch_response=True, name="Auth Fail (401)") as response:
            if response.status_code == 401:
                response.failure("Login Required")

    @task(1)
    def server_crash(self):
        # Tạo lỗi 500 (Internal Error)
        with self.client.get("/error/500", catch_response=True, name="Server Crash (500)") as response:
             if response.status_code == 500:
                response.failure("Internal Error")

# --- KỊCH BẢN NGÀY ĐÊM (TẠM TẮT ĐỂ TEST SPIKE QUA API) ---
# class DayNightCycle(LoadTestShape):
#     day_duration = 120 
#     spawn_rate = 50   
#     min_users = 50     
#     peak_users = 400   
#
#     def tick(self):
#         run_time = self.get_run_time()
#         
#         # Bắt đầu test tại thời điểm 6:00 sáng (Tăng tốc ngay)
#         virtual_time = run_time + 30 
#         
#         day_progress = (virtual_time % self.day_duration) / self.day_duration
#         hour = day_progress * 24
#         
#         target = self.min_users
#         
#         if 6 <= hour < 9: # SÁNG
#             ratio = (hour - 6) / 3
#             target = self.min_users + (self.peak_users - self.min_users) * ratio
#         elif 9 <= hour < 18: # TRƯA (Dao động)
#             target = self.peak_users + random.randint(-30, 30)
#         elif 18 <= hour <= 24: # TỐI
#             ratio = (hour - 18) / 6
#             target = self.peak_users - (self.peak_users - self.min_users) * ratio
#         else: # ĐÊM
#             target = self.min_users + random.randint(0, 10)
#
#         return (round(target), self.spawn_rate)