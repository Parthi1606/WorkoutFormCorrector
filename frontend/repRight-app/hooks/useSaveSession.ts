// hooks/useSaveSession.ts
// ─────────────────────────────────────────────────────────────────────────────
// Saves a completed exercise session to the backend.
// Call saveOnExit() from the session screen's cleanup effect.
//
// Usage in app/session/[exercise].tsx:
//
//   const { saveOnExit } = useSaveSession(exercise, startedAt);
//
//   useEffect(() => {
//     return () => { saveOnExit(); };   // fires when screen unmounts
//   }, []);

import { useRef, useCallback } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useSessionStore } from '@/store/sessionStore';
import { saveSession } from '@/services/api';

export function useSaveSession(exerciseKey: string, startedAt: Date) {
  const user     = useAuthStore((s) => s.user);
  const token    = useAuthStore((s) => s.token);
  const repCount = useSessionStore((s) => s.rep_count);
  const validReps= useSessionStore((s) => s.valid_reps);

  // Use refs so the cleanup closure always sees the latest values
  const repCountRef  = useRef(repCount);
  const validRepsRef = useRef(validReps);
  repCountRef.current  = repCount;
  validRepsRef.current = validReps;

  const saveOnExit = useCallback(async () => {
    // Skip for guests and skip if no reps were completed
    if (!user?.id || !token || repCountRef.current === 0) return;

    const endedAt = new Date();

    try {
      await saveSession(
        {
          user_id:      Number(user.id),
          exercise_key: exerciseKey,
          total_reps:   repCountRef.current,
          valid_reps:   validRepsRef.current,
          duration:     Math.round((endedAt.getTime() - startedAt.getTime()) / 1000),
          started_at:   startedAt.toISOString(),
          ended_at:     endedAt.toISOString(),
        },
        token,
      );
      console.log('[session] saved to backend');
    } catch (e) {
      // Non-critical — log but don't surface to user
      console.warn('[session] save failed:', e);
    }
  }, [user?.id, token, exerciseKey, startedAt]);

  return { saveOnExit };
}
