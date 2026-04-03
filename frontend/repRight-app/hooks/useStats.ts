// hooks/useStats.ts
// ─────────────────────────────────────────────────────────────────────────────
// Fetches aggregate stats + exercise breakdown for the profile screen.
// Returns loading state, error state, and the data.

import { useState, useEffect, useCallback } from 'react';
import { fetchUserStats, fetchExerciseBreakdown, AggregateStats, ExerciseStat } from '@/services/api';
import { useAuthStore } from '@/store/authStore';

interface UseStatsResult {
  stats:     AggregateStats | null;
  breakdown: ExerciseStat[];
  loading:   boolean;
  error:     string | null;
  refresh:   () => void;
}

export function useStats(): UseStatsResult {
  const user  = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.token);

  const [stats,     setStats]     = useState<AggregateStats | null>(null);
  const [breakdown, setBreakdown] = useState<ExerciseStat[]>([]);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState<string | null>(null);

  const load = useCallback(async () => {
    // Guest mode — no user_id or token, skip fetch
    if (!user?.id || !token) return;

    setLoading(true);
    setError(null);

    try {
      const [agg, breakdown] = await Promise.all([
        fetchUserStats(Number(user.id), token),
        fetchExerciseBreakdown(Number(user.id), token),
      ]);
      setStats(agg);
      setBreakdown(breakdown);
    } catch (e: any) {
      setError(e.message ?? 'Failed to load stats');
    } finally {
      setLoading(false);
    }
  }, [user?.id, token]);

  useEffect(() => {
    load();
  }, [load]);

  return { stats, breakdown, loading, error, refresh: load };
}
