# Hệ Thống Autoscaling Thông Minh - DataFlow Season 2

## Tổng Quan Dự Án
Kho lưu trữ này chứa mã nguồn của **Hệ Thống Autoscaling Thông Minh (Intelligent Autoscaling System)**, một giải pháp toàn diện được thiết kế để tối ưu hóa việc phân bổ tài nguyên cho các kiến trúc microservices. Bằng cách tận dụng các thuật toán dự báo tiên tiến (LightGBM) kết hợp với phân tích chỉ số thời gian thực, hệ thống có khả năng chủ động mở rộng cơ sở hạ tầng để đáp ứng biến động nhu cầu, đồng thời đảm bảo tuân thủ các Cam kết Chất lượng Dịch vụ (SLOs).

Các tính năng chính bao gồm:
- **Mở rộng Chủ động (Proactive Scaling):** Dự đoán các đợt tăng đột biến traffic (traffic spikes) sử dụng dữ liệu lịch sử để cấp phát tài nguyên trước khi nhu cầu thực tế xảy ra.
- **Chiến lược Lai (Hybrid Strategy):** Kết hợp giữa mở rộng dựa trên dự báo và cơ chế phản ứng (reactive fallback) để đảm bảo hiệu năng ổn định trong mọi tình huống.
- **Mô phỏng Tại lượng (Traffic Simulation):** Tích hợp chế độ "Storm" để giả lập traffic cường độ cao (tương đương DDoS) thông qua Locust.
- **Giám sát Thời gian thực (Real-time Observability):** Dashboard quản trị full-stack được xây dựng trên nền tảng React, Recharts và InfluxDB.

## Yêu Cầu Tiên Quyết
Vui lòng đảm bảo các công cụ sau đã được cài đặt trên hệ thống trước khi tiếp tục:
- **Docker Desktop** (phiên bản 4.20 trở lên) có hỗ trợ Docker Compose.
- **Git** để quản lý phiên bản.
- **Cấu hình Phần cứng Tối thiểu:** 4GB RAM (Khuyến nghị 8GB để kiểm thử tải toàn diện).

## Hướng Dẫn Cài Đặt

1.  **Sao chép Mã nguồn (Clone Repository)**
    ```bash
    git clone <repository_url>
    cd Autoscaling-Analysis
    ```

2.  **Cấu hình Môi trường**
    Sao chép file môi trường mẫu để tạo cấu hình cục bộ:
    ```bash
    cp .env.example .env
    # (Tùy chọn) Chỉnh sửa .env nếu cần thay đổi cổng hoặc mật khẩu
    ```

3.  **Xây dựng và Khởi chạy**
    Thực thi lệnh sau để xây dựng và khởi động toàn bộ stack hệ thống:
    ```bash
    docker compose up -d --build
    ```
    *Lưu ý: Quá trình build lần đầu có thể mất vài phút để biên dịch tài nguyên frontend và cài đặt các thư viện backend.*

## Hướng Dẫn Vận Hành & Kiểm Thử

### 1. Truy cập Dashboard Quản Trị
Sau khi các containers đã hoạt động, truy cập Operations Dashboard thông qua trình duyệt:
*   **URL:** `http://localhost:5173`
*   **Xác thực:** Không yêu cầu trong phiên bản demo này.

### 2. Giám Sát Chỉ Số (Metrics)
Dashboard hiển thị các chỉ số thời gian thực bao gồm:
*   **RPS (Requests Per Second):** Tải traffic hiện tại.
*   **Active Pods:** Số lượng bản sao (replicas) backend đang hoạt động.
*   **Latency:** Thời gian phản hồi trung bình.

### 3. Kích Hoạt Tải Đột Biến (Traffic Storm Test)
Để kiểm chứng logic autoscaling dưới điều kiện tải cực đoan:
1.  Điều hướng đến **Admin Panel** (Thanh bên phải).
2.  Nhấn vào **Biểu tượng Tia Sét (⚡)** trên thanh điều hướng phía trên.
3.  Quan sát biểu đồ **RPS** tăng vọt (>1000 RPS).
4.  Theo dõi số lượng **Active Pods** tăng lên khi autoscaler phản ứng.

### 4. Tài liệu API & Kiểm tra Hệ thống
*   **Tài liệu Backend API:** `http://localhost:8000/docs`
*   **Trạng thái Hệ thống (Health Check):** `http://localhost:8000/health`

## Cấu Trúc Dự Án
Mã nguồn được tổ chức như sau:
*   `backend/`: Logic cốt lõi, dịch vụ Autoscaler và Mock API.
*   `frontend/`: Ứng dụng dashboard sử dụng React + TypeScript.
*   `ingestion/`: Worker hiệu năng cao để chuyển logs từ Redis sang InfluxDB.
*   `locust/`: Kịch bản kiểm thử tải và logic mô phỏng.
*   `ml_model/`: Notebooks nghiên cứu và định nghĩa các mô hình AI.

## Ghi Chú Về Tính Tái Lập (Reproducibility)
*   **Không Hard-Coding:** Tất cả đường dẫn đều là tương đối hoặc được kiểm soát qua biến môi trường.
*   **Docker hóa:** Toàn bộ hệ thống vận hành trong các containers cô lập.
*   **Kiểm soát Random Seed:** Các hạt giống ngẫu nhiên (random seeds) được cố định trong các kịch bản mô phỏng để đảm bảo kết quả nhất quán.

---
**Bài Dự Thi DataFlow Mùa 2**
*Phát triển bởi Đội thi TuanThichCode100*
