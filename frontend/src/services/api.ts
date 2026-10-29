import type { Look, SavedLook, WardrobeItem } from '../types';

/**
 * Base URL of the FastAPI backend. Configure with VITE_API_BASE_URL in
 * frontend/.env (see .env.example). Defaults to the local dev server.
 */
export const API_BASE_URL: string = (
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://127.0.0.1:8000'
).replace(/\/+$/, '');

export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}, timeoutMs = 5000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init.headers ?? {}) },
      signal: controller.signal,
    });
    if (!res.ok) {
      let detail = `Request failed (${res.status})`;
      try {
        const body = (await res.json()) as { detail?: unknown };
        if (typeof body.detail === 'string') detail = body.detail;
      } catch {
        /* non-JSON error body */
      }
      throw new ApiError(detail, res.status);
    }
    if (res.status === 204) return undefined as T;
    return (await res.json()) as T;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError('The server took too long to respond.');
    }
    throw new ApiError('Cannot reach the SIERRAH server.');
  } finally {
    clearTimeout(timer);
  }
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export interface LookImageResponse {
  status: 'not_configured' | 'queued' | 'ready' | 'error';
  provider: string;
  imageUrl: string | null;
  message: string;
}

export const api = {
  health: () => request<HealthResponse>('/health', {}, 2500),

  getWardrobe: () => request<WardrobeItem[]>('/api/wardrobe'),
  createWardrobeItem: (item: WardrobeItem) =>
    request<WardrobeItem>('/api/wardrobe', { method: 'POST', body: JSON.stringify(item) }),
  updateWardrobeItem: (item: WardrobeItem) =>
    request<WardrobeItem>(`/api/wardrobe/${encodeURIComponent(item.id)}`, {
      method: 'PUT',
      body: JSON.stringify(item),
    }),
  deleteWardrobeItem: (id: string) =>
    request<void>(`/api/wardrobe/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  replaceWardrobe: (items: WardrobeItem[]) =>
    request<WardrobeItem[]>('/api/wardrobe/sync', { method: 'PUT', body: JSON.stringify({ items }) }, 15000),

  getSavedLooks: () => request<SavedLook[]>('/api/saved-looks'),
  replaceSavedLooks: (looks: SavedLook[]) =>
    request<SavedLook[]>('/api/saved-looks/sync', { method: 'PUT', body: JSON.stringify({ looks }) }, 15000),
  createSavedLook: (look: SavedLook) =>
    request<SavedLook>('/api/saved-looks', { method: 'POST', body: JSON.stringify(look) }),
  setLookFavorite: (id: string, favorite: boolean) =>
    request<SavedLook>(`/api/saved-looks/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify({ favorite }),
    }),
  deleteSavedLook: (id: string) =>
    request<void>(`/api/saved-looks/${encodeURIComponent(id)}`, { method: 'DELETE' }),

  /** Placeholder for the upcoming AI look-image generation phase. */
  requestLookImage: (look: Look) =>
    request<LookImageResponse>('/api/look-image', { method: 'POST', body: JSON.stringify({ look }) }, 4000),
};
