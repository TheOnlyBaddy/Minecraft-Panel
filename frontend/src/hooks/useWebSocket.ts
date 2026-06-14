import { useEffect, useState, useRef, useCallback } from 'react';

export interface TelemetryData {
  timestamp: string;
  cpu_percent: number;
  memory_used: number;
  memory_total: number;
  disk_used: number;
  disk_total: number;
  active_players: number;
  active_players_list?: string[];
  server_status: 'STOPPED' | 'STARTING' | 'RUNNING' | 'STOPPING' | 'CRASHED';
  server_address: string;
}

interface UseWebSocketResult {
  data: TelemetryData | null;
  isConnected: boolean;
  error: string | null;
}

export function useWebSocket(): UseWebSocketResult {
  const [data, setData] = useState<TelemetryData | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectDelayRef = useRef<number>(1000); // Start with 1s reconnect delay
  const socketRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    // Clear any pending reconnects
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (socketRef.current) {
      socketRef.current.close(1000);
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/server/telemetry`;

    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      setIsConnected(true);
      setError(null);
      reconnectDelayRef.current = 1000; // Reset delay on successful connection
    };

    socket.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data) as TelemetryData;
        setData(parsedData);
      } catch (err) {
        console.error('Failed to parse telemetry data', err);
      }
    };

    socket.onerror = () => {
      setError('WebSocket connection error occurred.');
    };

    socket.onclose = (event) => {
      if (socket !== socketRef.current) {
        return;
      }
      setIsConnected(false);
      socketRef.current = null;

      // Do not reconnect if closed cleanly by client unmounting
      // WS 1000 = Normal Closure, WS 1001 = Going Away (unmount)
      if (event.code !== 1000 && event.code !== 1001) {
        const nextDelay = Math.min(reconnectDelayRef.current * 2, 16000);
        console.warn(`WebSocket closed. Reconnecting in ${nextDelay}ms... (Code: ${event.code})`);
        reconnectDelayRef.current = nextDelay;
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, nextDelay);
      }
    };
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        // Close with normal closure code (1000) to prevent reconnect loop
        socketRef.current.close(1000);
      }
    };
  }, [connect]);

  return { data, isConnected, error };
}
