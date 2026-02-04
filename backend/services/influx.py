import os
from influxdb_client import InfluxDBClient

# --- CẤU HÌNH ---
INFLUX_URL = os.getenv("INFLUX_URL", "http://influxdb:8086")
INFLUX_TOKEN = os.getenv("INFLUXDB_INIT_ADMIN_TOKEN")
INFLUX_ORG = os.getenv("INFLUXDB_INIT_ORG", "HUS")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "api_metrics")

class InfluxService:
    def __init__(self):
        self.client = None
        self.query_api = None
        self._initialize_client()

    def _initialize_client(self):
        """Khởi tạo InfluxDB client an toàn"""
        try:
            if not INFLUX_TOKEN:
                print("⚠️ [Influx] INFLUXDB_INIT_ADMIN_TOKEN không được set.")
                return

            self.client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
            self.query_api = self.client.query_api()
            print(f"✅ [Influx] Đã kết nối thành công: {INFLUX_URL}")
        except Exception as e:
            print(f"⚠️ [Influx] Không thể kết nối InfluxDB: {e}")

    def get_recent_logs(self, limit=20):
        """
        Lấy danh sách log mới nhất (Có thêm trường bytes)
        Modified: Fetch larger pool (3x limit) -> Shuffle -> Return limit (Interleaved effect)
        """
        if not self.query_api: return []

        # Fetch 3x the limit to get a good pool for mixing
        pool_size = limit * 3
        
        query = f'''
        from(bucket: "{INFLUX_BUCKET}")
          |> range(start: -1h)
          |> filter(fn: (r) => r["_measurement"] == "api_requests")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> sort(columns: ["_time"], desc: true)
          |> limit(n: {pool_size})
        '''

        try:
            tables = self.query_api.query(query=query)
            logs = []
            for table in tables:
                for record in table.records:
                    host = record.values.get("host", "backend-api")
                    # Format timestamp to NASA style (Adjusted to Vietnam Time UTC+7)
                    # InfluxDB returns UTC. We add 7 hours manually.
                    dt = record.get_time()
                    from datetime import timedelta
                    dt_vn = dt + timedelta(hours=7)
                    formatted_time = dt_vn.strftime("[%d/%b/%Y:%H:%M:%S +0700]")
                    
                    method = record.values.get("method", "UNK")
                    endpoint = record.values.get("endpoint", "/unknown")
                    status = str(record.values.get("status", "200"))
                    bytes_val = record.values.get("bytes", 0)

                    logs.append({
                        "time": formatted_time, # Changed format
                        "method": method,
                        "endpoint": endpoint,
                        "status": status,
                        "latency": round(float(record.values.get("latency", 0)), 2),
                        "bytes": int(bytes_val), # Keep raw number or string? Let's keep number for now
                        "host": host,
                        "request_line": f'"{method} {endpoint} HTTP/1.0"', # Extra field for UI
                        "_dt": dt # Internal for sorting (Keep original UTC for sorting)
                    })
            
            # --- Randomize Logic ---
            import random
            if len(logs) > limit:
                # Shuffle the pool to mix GET/POST
                random.shuffle(logs)
                # Pick the first 'limit' items
                logs = logs[:limit]
            
            # Sort back by time (descending) so UI shows them in order
            logs.sort(key=lambda x: x["_dt"], reverse=True)
            
            # Remove internal sort key
            for log in logs:
                del log["_dt"]
                
            return logs
        except Exception as e:
            print(f"❌ [Influx] Lỗi Recent Logs: {e}")
            return []

    def get_realtime_metrics(self, time_range="-30s"):
        """
        Tính toán metrics thời gian thực (RPS, Latency) một cách chính xác.
        """
        if not self.query_api: return {"rps": 0, "latency": 0}

        try:
            # Cửa sổ thời gian là 30 giây (lấy từ time_range)
            time_window_seconds = int(time_range.strip("-s"))

            # --- Query 1: Đếm tổng số request để tính RPS ---
            # Use dot notation consistently and count the 'count' field (simplest)
            count_query = f'''
            from(bucket: "{INFLUX_BUCKET}")
              |> range(start: {time_range})
              |> filter(fn: (r) => r._measurement == "api_requests" and r._field == "count")
              |> group(columns: [])
              |> sum() 
            '''
            # Note: sum() on 'count' field (value=1) gives total requests. 
            
            count_tables = self.query_api.query(query=count_query)

            total_requests = 0
            if count_tables and count_tables[0].records:
                total_requests = count_tables[0].records[0].get_value() or 0

            # --- Query 2: Tính latency trung bình ---
            latency_query = f'''
            from(bucket: "{INFLUX_BUCKET}")
              |> range(start: {time_range})
              |> filter(fn: (r) => r._measurement == "api_requests" and r._field == "latency")
              |> group(columns: [])
              |> mean()
            '''
            latency_tables = self.query_api.query(query=latency_query)

            avg_latency = 0
            if latency_tables and latency_tables[0].records:
                avg_latency = latency_tables[0].records[0].get_value() or 0

            rps = total_requests / time_window_seconds if time_window_seconds > 0 else 0

            return {
                "rps": round(rps, 2),
                "latency": round(avg_latency, 2)
            }
        except Exception as e:
            print(f"❌ [Influx] Lỗi get_realtime_metrics: {e}")
            return {"rps": 0, "latency": 0}

    def get_chart_data(self, range_start="-1h", window_seconds=1):
        """
        Lấy dữ liệu vẽ biểu đồ: RPS, Latency, Error Rate, và Throughput.
        Sử dụng phương pháp union + pivot để gom dữ liệu, bền bỉ hơn join.
        Changed: window_seconds=1 to get per-second granularity
        """
        if not self.query_api:
            return []

        # NEW ROBUST QUERY
        query = f'''
            import "math"

            base_query = from(bucket: "{INFLUX_BUCKET}")
                |> range(start: {range_start})
                |> filter(fn: (r) => r._measurement == "api_requests")

            // 1. Calculate RPS (requests per second)
            rps = base_query
                |> filter(fn: (r) => r._field == "latency") // Filter any field that appears once per request
                |> group(columns: [])
                |> aggregateWindow(every: {window_seconds}s, fn: count, createEmpty: false)
                |> map(fn: (r) => ({{_time: r._time, _field: "rps", _value: float(v: r._value) / {window_seconds}.0}}))

            // 2. Calculate average latency
            latency = base_query
                |> filter(fn: (r) => r._field == "latency")
                |> group(columns: [])
                |> aggregateWindow(every: {window_seconds}s, fn: mean, createEmpty: false)
                |> map(fn: (r) => ({{r with _field: "latency"}}))


            // 3. Calculate error rate (%)
            requests_in_window = base_query
                |> filter(fn: (r) => r["_field"] == "count")
                |> group(columns: [])
                |> aggregateWindow(every: {window_seconds}s, fn: sum, createEmpty: false)

            errors_in_window = base_query
                |> filter(fn: (r) => r["_field"] == "count")
                |> filter(fn: (r) => r["status"] =~ /^[45]/)
                |> group(columns: [])
                |> aggregateWindow(every: {window_seconds}s, fn: sum, createEmpty: true)
                |> fill(value: 0)

            error_rate = join(tables: {{all: requests_in_window, errors: errors_in_window}}, on: ["_time"])
                |> map(fn: (r) => ({{
                    _time: r._time,
                    _field: "error_rate",
                    _value: if r._value_all > 0 then float(v: r._value_errors) / float(v: r._value_all) * 100.0 else 0.0
                }}))

            // 4. Calculate throughput (KB/s)
            throughput = base_query
                |> filter(fn: (r) => r._field == "bytes")
                |> group(columns: [])
                |> aggregateWindow(every: {window_seconds}s, fn: sum, createEmpty: false)
                |> map(fn: (r) => ({{_time: r._time, _field: "throughput", _value: float(v: r._value) / {window_seconds}.0 / 1024.0 }}))


            // Union all metrics and pivot
            union(tables: [rps, latency, error_rate, throughput])
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"])
        '''

        try:
            tables = self.query_api.query(query=query)
            chart_data = []
            for table in tables:
                for record in table.records:
                    # The keys will now be 'rps', 'latency', 'error_rate', 'throughput' after pivoting
                    chart_data.append({
                        "time": record.get_time().strftime("%H:%M:%S"),
                        "rps": round(record.values.get("rps", 0.0) or 0.0, 2),
                        "latency": round(record.values.get("latency", 0.0) or 0.0, 2),
                        "error_rate": round(record.values.get("error_rate", 0.0) or 0.0, 2),
                        "throughput": round(record.values.get("throughput", 0.0) or 0.0, 2),
                    })

            # Sort in Python just in case and slice
            chart_data.sort(key=lambda x: x['time'])
            return chart_data[-600:] # Return last 600 points (10 minutes with 1s interval)

        except Exception as e:
            print(f"❌ [Influx] Lỗi Chart Data: {e}")
            # To aid debugging, print the query that failed
            print(f"    Query gây lỗi:\n{query}")
            return []

influx_service = InfluxService()