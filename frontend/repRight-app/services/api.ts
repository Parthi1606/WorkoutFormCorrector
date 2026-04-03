// services/api.ts
// ─────────────────────────────────────────────────────────────────────────────
// Centralised HTTP client for all RepRight REST calls.
// All functions throw on non-2xx responses so callers can catch cleanly.
//
// Base URL is read from the same constants file used by the WebSocket hook.
// Set API_BASE in constants/theme.ts:
//   export const API_BASE = 'http://192.168.x.x:8001';   ← your machine's LAN IP

import { API_BASE } from '@/constants/theme';
import { useAuthStore } from '@/store/authStore';

// ── Internal helper ───────────────────────────────────────────────────────────

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }

  return res.json() as Promise<T>;
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface AuthResponse {
  token:   string;
  user_id: number;
  name:    string;
  email:   string;
}

/**
 * Exchange a Google ID token for a RepRight JWT.
 * Called immediately after Google Sign-In succeeds on the login screen.
 */
export async function loginWithGoogle(idToken: string): Promise<AuthResponse> {
  return request<AuthResponse>('/auth/google', {
    method: 'POST',
    body:   JSON.stringify({ id_token: idToken }),
  });
}

// ── Stats ─────────────────────────────────────────────────────────────────────

export interface AggregateStats {
  total_reps:     number;
  total_sessions: number;
  avg_form:       number;   // 0–100
  streak:         number;   // days
}

export interface ExerciseStat {
  exercise_key:   string;
  exercise_name:  string;
  total_reps:     number;
  total_sessions: number;
  avg_accuracy:   number;   // 0–100
}

/**
 * Fetch headline stats for the profile screen (streak, reps, form score).
 */
export async function fetchUserStats(
  userId: number,
  token: string,
): Promise<AggregateStats> {
  return request<AggregateStats>(`/stats/${userId}`, {}, token);
}

/**
 * Fetch per-exercise breakdown for the profile screen.
 */
export async function fetchExerciseBreakdown(
  userId: number,
  token: string,
): Promise<ExerciseStat[]> {
  return request<ExerciseStat[]>(`/stats/${userId}/breakdown`, {}, token);
}

// ── Session save ──────────────────────────────────────────────────────────────

export interface SaveSessionPayload {
  user_id:      number;
  exercise_key: string;
  total_reps:   number;
  valid_reps:   number;
  duration:     number;     // seconds
  started_at:   string;     // ISO 8601
  ended_at:     string;     // ISO 8601
}

export interface SaveSessionResponse {
  message:    string;
  session_id: number;
  accuracy:   number;
}

/**
 * Persist a completed session to the database.
 * Call this when the user leaves the session screen.
 */
export async function saveSession(
  payload: SaveSessionPayload,
  token: string,
): Promise<SaveSessionResponse> {
  return request<SaveSessionResponse>('/sessions/save', {
    method: 'POST',
    body:   JSON.stringify(payload),
  }, token);
}
