import React, { useRef, useEffect, useState, useCallback } from 'react';

// 1. Cập nhật Interface khớp 100% với JSON từ Backend trả về
interface LogEntry {
  time: string;     // VD: "08:10:05"
  method: string;   // VD: "GET"
  endpoint: string; // VD: "/images/logo.gif"
  status: string;   // VD: "200"
  latency: number;  // VD: 54.2
  host: string;     // VD: "backend-api"
}

// Component hiển thị từng dòng Log
const LogEntryItem = React.memo<{ log: LogEntry; getStatusColor: (status: string) => string }>(
  ({ log, getStatusColor }) => (
    <div className="break-all font-mono border-b border-slate-100 dark:border-slate-800/50 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors px-2 py-1.5 rounded text-[11px]">
      {/* Thời gian */}
      <span className="text-slate-400 dark:text-slate-500 mr-2">[{log.time}]</span>

      {/* Method (GET/POST) */}
      <span className={`font-bold mr-2 ${log.method === 'GET' ? 'text-blue-600 dark:text-blue-400' : 'text-purple-600 dark:text-purple-400'}`}>
        {log.method}
      </span>

      {/* Đường dẫn endpoint */}
      <span className="text-slate-600 dark:text-slate-300 mr-2">{log.endpoint}</span>

      {/* Status Code */}
      <span className={`font-bold mr-2 ${getStatusColor(log.status)}`}>
        {log.status}
      </span>

      {/* Latency (Quan trọng để xem lag) */}
      <span className={`mr-1 ${log.latency > 500 ? 'text-red-500 dark:text-red-400 font-bold' : 'text-slate-400'}`}>
        {log.latency}ms
      </span>
    </div>
  )
);

LogEntryItem.displayName = 'LogEntryItem';

export const LogViewer: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // 2. Hàm lấy màu dựa trên Status Code (Backend trả về string nên cần parse)
  const getStatusColor = useCallback((statusStr: string) => {
    const status = parseInt(statusStr, 10);
    if (status >= 500) return 'text-red-600 dark:text-red-500';
    if (status >= 400) return 'text-amber-500 dark:text-yellow-400';
    if (status >= 300) return 'text-cyan-600 dark:text-cyan-400';
    return 'text-emerald-600 dark:text-green-400'; // 200 OK
  }, []);

  // 3. Hàm gọi API Backend (Quan trọng nhất)
  const fetchLogs = async () => {
    try {
      // Gọi vào API mà chúng ta vừa viết ở bước trước
      const response = await fetch('http://localhost:8000/api/logs');
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data: LogEntry[] = await response.json();

      // Đảo ngược mảng để log mới nhất nằm dưới cùng (tùy sở thích hiển thị)
      // Backend đang trả về mới nhất trước -> nhưng log viewer thường đọc từ trên xuống
      // Ở đây mình giữ nguyên thứ tự Backend trả về (mới nhất ở đầu) hoặc đảo lại
      // Hãy thử đảo lại để log mới chạy xuống dưới đáy giống terminal thật:
      setLogs(data.reverse());
    } catch (error) {
      console.error("Failed to fetch logs:", error);
    }
  };

  // 4. Polling dữ liệu (Gọi liên tục mỗi 2 giây)
  useEffect(() => {
    fetchLogs(); // Gọi ngay lần đầu
    const interval = setInterval(fetchLogs, 2000); // Lặp lại
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll logic (Giữ nguyên như cũ vì nó tốt rồi)
  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  return (
    <div className="h-full w-full flex flex-col bg-white dark:bg-[#0d1117] overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm transition-colors duration-300">
      {/* Header nhỏ cho đẹp */}
      <div className="bg-slate-50 dark:bg-slate-900 px-3 py-2 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center transition-colors duration-300">
        <span className="text-xs font-bold text-slate-600 dark:text-slate-400 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          LIVE ACCESS LOGS
        </span>
        <span className="text-[10px] text-slate-500 dark:text-slate-600 font-mono">source: influxdb</span>
      </div>

      <div className="flex-1 overflow-y-auto p-2 custom-scrollbar-dark font-mono text-xs text-slate-800 dark:text-slate-200">
        {logs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 dark:text-slate-600 space-y-2 opacity-70">
            <div className="animate-spin h-5 w-5 border-2 border-current border-t-transparent rounded-full"></div>
            <span>Waiting for traffic...</span>
          </div>
        ) : (
          logs.map((log, index) => (
            // Dùng index làm key tạm vì log realtime thay đổi nhanh
            <LogEntryItem key={index} log={log} getStatusColor={getStatusColor} />
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};