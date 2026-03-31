// hooks/useWebSocket.ts
// Manages the WebSocket lifecycle for one exercise session.
// Connects to ws://{WS_BASE}/session/{exerciseName} on mount,
// disconnects on unmount or when exerciseName changes.

import { useEffect, useRef, useCallback } from 'react';
import { WS_BASE } from '../constants/theme';
import { useSessionStore, SessionFrame } from '../store/sessionStore';

interface LandmarkPoint {
  x: number;
  y: number;
  z: number;
  visibility: number;
}

export function useWebSocket(exerciseName: string | null) {
  const ws             = useRef<WebSocket | null>(null);
  const setFrame       = useSessionStore((s) => s.setFrame);
  const setConnected   = useSessionStore((s) => s.setConnected);

  // ── Connect / disconnect ────────────────────────────────────────────────
  useEffect(() => {
    if (!exerciseName) return;

    const url = `${WS_BASE}/session/${exerciseName}`;
    const socket = new WebSocket(url);
    ws.current = socket;

    socket.onopen = () => {
      setConnected(true);
      console.log(`[WS] connected → ${url}`);
    };

    socket.onmessage = (event) => {
      try {
        const frame: SessionFrame = JSON.parse(event.data);
        if (frame.phase) {          // ignore error frames silently
          setFrame(frame);
        }
      } catch (e) {
        console.warn('[WS] parse error:', e);
      }
    };

    socket.onerror = (e) => {
      console.error('[WS] error:', e);
    };

    socket.onclose = () => {
      setConnected(false);
      console.log('[WS] disconnected');
    };

    return () => {
      socket.close();
      ws.current = null;
    };
  }, [exerciseName]);

  // ── Send landmark frame ─────────────────────────────────────────────────
  const sendLandmarks = useCallback((landmarks: LandmarkPoint[]) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ landmarks }));
    }
  }, []);

  return { sendLandmarks };
}
