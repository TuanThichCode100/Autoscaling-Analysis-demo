#!/usr/bin/env python3
"""
Apache Log Parser to Parquet Format

Chuyển đổi định dạng Apache HTTP Server Common Log Format sang Parquet với các kiểu dữ liệu chính xác:
- host: string (IP hoặc hostname)
- timestamp: datetime64[us, UTC] (đã chuẩn hóa về UTC)
- request: string (HTTP request line)
- status: int32 (HTTP status code)
- bytes: int64 (kích thước response)

Quá trình xử lý:
1. Đọc từng dòng từ file log
2. Parse log line bằng regex
3. Chuyển đổi timestamp sang UTC
4. Lưu vào batch (mặc định 10,000 records)
5. Ghi batch vào Parquet (append mode)
6. Hiển thị thống kê cuối cùng
"""

import re
import pandas as pd
from datetime import datetime
import pytz
import sys
from pathlib import Path

# ============================================================================
# REGEX PATTERN - Mẫu regex để parse Apache Common Log Format
# ============================================================================
# Format: host - - [timestamp] "request" status bytes
# Ví dụ: 199.72.81.55 - - [01/Jul/1995:00:00:01 -0400] "GET /path HTTP/1.0" 200 6245
# 
# Giải thích regex:
# ^([^\s]+)         → host: không chứa khoảng trắng
# \s+\-\s+\-\s+     → " - - " (literal)
# \[(.+?)\]         → [timestamp] (non-greedy capture)
# \s+"(.+?)"\s+     → "request" (non-greedy capture)
# (\d+)             → status: 1 hoặc nhiều chữ số
# \s+(\d+|-)$       → bytes: số hoặc dấu "-"
LOG_PATTERN = re.compile(
    r'^([^\s]+)\s+\-\s+\-\s+\[(.+?)\]\s+"(.+?)"\s+(\d+)\s+(\d+|-)$'
)

# Định dạng timestamp: 01/Jul/1995:00:00:01 -0400
# %d = day (01-31), %b = month (Jan-Dec), %Y = year (1995)
# %H:%M:%S = time, %z = timezone offset (-0400)
TIMESTAMP_FORMAT = "%d/%b/%Y:%H:%M:%S %z"

# ============================================================================
# HÀM PARSE LOG LINE
# ============================================================================
def parse_log_line(line):
    """
    Parse một dòng log Apache sang dictionary
    
    Args:
        line (str): Một dòng từ file log
        
    Returns:
        dict: Dictionary chứa {host, timestamp, request, status, bytes}
        None: Nếu parse thất bại
        
    Quá trình:
    1. Strip khoảng trắng và match với regex
    2. Parse timestamp và convert sang UTC
    3. Parse bytes (xử lý trường hợp "-")
    4. Trả về dictionary hoặc None
    """
    match = LOG_PATTERN.match(line.strip())
    if not match:
        return None
    
    try:
        # Lấy 5 group từ regex match
        host, timestamp_str, request, status, bytes_str = match.groups()
        
        # ========== TIMESTAMP CONVERSION ==========
        # Parse timestamp với timezone offset
        dt = datetime.strptime(timestamp_str, TIMESTAMP_FORMAT)
        # datetime.strptime với %z tự động tạo timezone-aware object
        # Ví dụ: "01/Jul/1995:00:00:01 -0400" → datetime(1995, 7, 1, 0, 0, 1, tzinfo=UTC-4)
        
        # Convert sang UTC timezone
        # Ví dụ: UTC-4 lúc 12:00 → UTC lúc 16:00
        utc_dt = dt.astimezone(pytz.UTC)
        
        # ========== BYTES CONVERSION ==========
        # Nếu bytes là "-" (no data sent), chuyển thành -1 (marker value)
        # Nếu không, convert sang integer
        bytes_val = int(bytes_str) if bytes_str != '-' else -1
        
        return {
            'host': host,              # string
            'timestamp': utc_dt,       # datetime (sẽ convert sang datetime64[us, UTC] khi làm DataFrame)
            'request': request,        # string
            'status': int(status),     # int
            'bytes': bytes_val         # int
        }
    except Exception as e:
        # Log lỗi ra stderr (không ảnh hưởng output chính)
        print(f"Error parsing line: {line}", file=sys.stderr)
        print(f"Exception: {e}", file=sys.stderr)
        return None

