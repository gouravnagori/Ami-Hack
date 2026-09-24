/* ============================================================
   GoldenHour — API Client
   Typed fetch wrapper with bearer token, refresh-on-401,
   idempotency keys, error normalisation
   ============================================================ */
import type { ApiError } from '../types/api';
import { useSessionStore } from '../store/session';

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

class ApiClient {
  private refreshPromise: Promise<void> | null = null;

  private getHeaders(idempotent = false): HeadersInit {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    const token = useSessionStore.getState().accessToken;
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (idempotent) {
      headers['Idempotency-Key'] = crypto.randomUUID();
    }

    return headers;
  }

  private async handleResponse<T>(res: Response): Promise<T> {
    if (res.status === 401) {
      await this.tryRefresh();
      throw new Error('UNAUTHENTICATED');
    }

    if (!res.ok) {
      const body = await res.json().catch(() => null) as ApiError | null;
      const msg = body?.error?.message || `Request failed: ${res.status}`;
      const err = new Error(msg) as Error & { code?: string; details?: unknown };
      err.code = body?.error?.code || 'UNKNOWN';
      err.details = body?.error?.details;
      throw err;
    }

    if (res.status === 204) return undefined as T;
    return res.json();
  }

  private async tryRefresh(): Promise<void> {
    if (this.refreshPromise) return this.refreshPromise;

    this.refreshPromise = (async () => {
      const refreshToken = useSessionStore.getState().refreshToken;
      if (!refreshToken) {
        useSessionStore.getState().logout();
        return;
      }

      try {
        const res = await fetch(`${BASE_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!res.ok) {
          useSessionStore.getState().logout();
          return;
        }

        const data = await res.json();
        useSessionStore.getState().setTokens(data.access_token, data.refresh_token);
      } catch {
        useSessionStore.getState().logout();
      } finally {
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  async get<T>(path: string, params?: Record<string, string>): Promise<T> {
    const url = new URL(`${BASE_URL}${path}`, window.location.origin);
    if (params) {
      Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
    }
    const res = await fetch(url.toString(), { headers: this.getHeaders() });
    return this.handleResponse<T>(res);
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: body ? JSON.stringify(body) : undefined,
    });
    return this.handleResponse<T>(res);
  }

  async put<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    });
    return this.handleResponse<T>(res);
  }

  async delete<T>(path: string): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    return this.handleResponse<T>(res);
  }
}

export const api = new ApiClient();
