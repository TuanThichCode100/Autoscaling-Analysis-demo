# Sử dụng Node 18 trên nền Alpine cho nhẹ
FROM node:18-alpine

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy file định nghĩa gói tin trước (để tận dụng Docker cache)
COPY package.json ./
# Copy package-lock.json nếu có (dấu * giúp không lỗi nếu thiếu file này)
COPY package-lock.json* ./

# --- SỬA LỖI Ở ĐÂY ---
# Thay vì dùng npm ci phức tạp, ta dùng npm install đơn giản
# --legacy-peer-deps: Bỏ qua lỗi xung đột phiên bản cũ
RUN npm install --legacy-peer-deps

# Copy toàn bộ code nguồn vào
COPY . .

# Mở port cho Vite
EXPOSE 5173

# Chạy server dev
CMD ["npm", "run", "dev", "--", "--host"]