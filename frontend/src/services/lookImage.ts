import type { Look } from '../types';
import { api } from './api';

/**
 * Image-generation seam for the next development phase.
 *
 * Today every look uses a curated editorial photograph (`look.modelImage`).
 * When a provider is configured on the backend (see backend/app/services/
 * image_generation.py), `/api/look-image` returns a generated image URL and
 * this function will transparently start using it, with no UI changes.
 */
export async function resolveLookImage(look: Look): Promise<string> {
  try {
    const res = await api.requestLookImage(look);
    if (res.status === 'ready' && res.imageUrl) return res.imageUrl;
  } catch {
    /* backend offline or not configured: keep the curated photo */
  }
  return look.modelImage;
}
