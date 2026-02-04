import React from 'react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { SystemMetric } from '../types';

interface OpsDashboardProps {
  metrics: SystemMetric[];
}

const CustomTooltip = ({ active, payload, label, unit }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900/90 dark:bg-slate-800/90 border border-slate-700 p-2 rounded shadow-xl backdrop-blur-sm text-xs text-white z-50">
        <p className="font-mono text-slate-400 mb-1">{label}</p>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: payload[0].color }}></span>
          <span className="font-bold">{payload[0].value}</span>
          <span className="text-slate-400 text-[10px]">{unit}</span>
        </div>
      </div>
    );
  }
  return null;
};

export const OpsDashboard: React.FC<OpsDashboardProps> = ({ metrics }) => {
  // Hiển thị message nếu không có data
  if (!metrics || metrics.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-2 bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-4 transition-colors duration-300">
        <div className="text-slate-400 dark:text-slate-500 text-sm">Chưa có dữ liệu</div>
        <div className="text-slate-500 dark:text-slate-600 text-xs">Đang chờ traffic từ API...</div>
      </div>
    );
  }

  // Note: Colors for charts are kept static for consistency, but containers adapt.
  // Recharts grids are set to specific hexes. In dark mode, #f1f5f9 (slate-100) might be too bright on slate-900.
  // Ideally we use a variable or context, but for now we'll accept the light grid or use a very transparent white.
  // Since we can't easily switch Recharts props with CSS classes, we'll keep the grid subtle.

  return (
    <div className="h-full flex flex-col gap-3 font-sans">

      {/* 1. RPS (Xanh Lá) */}
      <div className="flex-1 bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-2 flex flex-col min-h-0 transition-colors duration-300">
        <div className="flex justify-between items-center mb-0.5">
          <h3 className="text-[10px] font-bold text-slate-600 dark:text-slate-400 uppercase flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span> RPS (Requests/s)
          </h3>
        </div>
        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={metrics} syncId="dashboardSync">
              <defs>
                <linearGradient id="colorRps" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" strokeOpacity={0.2} />
              <XAxis dataKey="timestamp" hide />
              <YAxis tick={{ fontSize: 9, fill: '#94a3b8' }} axisLine={false} tickLine={false} width={30} />
              <Tooltip content={<CustomTooltip unit="req/s" />} cursor={{ stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '4 4' }} />
              <Area
                type="monotone"
                dataKey="rpsActual"
                stroke="#10b981"
                fill="url(#colorRps)"
                strokeWidth={2}
                isAnimationActive={true}
                activeDot={{ r: 4, strokeWidth: 0, fill: '#10b981' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 2. THROUGHPUT - MỚI (Màu Cam) */}
      <div className="flex-1 bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-2 flex flex-col min-h-0 transition-colors duration-300">
        <div className="flex justify-between items-center mb-0.5">
          <h3 className="text-[10px] font-bold text-slate-600 dark:text-slate-400 uppercase flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-orange-500"></span> Throughput (Băng thông)
          </h3>
        </div>
        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={metrics} syncId="dashboardSync">
              <defs>
                <linearGradient id="colorBytes" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f97316" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#f97316" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" strokeOpacity={0.2} />
              <XAxis dataKey="timestamp" hide />
              <YAxis tick={{ fontSize: 9, fill: '#94a3b8' }} axisLine={false} tickLine={false} width={30} />
              <Tooltip content={<CustomTooltip unit="KB/s" />} cursor={{ stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '4 4' }} />
              <Area
                type="monotone"
                dataKey="throughput"
                stroke="#f97316"
                fill="url(#colorBytes)"
                strokeWidth={2}
                isAnimationActive={true}
                activeDot={{ r: 4, strokeWidth: 0, fill: '#f97316' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 3. LATENCY (Tím) */}
      <div className="flex-1 bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-2 flex flex-col min-h-0 transition-colors duration-300">
        <div className="flex justify-between items-center mb-0.5">
          <h3 className="text-[10px] font-bold text-slate-600 dark:text-slate-400 uppercase flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-indigo-500"></span> Latency (Độ trễ)
          </h3>
        </div>
        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={metrics} syncId="dashboardSync">
              <defs>
                <linearGradient id="colorLatency" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" strokeOpacity={0.2} />
              <XAxis dataKey="timestamp" hide />
              <YAxis tick={{ fontSize: 9, fill: '#94a3b8' }} axisLine={false} tickLine={false} width={30} />
              <Tooltip content={<CustomTooltip unit="ms" />} cursor={{ stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '4 4' }} />
              <Area
                type="monotone"
                dataKey="latency"
                stroke="#6366f1"
                fill="url(#colorLatency)"
                strokeWidth={2}
                isAnimationActive={true}
                activeDot={{ r: 4, strokeWidth: 0, fill: '#6366f1' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 4. ERROR RATE (Đỏ) */}
      <div className="flex-1 bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-2 flex flex-col min-h-0 transition-colors duration-300">
        <div className="flex justify-between items-center mb-0.5">
          <h3 className="text-[10px] font-bold text-slate-600 dark:text-slate-400 uppercase flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500"></span> Error Rate (Lỗi)
          </h3>
        </div>
        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={metrics} syncId="dashboardSync">
              <defs>
                <linearGradient id="colorError" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" strokeOpacity={0.2} />
              <XAxis dataKey="timestamp" tick={{ fontSize: 9, fill: '#94a3b8' }} axisLine={false} tickLine={false} minTickGap={30} />
              <YAxis tick={{ fontSize: 9, fill: '#94a3b8' }} axisLine={false} tickLine={false} width={30} domain={[0, 100]} allowDecimals={false} />
              <Tooltip content={<CustomTooltip unit="%" />} cursor={{ stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '4 4' }} />
              <Area
                type="monotone"
                dataKey="errorRate"
                stroke="#ef4444"
                fill="url(#colorError)"
                strokeWidth={2}
                isAnimationActive={true}
                activeDot={{ r: 4, strokeWidth: 0, fill: '#ef4444' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

    </div>
  );
};