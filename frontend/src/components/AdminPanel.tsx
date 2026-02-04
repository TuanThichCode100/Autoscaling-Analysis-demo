import React from 'react';
import { Activity, Server, Zap, ShieldAlert, Cpu } from 'lucide-react';

// Định nghĩa Props khớp với dữ liệu từ App.tsx truyền xuống
interface AdminPanelProps {
  currentMetrics: {
    rpsActual: number;
    activeServers: number;
    latency: number;
  };
  // Capacity cố định là 50 (như backend), sau này có thể làm API để chỉnh
  capacityPerPod?: number;

  // New control props
  isStormActive: boolean;
  onToggleStorm: () => void;
  scaleThreshold: number; // For compatibility
  onThresholdChange: (val: number) => void; // For compatibility
  featureImportance: any; // For compatibility
}

export const AdminPanel: React.FC<AdminPanelProps> = ({
  currentMetrics,
  capacityPerPod = 50,
  isStormActive,
  onToggleStorm
}) => {
  const { rpsActual, activeServers, latency } = currentMetrics;

  // 1. Tính toán Logic Autoscaling (Mô phỏng lại logic backend để hiển thị)
  const totalClusterCapacity = activeServers * capacityPerPod;
  const utilization = totalClusterCapacity > 0 ? (rpsActual / totalClusterCapacity) * 100 : 0;

  // Tính số server CẦN THIẾT theo công thức
  const neededReplicas = Math.ceil(rpsActual / capacityPerPod);

  // Xác định trạng thái
  let statusColor = "bg-emerald-500";
  let statusText = "HEALTHY";

  if (neededReplicas > activeServers) {
    statusColor = "bg-red-500";
    statusText = "OVERLOAD (SCALING UP)";
  } else if (utilization > 80) {
    statusColor = "bg-amber-500";
    statusText = "HEAVY LOAD";
  } else if (utilization < 30 && activeServers > 1) {
    statusColor = "bg-blue-500";
    statusText = "UNDERUTILIZED (SCALING DOWN)";
  }

  return (
    <div className="h-full flex flex-col gap-3 font-sans">

      {/* --- PHẦN 1: METRICS CHÍNH (Real-time) --- */}
      <div className="grid grid-cols-1 gap-3">
        {/* Card RPS */}
        <div className="bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between transition-colors duration-300">
          <div>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-bold tracking-wider">Current RPS</p>
            <p className="text-2xl font-bold text-slate-800 dark:text-white">{rpsActual.toFixed(0)}</p>
            <p className="text-[10px] text-slate-400 dark:text-slate-500">Requests per second</p>
          </div>
          <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <Zap className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
        </div>

        {/* Card Active Servers */}
        <div className="bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between transition-colors duration-300">
          <div>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-bold tracking-wider">Active Pods</p>
            <div className="flex items-end gap-2">
              <p className="text-2xl font-bold text-slate-800 dark:text-white">{activeServers}</p>
              <span className="text-xs text-slate-500 mb-1">containers</span>
            </div>
            <p className="text-[10px] text-slate-400 dark:text-slate-500">Total Cap: {totalClusterCapacity} RPS</p>
          </div>
          <div className={`p-2 rounded-lg ${activeServers >= 10 ? 'bg-red-50 dark:bg-red-900/20 animate-pulse' : 'bg-emerald-50 dark:bg-emerald-900/20'}`}>
            <Server className={`w-5 h-5 ${activeServers >= 10 ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'}`} />
          </div>
        </div>
      </div>

      {/* --- PHẦN 2: TRẠNG THÁI CLUSTER (UTILIZATION) --- */}
      <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col gap-3 transition-colors duration-300">
        <div className="flex justify-between items-center">
          <h3 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase flex items-center gap-2">
            <Activity className="w-3 h-3" /> Cluster Load
          </h3>
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded text-white ${statusColor}`}>
            {statusText}
          </span>
        </div>

        {/* Progress Bar trực quan */}
        <div className="space-y-1">
          <div className="flex justify-between text-[10px] text-slate-500 dark:text-slate-400">
            <span>Used: {rpsActual.toFixed(0)}</span>
            <span>Capacity: {totalClusterCapacity}</span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
            <div
              className={`h-2.5 rounded-full transition-all duration-500 ${utilization > 100 ? 'bg-red-500 animate-pulse' :
                utilization > 75 ? 'bg-amber-500' : 'bg-blue-500'
                }`}
              style={{ width: `${Math.min(utilization, 100)}%` }}
            ></div>
          </div>
          <p className="text-right text-[10px] font-bold text-slate-600 dark:text-slate-400">{utilization.toFixed(1)}%</p>
        </div>
      </div>

      {/* --- PHẦN 3: GIẢI THÍCH THUẬT TOÁN (DECISION ENGINE) --- */}
      <div className="flex-1 bg-white dark:bg-slate-900 text-slate-800 dark:text-white p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col transition-colors duration-300">
        <div className="flex justify-between items-center mb-4 border-b border-slate-200 dark:border-slate-800 pb-2">
          <h3 className="text-xs font-bold uppercase text-slate-700 dark:text-slate-300 flex items-center gap-2">
            <Cpu className="w-3 h-3" /> Autoscaling Logic
          </h3>
          <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">Backend: v3.1</span>
        </div>

        <div className="flex-1 space-y-4 font-mono text-xs">
          {/* Tham số đầu vào */}
          <div className="bg-slate-50 dark:bg-slate-800/50 p-2 rounded border border-slate-200 dark:border-slate-700">
            <p className="text-slate-500 dark:text-slate-400 mb-1">Configuration:</p>
            <div className="flex justify-between">
              <span>CAPACITY_PER_POD (C):</span>
              <span className="text-emerald-600 dark:text-emerald-400 font-bold">{capacityPerPod} RPS</span>
            </div>
          </div>

          {/* Công thức toán học */}
          <div className="space-y-2">
            <p className="text-slate-500 dark:text-slate-400">Scaling Formula:</p>
            <div className="bg-slate-100 dark:bg-black p-2 rounded border border-slate-200 dark:border-slate-700 text-center">
              <p className="text-slate-600 dark:text-slate-300 mb-1">Replicas = Ceil( RPS / C )</p>
              <p className="text-lg text-emerald-600 dark:text-emerald-400 font-bold">
                {Math.ceil(rpsActual / capacityPerPod)} = ⌈ {rpsActual} / {capacityPerPod} ⌉
              </p>
            </div>
          </div>

          {/* Quyết định của hệ thống */}
          <div className="mt-2">
            <p className="text-slate-500 dark:text-slate-400 mb-1">Decision:</p>
            {neededReplicas !== activeServers ? (
              <div className="flex items-center gap-2 text-amber-500 dark:text-amber-300 animate-pulse">
                <ShieldAlert className="w-4 h-4" />
                <span>Scaling to {neededReplicas} replicas...</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
                <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                <span>Stable. Optimal replicas.</span>
              </div>
            )}
          </div>
        </div>

        {/* Latency cảnh báo */}
        <div className="mt-auto pt-3 border-t border-slate-200 dark:border-slate-800">
          <div className="flex justify-between items-center">
            <span className="text-slate-500 dark:text-slate-400">Avg Latency:</span>
            <span className={`font-bold ${latency > 200 ? 'text-red-500 dark:text-red-400' : 'text-slate-700 dark:text-slate-200'}`}>
              {latency.toFixed(2)} ms
            </span>
          </div>
          {latency > 500 && (
            <p className="text-[10px] text-red-500 dark:text-red-400 mt-1 text-right">⚠️ Latency Critical! System lagging.</p>
          )}
        </div>

      </div>
    </div>
  );
};