/**
 * ConsultOS Centralized API Client
 * Manages HTTP communications, error normalization, AbortController timeouts,
 * connectivity status detection, and SSE streaming.
 */

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: any;
}

export type ConnectionState = 'connected' | 'reconnecting' | 'offline';

const STORAGE_KEY_API_BASE = 'consultos_api_base_url';
const STORAGE_KEY_USE_SIMULATOR = 'consultos_use_simulator';

export function getStoredApiBaseUrl(): string {
  const stored = localStorage.getItem(STORAGE_KEY_API_BASE);
  if (stored) return stored.trim();
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  return envUrl && typeof envUrl === 'string' ? envUrl.trim() : 'http://localhost:8000';
}

export function setStoredApiBaseUrl(url: string): void {
  localStorage.setItem(STORAGE_KEY_API_BASE, url.trim());
  window.dispatchEvent(new CustomEvent('consultos_api_url_changed', { detail: url.trim() }));
}

export function isSimulatorForced(): boolean {
  return localStorage.getItem(STORAGE_KEY_USE_SIMULATOR) === 'true';
}

export function setSimulatorForced(val: boolean): void {
  localStorage.setItem(STORAGE_KEY_USE_SIMULATOR, val ? 'true' : 'false');
  window.dispatchEvent(new CustomEvent('consultos_simulator_changed', { detail: val }));
}

class ApiClient {
  private activeControllers: Set<AbortController> = new Set();
  private connectionListeners: Set<(state: ConnectionState) => void> = new Set();
  private currentState: ConnectionState = 'connected';

  public subscribeConnection(callback: (state: ConnectionState) => void): () => void {
    this.connectionListeners.add(callback);
    callback(this.currentState);
    return () => {
      this.connectionListeners.delete(callback);
    };
  }

  public setConnectionState(newState: ConnectionState) {
    if (this.currentState !== newState) {
      this.currentState = newState;
      this.connectionListeners.forEach((cb) => cb(newState));
    }
  }

  public getConnectionState(): ConnectionState {
    return this.currentState;
  }

  public async checkHealth(): Promise<{ ok: boolean; data?: any; error?: string }> {
    const baseUrl = getStoredApiBaseUrl();
    try {
      const res = await this.request<{ status: string }>(`${baseUrl}/api/health`, {
        method: 'GET',
        timeoutMs: 4000,
      });
      this.setConnectionState('connected');
      return { ok: true, data: res };
    } catch (err: any) {
      this.setConnectionState('offline');
      return { ok: false, error: err.message || 'FastAPI backend unreachable' };
    }
  }

  public async request<T>(
    endpoint: string,
    options: RequestInit & { timeoutMs?: number; signal?: AbortSignal } = {}
  ): Promise<T> {
    const { timeoutMs = 20000, ...fetchOptions } = options;

    const controller = new AbortController();
    this.activeControllers.add(controller);

    // Chain external signal if provided
    if (options.signal) {
      options.signal.addEventListener('abort', () => controller.abort());
    }

    const timer = setTimeout(() => {
      controller.abort();
    }, timeoutMs);

    const baseUrl = getStoredApiBaseUrl();
    const url = endpoint.startsWith('http://') || endpoint.startsWith('https://')
      ? endpoint
      : `${baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
      });

      clearTimeout(timer);
      this.activeControllers.delete(controller);

      if (!response.ok) {
        let errorDetails: any = null;
        try {
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            errorDetails = await response.json();
          } else {
            errorDetails = await response.text();
          }
        } catch {
          errorDetails = null;
        }

        const normalizedError: ApiError = {
          message:
            (typeof errorDetails === 'object' && (errorDetails?.detail || errorDetails?.message)) ||
            (typeof errorDetails === 'string' && errorDetails) ||
            `Request failed with status ${response.status}`,
          status: response.status,
          details: errorDetails,
        };
        throw normalizedError;
      }

      this.setConnectionState('connected');

      // 204 No Content
      if (response.status === 204) {
        return null as unknown as T;
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return (await response.json()) as T;
      }

      return (await response.text()) as unknown as T;
    } catch (err: any) {
      clearTimeout(timer);
      this.activeControllers.delete(controller);

      if (err.name === 'AbortError') {
        const timeoutError: ApiError = {
          message: `Request timed out after ${timeoutMs}ms or was cancelled.`,
          code: 'TIMEOUT_OR_ABORT',
        };
        throw timeoutError;
      }

      // If network failure / connection refused
      if (err instanceof TypeError && err.message.includes('fetch')) {
        this.setConnectionState('offline');
        const offlineError: ApiError = {
          message: `Cannot connect to FastAPI backend at ${baseUrl}. Ensure backend server is running and CORS is configured.`,
          code: 'BACKEND_OFFLINE',
          details: err.message,
        };
        throw offlineError;
      }

      // Normalized error or rethrow
      if (err.message && (err.status !== undefined || err.code !== undefined)) {
        throw err;
      }

      const genericError: ApiError = {
        message: err.message || 'An unexpected error occurred during API communication',
        details: err,
      };
      throw genericError;
    }
  }

  public cancelAllPendingRequests() {
    this.activeControllers.forEach((c) => c.abort());
    this.activeControllers.clear();
  }
}

export const apiClient = new ApiClient();
