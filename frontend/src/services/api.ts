import type {
  Appearance,
  GeneratedImage,
  ImageStatus,
  Look,
  LookPreferences,
  SavedLook,
  ShopItem,
  WardrobeItem,
} from '../types';

/**
 * Base URL of the FastAPI backend. Configure with VITE_API_BASE_URL in
 * frontend/.env (see .env.example). Defaults to the local dev server.
 */
export const API_BASE_URL: string = (
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://127.0.0.1:8000'
).replace(/\/+$/, '');

export class ApiError extends Error {
  status?: number;
  /** Machine-readable code for image errors, e.g. "provider_rate_limited". */
  code?: string;
  retryable: boolean;
  /** True when the server could not be reached at all (as opposed to answering with an error). */
  unreachable: boolean;
  constructor(message: string, opts: { status?: number; code?: string; retryable?: boolean; unreachable?: boolean } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = opts.status;
    this.code = opts.code;
    this.retryable = opts.retryable ?? false;
    this.unreachable = opts.unreachable ?? false;
  }
}

/** Turn FastAPI's three `detail` shapes (string, validation list, error object) into text. */
function describeDetail(detail: unknown, status: number): { message: string; code?: string; retryable?: boolean } {
  if (typeof detail === 'string') return { message: detail };
  if (Array.isArray(detail)) {
    const first = detail[0] as { loc?: unknown[]; msg?: string } | undefined;
    const field = first?.loc?.filter((p) => typeof p === 'string' && p !== 'body').join(' → ');
    return { message: first?.msg ? `Some details are invalid${field ? ` (${field})` : ''}: ${first.msg}.` : 'Some details are invalid.' };
  }
  if (detail && typeof detail === 'object') {
    const d = detail as { message?: string; code?: string; retryable?: boolean };
    if (d.message) return { message: d.message, code: d.code, retryable: d.retryable };
  }
  return { message: status >= 500 ? 'The server had a problem. Please try again.' : `Request failed (${status}).` };
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
      let info: { message: string; code?: string; retryable?: boolean } = describeDetail(undefined, res.status);
      try {
        const body = (await res.json()) as { detail?: unknown };
        info = describeDetail(body.detail, res.status);
      } catch {
        /* non-JSON error body */
      }
      throw new ApiError(info.message, { status: res.status, code: info.code, retryable: info.retryable });
    }
    if (res.status === 204) return undefined as T;
    return (await res.json()) as T;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError('The server took too long to respond.', { retryable: true });
    }
    throw new ApiError('Cannot reach the SIERRAH server. Make sure the backend is running.', {
      unreachable: true,
      retryable: true,
    });
  } finally {
    clearTimeout(timer);
  }
}

/** Generated images are served by the API (`/media/...`); bundled sample photos are relative to the site. */
export const resolveImageUrl = (url: string): string => (url.startsWith('/media/') ? `${API_BASE_URL}${url}` : url);

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  imageGeneration: ImageStatus;
}

export interface RecommendationRequest extends LookPreferences {
  wardrobe: WardrobeItem[];
  maxOutfits?: number;
  appearance?: Appearance | null;
}

export interface RecommendationResponse {
  requestId: string;
  occasion: string;
  occasionLabel: string;
  resolvedOccasion: string;
  wardrobeSource: 'request' | 'database';
  wardrobeSize: number;
  outfits: Look[];
  limitations: string[];
  engineVersion: string;
  generatedAt: string;
}

export interface GenerateImageResponse {
  status: 'ready' | 'not_configured';
  outfitId: string;
  image: GeneratedImage | null;
  cached: boolean;
  message: string;
  disclaimer: string;
}

export interface GenerateImageOptions {
  regenerate?: boolean;
  appearance?: Appearance | null;
  useReferenceImages?: boolean;
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
    request<SavedLook>('/api/saved-looks', { method: 'POST', body: JSON.stringify(look) }, 15000),
  setLookFavorite: (id: string, favorite: boolean) =>
    request<SavedLook>(`/api/saved-looks/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify({ favorite }),
    }),
  deleteSavedLook: (id: string) =>
    request<void>(`/api/saved-looks/${encodeURIComponent(id)}`, { method: 'DELETE' }),

  /** The Python occasion engine: ranks outfits from the wardrobe sent with the request. */
  recommend: (body: RecommendationRequest) =>
    request<RecommendationResponse>('/api/recommendations', { method: 'POST', body: JSON.stringify(body) }, 30000),

  getCatalog: () => request<ShopItem[]>('/api/catalog'),

  /** Asks the backend to create the AI model preview. Can take up to a minute or two. */
  generateImage: (outfitId: string, options: GenerateImageOptions = {}) =>
    request<GenerateImageResponse>(
      `/api/outfits/${encodeURIComponent(outfitId)}/generate-image`,
      { method: 'POST', body: JSON.stringify(options) },
      330000,
    ),
};
