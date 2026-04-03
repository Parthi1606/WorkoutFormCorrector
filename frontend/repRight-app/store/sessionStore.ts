// store/sessionStore.ts
// Zustand store for live session state.
// Updated every frame by useSession hook via WebSocket responses.

import { create } from 'zustand';

export type Phase = 'idle' | 'moving' | 'top' | 'lowering' | 'hold';

export interface FormCheck {
  label:   string;
  ok:      boolean;
  value:   number;
  message: string;
}

export interface SessionFrame {
  phase:        Phase;
  rep_count:    number;
  valid_reps:   number;
  active_side:  string | null;
  checks:       FormCheck[];
  rep_event:    'valid' | 'invalid' | null;
  faults:       string[];
  hold_seconds: number | null;
}

interface SessionState extends SessionFrame {
  isConnected:  boolean;
  exerciseName: string | null;

  // actions
  setFrame:      (frame: SessionFrame) => void;
  setConnected:  (v: boolean) => void;
  startSession:  (exerciseName: string) => void;
  resetSession:  () => void;
}

const EMPTY_FRAME: SessionFrame = {
  phase:        'idle',
  rep_count:    0,
  valid_reps:   0,
  active_side:  null,
  checks:       [],
  rep_event:    null,
  faults:       [],
  hold_seconds: null,
};

export const useSessionStore = create<SessionState>((set) => ({
  ...EMPTY_FRAME,
  isConnected:  false,
  exerciseName: null,

  setFrame:     (frame) => set({ ...frame }),
  setConnected: (v)     => set({ isConnected: v }),

  startSession: (exerciseName) => set({
    ...EMPTY_FRAME,
    exerciseName,
    isConnected: false,
  }),

  resetSession: () => set({
    ...EMPTY_FRAME,
    isConnected:  false,
    exerciseName: null,
  }),
}));