# ============================================================================
# HÀM PARSE FILE LỚN
# ============================================================================
def parse_log_file(input_path, output_path, batch_size=10000):
    """
    Parse file log lớn và ghi vào Parquet (xử lý batch để tiết kiệm memory)
    
    Args:
        input_path (str): Đường dẫn file log input (ví dụ: "train.txt")
        output_path (str): Đường dẫn file Parquet output (ví dụ: "output.parquet")
        batch_size (int): Số records xử lý 1 lần (mặc định 10,000)
                         - Cao hơn → nhanh hơn nhưng dùng RAM nhiều
                         - Thấp hơn → RAM ít nhưng chậm hơn
        
    Quá trình:
    1. Mở file log, đọc từng dòng
    2. Parse mỗi dòng bằng parse_log_line()
    3. Collect records vào batch
    4. Khi batch đủ batch_size:
       - Convert sang DataFrame
       - Set kiểu dữ liệu (int32, int64)
       - Ghi vào Parquet (append mode)
       - Clear batch
    5. Ghi remaining records ở cuối
    6. Hiển thị thống kê
    """
    records = []
    error_count = 0
    record_count = 0
    
    # ========== HEADER ==========
    print(f"=== Apache Log to Parquet Converter ===")
    print(f"Input file: {input_path}")
    print(f"Output file: {output_path}")
    print(f"Batch size: {batch_size:,} records")
    print()
    
    # ========== MAIN PROCESSING ==========
    # Mở file với UTF-8 encoding, bỏ qua lỗi encoding
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            # Parse dòng hiện tại
            parsed = parse_log_line(line)
            
            if parsed:
                # Parse thành công, thêm vào records
                records.append(parsed)
                record_count += 1
                
                # Hiển thị progress mỗi batch_size records
                if record_count % batch_size == 0:
                    print(f"Processed: {record_count:,} records")
                
                # ========== WRITE BATCH TO PARQUET ==========
                # Khi records đủ batch_size, ghi vào Parquet
                if len(records) >= batch_size:
                    # Tạo DataFrame từ records
                    df = pd.DataFrame(records)
                    
                    # Set kiểu dữ liệu chính xác
                    df['status'] = df['status'].astype('int32')  # HTTP status code
                    # Chuyển bytes thành int64 (các giá trị "-" đã được convert thành -1)
                    df['bytes'] = df['bytes'].astype('int64')    # File size
                    
                    if record_count == batch_size:
                        # Batch đầu tiên: tạo file Parquet mới
                        df.to_parquet(output_path, index=False, engine='pyarrow')
                    else:
                        # Batch tiếp theo: append vào file Parquet cũ
                        # Cách làm:
                        # 1. Đọc file Parquet cũ
                        # 2. Ghép thêm batch mới
                        # 3. Ghi lại file Parquet
                        existing_df = pd.read_parquet(output_path)
                        combined_df = pd.concat([existing_df, df], ignore_index=True)
                        combined_df.to_parquet(output_path, index=False, engine='pyarrow')
                    
                    # Clear records để lấy batch tiếp theo
                    records = []
            else:
                # Parse thất bại, tăng error counter
                error_count += 1
    
    # ========== WRITE REMAINING RECORDS ==========
    # Xử lý những records cuối cùng (có thể < batch_size)
    if records:
        df = pd.DataFrame(records)
        # Chuyển bytes thành int64 (các giá trị "-" đã được convert thành -1)
        df['status'] = df['status'].astype('int32')
        df['bytes'] = df['bytes'].astype('int64')
        
        if record_count == len(records):
            # Chỉ có 1 batch (toàn bộ file < batch_size)
            df.to_parquet(output_path, index=False, engine='pyarrow')
        else:
            # Append batch cuối cùng vào file Parquet cũ
            existing_df = pd.read_parquet(output_path)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df.to_parquet(output_path, index=False, engine='pyarrow')
    
    # ========== SUMMARY ==========
    print(f"\n=== Conversion Complete ===")
    print(f"Successfully written: {record_count:,} records")
    print(f"Failed records: {error_count:,}")
    print(f"Output file: {output_path}")
    
    # Hiển thị Parquet schema (kiểu dữ liệu của mỗi column)
    df_final = pd.read_parquet(output_path)
    print(f"\nParquet Schema (Data Types):")
    print(df_final.dtypes)
    print(f"\nFile size: {Path(output_path).stat().st_size / (1024**2):.2f} MB")

# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    # Kiểm tra số lượng arguments
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input_log_file> <output_parquet_file>")
        print(f"\nExample:")
        print(f"  python {sys.argv[0]} test.txt output_test.parquet")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Kiểm tra file input tồn tại
    if not Path(input_file).exists():
        print(f"Error: Input file '{input_file}' does not exist")
        sys.exit(1)
    
    # Thực hiện conversion
    try:
        parse_log_file(input_file, output_file)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

