/* ============================================================
   GoldenHour — API Client
   Typed fetch wrapper with bearer token, refresh-on-401,
   idempotency keys, error normalisation
   ============================================================ */
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

  private async handleResponse<T>(res: Response, path?: string): Promise<T> {
    const isAuthRequest = path ? path.includes('/auth/login') || path.includes('/auth/register') : false;

    if (res.status === 401 && !isAuthRequest) {
      await this.tryRefresh();
      throw new Error('UNAUTHENTICATED');
    }

    if (!res.ok) {
      const body = (await res.json().catch(() => null)) as any;
      let msg = body?.error?.message || body?.message;

      // Handle FastAPI standard 422 validation detail array
      if (!msg && Array.isArray(body?.detail)) {
        const first = body.detail[0];
        const fieldName = Array.isArray(first?.loc) ? first.loc.slice(1).join(' ') : 'Field';
        msg = `${fieldName ? fieldName.toUpperCase() + ': ' : ''}${first?.msg || 'Invalid value provided.'}`;
      } else if (!msg && typeof body?.detail === 'string') {
        msg = body.detail;
      }

      if (!msg) {
        if (res.status === 401) {
          msg = 'Invalid email, phone number, or password.';
        } else if (res.status === 409) {
          msg = 'An account with this email or phone number already exists.';
        } else if (res.status === 404) {
          msg = 'The requested resource was not found.';
        } else {
          msg = `Request could not be completed (${res.status}).`;
        }
      }

      const err = new Error(msg) as Error & { code?: string; details?: unknown; status?: number };
      err.code = body?.error?.code || (res.status === 401 ? 'INVALID_CREDENTIALS' : 'UNKNOWN');
      err.details = body?.error?.details || body?.detail;
      err.status = res.status;
      throw err;
    }

    if (res.status === 204) return undefined as T;
    return res.json();
  }

  private resolveUrl(path: string): string {
    const base = (BASE_URL || '/api/v1').replace(/\/+$/, '');
    let p = path.trim();
    if (!p.startsWith('/')) {
      p = '/' + p;
    }
    // Prevent double prefixing when path has /api/v1/ or /api/
    if (base.endsWith('/api/v1') && p.startsWith('/api/v1/')) {
      p = p.slice(7);
    } else if (base.endsWith('/api/v1') && p.startsWith('/api/')) {
      p = p.slice(4);
    }

    if (base.startsWith('http://') || base.startsWith('https://')) {
      return `${base}${p}`;
    }
    return `${window.location.origin}${base}${p}`;
  }

  private async tryRefresh(): Promise<void> {
    if (this.refreshPromise) return this.refreshPromise;

    this.refreshPromise = (async () => {
      const refreshToken = useSessionStore.getState().refreshToken;
      if (!refreshToken) {
        useSessionStore.getState().logout();
        // Redirect to login
        window.location.href = '/auth';
        return;
      }

      try {
        const res = await fetch(this.resolveUrl('/auth/refresh'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!res.ok) {
          useSessionStore.getState().logout();
          // Redirect to login when refresh fails
          window.location.href = '/auth';
          return;
        }

        const data = await res.json();
        useSessionStore.getState().setTokens(data.access_token, data.refresh_token);
      } catch {
        useSessionStore.getState().logout();
        window.location.href = '/auth';
      } finally {
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  async get<T>(path: string, params?: Record<string, string>): Promise<T> {
    const resolved = this.resolveUrl(path);
    const url = new URL(resolved);
    if (params) {
      Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
    }
    const res = await fetch(url.toString(), { headers: this.getHeaders() });
    return this.handleResponse<T>(res, path);
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(this.resolveUrl(path), {
      method: 'POST',
      headers: this.getHeaders(true),
      body: body ? JSON.stringify(body) : undefined,
    });
    return this.handleResponse<T>(res, path);
  }

  async put<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(this.resolveUrl(path), {
      method: 'PUT',
      headers: this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    });
    return this.handleResponse<T>(res, path);
  }

  async delete<T>(path: string): Promise<T> {
    const res = await fetch(this.resolveUrl(path), {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    return this.handleResponse<T>(res, path);
  }
}

export const api = new ApiClient();
