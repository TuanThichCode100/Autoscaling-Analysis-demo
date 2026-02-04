import React, { useState, useEffect } from 'react';
import { OpsDashboard } from './components/OpsDashboard';
import { AdminPanel } from './components/AdminPanel';
import { LogViewer } from './components/LogViewer';
import { ThemeProvider } from './context/ThemeContext';
import { ThemeToggle } from './components/ThemeToggle';

// Types khớp với dữ liệu Frontend cần vẽ
import { SystemMetric } from './types';

// Mock data cho Feature Importance (Vì backend chưa tính cái này)
import { BASE_FEATURE_IMPORTANCE } from './constants';

const AppContent: React.FC = () => {
    // --- STATE ---
    // 1. Dữ liệu lịch sử để vẽ biểu đồ (Lấy từ /api/metrics/history)
    const [metrics, setMetrics] = useState<SystemMetric[]>([]);

    // 2. Trạng thái hệ thống hiện tại (Lấy từ /api/status)
    const [systemStatus, setSystemStatus] = useState({
        rps: 0,
        latency: 0,
        replicas: 0,
        status: "Unknown"
    });

    const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected'>('disconnected');

    // Giữ lại state UI cho đẹp (chức năng trigger storm thật cần gọi API khác)
    const [isStormActive, setIsStormActive] = useState(false);
    const [scaleThreshold, setScaleThreshold] = useState(50); // Mặc định khớp với Capacity

    // --- EFFECT: POLLING DỮ LIỆU TỪ BACKEND ---
    useEffect(() => {
        const fetchData = async () => {
            try {
                // 1. Gọi API lấy trạng thái tức thời
                const statusRes = await fetch('http://localhost:8000/api/status');
                const statusData = await statusRes.json();

                // 2. Gọi API lấy lịch sử biểu đồ
                const historyRes = await fetch('http://localhost:8000/api/metrics/history');
                const historyData = await historyRes.json();

                // 3. Cập nhật State
                setSystemStatus({
                    rps: statusData.current_rps || 0,
                    latency: statusData.current_latency || 0,
                    replicas: statusData.replicas || 1,
                    status: statusData.status || "Unknown"
                });

                // Mapping dữ liệu từ Backend sang format của Chart
                // Backend trả về: { time: "10:00", rps: 10, latency: 20 }
                // Frontend cần: SystemMetric interface
                const formattedMetrics: SystemMetric[] = Array.isArray(historyData)
                    ? historyData.map((d: any) => ({
                        timestamp: d.time || new Date().toLocaleTimeString(),
                        rpsActual: d.rps || 0,
                        rpsPredicted: 0,
                        latency: d.latency || 0,
                        activeServers: 0,
                        errorRate: d.error_rate || 0,
                        cpuUtilization: 0,
                        memoryUsage: 0,
                        throughput: d.throughput || 0
                    }))
                    : [];

                setMetrics(formattedMetrics);
                setConnectionStatus('connected');
            } catch (error) {
                console.error("Failed to fetch backend data:", error);
                setConnectionStatus('disconnected');
            }
        };

        // Gọi ngay lập tức
        fetchData();

        // Lặp lại mỗi 2 giây (Polling)
        const interval = setInterval(fetchData, 2000);

        // Cleanup khi tắt app
        return () => clearInterval(interval);
    }, []);

    // --- HANDLERS (Gọi API điều khiển) ---
    const handleToggleStorm = async () => {
        const newState = !isStormActive;
        try {
            console.log(`Sending Storm Request: ${newState}`);
            const res = await fetch('http://localhost:8000/api/control/storm', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: newState })
            });

            if (res.ok) {
                setIsStormActive(newState);
                console.log("Storm toggled successfully");
            } else {
                console.error("Failed to toggle storm");
            }
        } catch (error) {
            console.error("API Error:", error);
        }
    };

    const handleThresholdChange = (val: number) => {
        setScaleThreshold(val);
        // TODO: Gọi API /api/config nếu có
    };

    // Chuẩn bị dữ liệu để truyền xuống AdminPanel
    const latestMetricForAdmin = {
        timestamp: new Date().toLocaleTimeString(),
        rpsActual: systemStatus.rps,
        rpsPredicted: 0,
        activeServers: systemStatus.replicas, // Quan trọng: Số Pod thật
        latency: systemStatus.latency,
        errorRate: 0, // Chưa có
        cpuUtilization: 0, // Chưa có
        memoryUsage: 0 // Chưa có
    };

    return (
        <div className="h-screen flex flex-col font-sans overflow-hidden bg-slate-50 dark:bg-[#0d1117] text-slate-900 dark:text-slate-100 transition-colors duration-300">
            {/* Top Navbar */}
            <nav className="flex-none bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 py-2 flex items-center justify-between shadow-sm h-14 transition-colors duration-300">
                <div className="flex items-center space-x-3">
                    <div className="bg-blue-600 rounded p-1.5 shadow-lg shadow-blue-500/20">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                    </div>
                    <h1 className="text-base font-bold tracking-tight text-slate-800 dark:text-white">AutoScaler Watchtower</h1>
                </div>
                <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-3 text-xs text-slate-500 dark:text-slate-400 font-medium">
                        <span className="flex items-center px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded-full border border-slate-200 dark:border-slate-700">
                            <span className={`w-1.5 h-1.5 rounded-full mr-2 ${connectionStatus === 'connected' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-red-500'}`}></span>
                            {connectionStatus === 'connected' ? 'Connected' : 'Offline'}
                        </span>
                        <span className="flex items-center px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded-full border border-slate-200 dark:border-slate-700">
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mr-2 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></span>
                            v3.1
                        </span>
                    </div>
                    <div className="h-6 w-px bg-slate-200 dark:bg-slate-700 mx-2"></div>

                    {/* Nút Trigger Storm (Tròn nhỏ) */}
                    <button
                        onClick={handleToggleStorm}
                        title={isStormActive ? "Stop Traffic Storm" : "Trigger Traffic Storm (Spike)"}
                        className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg ${isStormActive
                                ? 'bg-red-500 hover:bg-red-600 animate-pulse shadow-red-500/50'
                                : 'bg-slate-100 dark:bg-slate-800 hover:bg-red-100 dark:hover:bg-red-900/30 text-slate-500 dark:text-slate-400 hover:text-red-500'
                            }`}
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </button>

                    <ThemeToggle />
                </div>
            </nav>

            {/* Main Grid Layout */}
            <main className="flex-1 overflow-hidden p-4">
                <div className="grid grid-cols-12 gap-4 h-full">

                    {/* Column 1: Logs (Left - 25% -> Reduced from 33% to satisfy 'narrower' request) */}
                    <div className="col-span-12 md:col-span-3 lg:col-span-3 h-full flex flex-col min-h-0 bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden transition-colors duration-300">
                        {/* LogViewer tự lo việc gọi API, không cần truyền props logs nữa */}
                        <LogViewer />
                    </div>

                    {/* Column 2: Charts (Middle - 50% -> Increased to fill space) */}
                    <div className="col-span-12 md:col-span-6 lg:col-span-6 h-full flex flex-col gap-4 min-h-0">
                        {/* Truyền dữ liệu lịch sử vào biểu đồ */}
                        <OpsDashboard metrics={metrics} />
                    </div>

                    {/* Column 3: Metrics & Controls (Right - 25%) */}
                    <div className="col-span-12 md:col-span-3 lg:col-span-3 h-full flex flex-col min-h-0">
                        <AdminPanel
                            isStormActive={isStormActive}
                            onToggleStorm={handleToggleStorm}
                            scaleThreshold={scaleThreshold}
                            onThresholdChange={handleThresholdChange}
                            featureImportance={BASE_FEATURE_IMPORTANCE} // Dữ liệu tĩnh tạm thời
                            currentMetrics={latestMetricForAdmin} // Dữ liệu thật từ Backend
                        />
                    </div>

                </div>
            </main>
        </div>
    );
};

const App: React.FC = () => {
    return (
        <ThemeProvider>
            <AppContent />
        </ThemeProvider>
    );
};

export default App;