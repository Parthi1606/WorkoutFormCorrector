// store/authStore.ts
// Zustand store for authentication state.
// Google OAuth is handled via expo-auth-session in the login screen;
// the resulting token/user object is written here.

import { create } from 'zustand';

export interface UserProfile {
  id:        string;
  name:      string;
  email:     string;
  avatarUrl: string | null;
}

interface AuthState {
  user:      UserProfile | null;
  token:     string | null;
  isLoading: boolean;

  setUser:   (user: UserProfile, token: string) => void;
  logout:    () => void;
  setLoading:(v: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user:      null,
  token:     null,
  isLoading: false,

  setUser: (user, token) => set({ user, token }),
  logout:  ()            => set({ user: null, token: null }),
  setLoading: (v)        => set({ isLoading: v }),
}));
