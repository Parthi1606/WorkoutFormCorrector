// hooks/useSession.ts
// Bridges the camera feed → MediaPipe → WebSocket pipeline.
//
// ─── MediaPipe integration point ─────────────────────────────────────────────
// When you're ready to wire MediaPipe:
//
//   1. Install react-native-vision-camera + a MediaPipe frame processor plugin
//      (e.g. vision-camera-pose-detection or your own native module).
//
//   2. Replace the TODO block below with a useFrameProcessor() call that:
//        a) Runs the MediaPipe Pose model on each camera frame (worklet).
//        b) Extracts the 33 landmark objects.
//        c) Calls sendLandmarks(landmarks) — same shape as below.
//
//   3. The rest of the pipeline (WebSocket → sessionStore → UI) needs zero
//      changes — it already consumes the server's JSON response.
//
// Interface the frame processor must produce per frame:
//   landmarks: Array<{ x: number; y: number; z: number; visibility: number }>
//   Length: exactly 33 items, in MediaPipe PoseLandmark order.
// ─────────────────────────────────────────────────────────────────────────────

import { useCallback } from 'react';
import { useWebSocket } from './useWebSocket';

export function useSession(exerciseName: string | null) {
  const { sendLandmarks } = useWebSocket(exerciseName);

  // TODO: replace with real frame processor output
  // This stub lets you test the UI and WebSocket flow end-to-end
  // by calling onFrame() manually (e.g. from a test button).
  const onFrame = useCallback((landmarks: Array<{
    x: number;
    y: number;
    z: number;
    visibility: number;
  }>) => {
    sendLandmarks(landmarks);
  }, [sendLandmarks]);

  return { onFrame };
}
