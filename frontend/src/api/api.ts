import { SystemMetric, LogEntry, ModelMetrics } from '../types';

// --- Configuration ---
// MOCK DATA: Fallback to localhost if env var missing
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

// --- WebSocket with Auto-Reconnect ---
interface WebSocketManager {
    ws: WebSocket | null;
    reconnectAttempts: number;
    maxReconnectAttempts: number;
    reconnectTimeout: NodeJS.Timeout | null;
    isIntentionallyClosed: boolean;
}

export const connectWebSocket = (
    onMetrics: (metric: SystemMetric) => void,
    onLogs: (logs: LogEntry[]) => void,
    onStatusChange: (status: 'connected' | 'disconnected' | 'connecting') => void
) => {
    const manager: WebSocketManager = {
        ws: null,
        reconnectAttempts: 0,
        maxReconnectAttempts: 10,
        reconnectTimeout: null,
        isIntentionallyClosed: false
    };

    const connect = () => {
        // Prevent multiple simultaneous connection attempts
        if (manager.ws?.readyState === WebSocket.CONNECTING ||
            manager.ws?.readyState === WebSocket.OPEN) {
            console.log('[WS] Already connected or connecting, skipping...');
            return;
        }

        onStatusChange('connecting');
        console.log(`[WS] Connecting to ${WS_URL}... (attempt ${manager.reconnectAttempts + 1})`);

        try {
            manager.ws = new WebSocket(WS_URL);

            manager.ws.onopen = () => {
                console.log('[WS] Connected successfully');
                onStatusChange('connected');
                manager.reconnectAttempts = 0; // Reset on successful connection
            };

            manager.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    if (data.metric) {
                        onMetrics(data.metric);
                    }

                    if (data.logs && Array.isArray(data.logs)) {
                        onLogs(data.logs);
                    }
                } catch (e) {
                    console.error('[WS] Parse error', e);
                }
            };

            manager.ws.onclose = (event) => {
                console.log(`[WS] Disconnected (code: ${event.code}, reason: ${event.reason || 'none'})`);
                onStatusChange('disconnected');

                // Only attempt reconnect if not intentionally closed
                if (!manager.isIntentionallyClosed) {
                    attemptReconnect();
                }
            };

            manager.ws.onerror = (err) => {
                console.error('[WS] Error', err);
                // Don't close here - let onclose handle reconnection
            };
        } catch (err) {
            console.error('[WS] Failed to create WebSocket', err);
            attemptReconnect();
        }
    };

    const attemptReconnect = () => {
        if (manager.isIntentionallyClosed) {
            console.log('[WS] Not reconnecting - connection was intentionally closed');
            return;
        }

        if (manager.reconnectAttempts >= manager.maxReconnectAttempts) {
            console.error('[WS] Max reconnection attempts reached. Giving up.');
            onStatusChange('disconnected');
            return;
        }

        // Exponential backoff: 1s, 2s, 4s, 8s, max 30s
        const delay = Math.min(1000 * Math.pow(2, manager.reconnectAttempts), 30000);
        console.log(`[WS] Reconnecting in ${delay}ms...`);

        manager.reconnectTimeout = setTimeout(() => {
            manager.reconnectAttempts++;
            connect();
        }, delay);
    };

    const disconnect = () => {
        manager.isIntentionallyClosed = true;

        if (manager.reconnectTimeout) {
            clearTimeout(manager.reconnectTimeout);
            manager.reconnectTimeout = null;
        }

        if (manager.ws) {
            manager.ws.close(1000, 'Client disconnect');
            manager.ws = null;
        }
    };

    // Initial connection
    connect();

    // Return disconnect function for cleanup
    return {
        disconnect,
        getState: () => manager.ws?.readyState
    };
};

// --- REST API ---
export const toggleStorm = async (enable: boolean): Promise<boolean> => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/control/storm?enable=${enable}`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to toggle storm');
        return true; // Success
    } catch (e) {
        console.error("Failed to toggle storm", e);
        // MOCK DATA: In a real app we might want to throw or return false
        return false;
    }
};

export const updateThreshold = async (value: number): Promise<boolean> => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/config/threshold?value=${value}`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to update threshold');
        return true;
    } catch (e) {
        console.error("Failed to update threshold", e);
        return false;
    }
};

export const fetchModelMetrics = async (): Promise<ModelMetrics | null> => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/ml/metrics`);
        if (!response.ok) throw new Error('Failed to fetch model metrics');
        const data = await response.json();
        return data.status === 'available' ? data : null;
    } catch (e) {
        console.error("Failed to fetch model metrics", e);
        return null;
    }
};
