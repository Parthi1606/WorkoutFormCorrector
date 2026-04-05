// hooks/usePoseLandmarker.ts
import { useEffect, useRef } from 'react';
import { TurboModuleRegistry } from 'react-native';
import { useFrameProcessor } from 'react-native-vision-camera';
import { runOnJS } from 'react-native-reanimated';
import type { Spec } from '../specs/NativePoseLandmarker';

let _poseLandmarker: Spec | null = null;
function getPoseLandmarker(): Spec {
  if (!_poseLandmarker) {
    _poseLandmarker = TurboModuleRegistry.getEnforcing<Spec>('PoseLandmarker');
  }
  return _poseLandmarker;
}

export interface LandmarkPoint {
  x: number;
  y: number;
  z: number;
  visibility: number;
}

export function usePoseLandmarker(
  onLandmarks: (landmarks: LandmarkPoint[]) => void
) {
  const initialized = useRef(false);
  const onLandmarksRef = useRef(onLandmarks);
  onLandmarksRef.current = onLandmarks;

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    getPoseLandmarker().initializePoseLandmarker()
      .then(() => console.log('[PoseLandmarker] initialized ✓'))
      .catch((e) => console.error('[PoseLandmarker] init failed:', e));
  }, []);

  function handleLandmarks(raw: ReadonlyArray<ReadonlyArray<number>>) {
    if (!raw || raw.length === 0) return;
    const landmarks: LandmarkPoint[] = raw.map((point) => ({
      x:          point[0],
      y:          point[1],
      z:          point[2],
      visibility: 1.0,
    }));
    onLandmarksRef.current(landmarks);
  }

  function handleError(msg: string) {
    console.warn('[PoseLandmarker] detect error:', msg);
  }

  function detectOnJS(b64: string) {
    getPoseLandmarker().detectPose(b64)
      .then((raw) => handleLandmarks(raw))
      .catch((e: any) => handleError(String(e)));
  }

  const frameProcessor = useFrameProcessor((frame) => {
    'worklet';
    const arrayBuffer = frame.toArrayBuffer();
    const uint8 = new Uint8Array(arrayBuffer);
    let binary = '';
    for (let i = 0; i < uint8.length; i++) {
      binary += String.fromCharCode(uint8[i]);
    }
    const base64 = btoa(binary);
    if (!base64) return;
    runOnJS(detectOnJS)(base64);
  }, []);

  return { frameProcessor };
}