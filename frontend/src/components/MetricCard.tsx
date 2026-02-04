import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subValue?: string;
  icon: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
  color: 'blue' | 'red' | 'green' | 'amber' | 'slate';
}

export const MetricCard: React.FC<MetricCardProps> = ({ title, value, subValue, icon: Icon, color, trend }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 border-blue-100',
    red: 'bg-red-50 text-red-600 border-red-100',
    green: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    amber: 'bg-amber-50 text-amber-600 border-amber-100',
    slate: 'bg-slate-100 text-slate-600 border-slate-200'
  };

  const trendColor = trend === 'up' ? 'text-red-500' : trend === 'down' ? 'text-emerald-500' : 'text-slate-400';

  return (
    <div className="bg-white rounded-lg p-3 border border-slate-100 shadow-sm flex items-start justify-between">
      <div className="min-w-0">
        <p className="text-xs font-semibold text-slate-500 mb-0.5 truncate">{title}</p>
        <div className="flex items-baseline space-x-1">
            <h3 className="text-xl font-bold text-slate-900 leading-tight">{value}</h3>
        </div>
        {subValue && <p className={`text-[10px] mt-0.5 ${trend ? trendColor : 'text-slate-400'} truncate`}>{subValue}</p>}
      </div>
      <div className={`p-1.5 rounded-md ${colorClasses[color]} border flex-shrink-0`}>
        <Icon size={16} />
      </div>
    </div>
  );
};