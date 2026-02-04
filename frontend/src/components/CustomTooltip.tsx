import React from 'react';

interface CustomTooltipProps {
    active?: boolean;
    payload?: any[];
    label?: string;
}

export const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
    if (!active || !payload || payload.length === 0) return null;

    return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-slate-200">
            <p className="text-xs font-semibold text-slate-600 mb-2">
                {label}
            </p>
            <div className="space-y-1">
                {payload.map((entry, index) => (
                    <div key={index} className="flex items-center justify-between gap-4">
                        <span className="text-xs flex items-center gap-1">
                            <span
                                className="w-2 h-2 rounded-full"
                                style={{ backgroundColor: entry.color }}
                            />
                            {entry.name}
                        </span>
                        <span className="text-xs font-bold">
                            {typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}
                        </span>
                    </div>
                ))}

                {/* Show difference for RPS chart */}
                {payload.length === 2 && payload[0].dataKey === 'rpsActual' && (
                    <div className="pt-1 mt-1 border-t border-slate-100">
                        <span className="text-xs text-slate-500">
                            Diff: {(payload[0].value - payload[1].value).toFixed(0)} RPS
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
};
