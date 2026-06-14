import { useEffect, useState, useRef, useCallback } from 'react';

interface UseConsoleWebSocketResult {
  logs: string[];
  isConnected: boolean;
  error: string | null;
  clearLogs: () => void;
}

export function useConsoleWebSocket(): UseConsoleWebSocketResult {
  const [logs, setLogs] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectDelayRef = useRef<number>(1000);

  const connect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (socketRef.current) {
      socketRef.current.close(1000);
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/server/console`;

    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      setIsConnected(true);
      setError(null);
      reconnectDelayRef.current = 1000;
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'history') {
          setLogs(data.lines || []);
        } else if (data.type === 'log') {
          setLogs((prev) => {
            const next = [...prev, data.line];
            return next.slice(-2000); // Limit to 2000 lines for client performance
          });
        }
      } catch (err) {
        console.error('Failed to parse console socket message:', err);
      }
    };

    socket.onerror = () => {
      setError('Console WebSocket connection error occurred.');
    };

    socket.onclose = (event) => {
      if (socket !== socketRef.current) {
        return;
      }
      setIsConnected(false);
      socketRef.current = null;

      // Only attempt reconnect if not a clean unmount closure
      if (event.code !== 1000 && event.code !== 1001) {
        const nextDelay = Math.min(reconnectDelayRef.current * 2, 16000);
        console.warn(`Console WebSocket closed. Reconnecting in ${nextDelay}ms... (Code: ${event.code})`);
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
        socketRef.current.close(1000);
      }
    };
  }, [connect]);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  return { logs, isConnected, error, clearLogs };
}
