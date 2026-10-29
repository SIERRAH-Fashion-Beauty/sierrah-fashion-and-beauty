import type { WardrobeItem } from '../types';
import demo from './seed/demoWardrobe.json';

/**
 * Sample wardrobe shown on first launch. It is generated from the same source as the
 * backend's seed (backend/scripts/export_seed_data.py), so the app behaves identically
 * online and offline.
 */
export const DEMO_WARDROBE = demo as unknown as WardrobeItem[];
