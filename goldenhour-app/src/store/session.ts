/* ============================================================
   GoldenHour — Session Store (Zustand)
   ============================================================ */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Role, User } from '../types/api';

interface SessionState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;

  setUser: (user: User) => void;
  setTokens: (access: string, refresh: string) => void;
  setSession: (user: User, tokens?: { access_token?: string; refresh_token?: string }) => void;
  clearSession: () => void;
  login: (user: User, access: string, refresh: string) => void;
  logout: () => void;
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      setUser: (user) => set({ user }),
      setTokens: (access, refresh) => set({ accessToken: access, refreshToken: refresh }),
      setSession: (user, tokens) =>
        set({
          user,
          accessToken: tokens?.access_token || null,
          refreshToken: tokens?.refresh_token || null,
          isAuthenticated: true,
        }),
      clearSession: () =>
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false }),
      login: (user, access, refresh) =>
        set({ user, accessToken: access, refreshToken: refresh, isAuthenticated: true }),
      logout: () =>
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false }),
    }),
    { name: 'gh-session' }
  )
);

/** Quick role check */
export function useRole(): Role | null {
  return useSessionStore((s) => s.user?.role ?? null);
}
