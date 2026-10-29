import { ITEM_OCCASIONS, SAMPLE_MODEL_PHOTO, STYLES } from '../data/options';
import demoLookJson from '../data/seed/demoLook.json';
import sampleLooksJson from '../data/seed/sampleLooks.json';
import type {
  ConcreteOccasion,
  Look,
  LookItem,
  LookPreferences,
  OutfitPiece,
  SavedLook,
  ShopItem,
  StyleId,
  WardrobeCategory,
  WardrobeItem,
} from '../types';

export const DEFAULT_PREFERENCES: LookPreferences = {
  occasion: 'college',
  customOccasion: '',
  style: 'casual',
  colors: [],
  budget: '500-1500',
  comfort: 'medium',
  traits: ['comfortable'],
  notes: '',
};

/**
 * Sample look shown before the user has asked for one. It was produced by the real Python
 * engine from the demo wardrobe (backend/scripts/export_seed_data.py) and is always
 * labelled as a sample in the UI.
 */
export const DEMO_LOOK: Look = { ...(demoLookJson as unknown as Look), isDemo: true };

/** Sample saved looks for first launch (also produced by the real engine). */
export const SAMPLE_LOOKS: SavedLook[] = sampleLooksJson as unknown as SavedLook[];

const DEMO_PHOTO = '/images/models/look-model.jpg';

/** Curated editorial photo for a look. It is NOT AI-generated and must be labelled as a sample. */
export function samplePhotoFor(look: Pick<Look, 'id' | 'resolvedOccasion'>): string {
  if (look.id === 'demo-look') return DEMO_PHOTO;
  return SAMPLE_MODEL_PHOTO[look.resolvedOccasion] ?? '/images/models/hero.jpg';
}

/** A look in the current shape (older builds stored a different structure). */
export function isModernLook(value: unknown): value is Look {
  const l = value as Partial<Look> | null;
  return (
    !!l &&
    typeof l.id === 'string' &&
    Array.isArray(l.items) &&
    Array.isArray(l.stylingTips) &&
    Array.isArray(l.missingItems) &&
    typeof l.score === 'number' &&
    typeof l.resolvedOccasion === 'string' &&
    l.items.every((i: LookItem) => Array.isArray(i.pieces))
  );
}

// ---- Wardrobe normalisation ---------------------------------------------------------

const OCCASION_IDS = new Set<string>(ITEM_OCCASIONS.map((o) => o.id));
const STYLE_IDS = new Set<string>(STYLES.map((s) => s.id));
const CATEGORIES = new Set<string>([
  'tops', 'bottoms', 'dresses', 'kurtis', 'sarees', 'footwear', 'bags', 'jewellery', 'makeup', 'skincare',
]);

/** Upgrade an item saved by an older build (single `color`, `beauty` category, mixed tags). */
export function normalizeWardrobeItem(raw: unknown): WardrobeItem | null {
  const r = raw as Record<string, unknown> | null;
  if (!r || typeof r.id !== 'string' || typeof r.name !== 'string') return null;
  const tags = Array.isArray(r.tags) ? (r.tags as string[]).map(String) : [];
  const lowerTags = tags.map((t) => t.toLowerCase());
  const text = `${r.name} ${lowerTags.join(' ')}`.toLowerCase();
  let category = String(r.category ?? 'tops');
  if (category === 'beauty') {
    category = /serum|cream|moistur|sunscreen|cleanser|skincare|hair/.test(text) ? 'skincare' : 'makeup';
  }
  if (category === 'tops' && lowerTags.includes('kurti')) category = 'kurtis';
  if (!CATEGORIES.has(category)) category = 'tops';
  const colors = Array.isArray(r.colors) ? (r.colors as string[]) : r.color ? [String(r.color)] : [];
  const modern = Array.isArray(r.occasions) && Array.isArray(r.styles);
  return {
    id: r.id,
    name: r.name,
    category: category as WardrobeCategory,
    subcategory: typeof r.subcategory === 'string' ? r.subcategory : lowerTags.find((t) => !OCCASION_IDS.has(t) && !STYLE_IDS.has(t)) ?? '',
    colors,
    styles: modern ? (r.styles as StyleId[]) : (lowerTags.filter((t) => STYLE_IDS.has(t)) as StyleId[]),
    occasions: modern ? (r.occasions as ConcreteOccasion[]) : (lowerTags.filter((t) => OCCASION_IDS.has(t)) as ConcreteOccasion[]),
    fabric: typeof r.fabric === 'string' ? r.fabric : '',
    comfort: typeof r.comfort === 'number' ? Math.min(5, Math.max(1, Math.round(r.comfort))) : 3,
    price: typeof r.price === 'number' ? r.price : null,
    brand: (r.brand as string | undefined) ?? null,
    notes: (r.notes as string | undefined) ?? null,
    tags: modern ? tags : tags.filter((t) => !OCCASION_IDS.has(t.toLowerCase()) && !STYLE_IDS.has(t.toLowerCase())),
    image: typeof r.image === 'string' ? r.image : '',
    createdAt: typeof r.createdAt === 'string' ? r.createdAt : new Date().toISOString(),
  };
}

export function normalizeWardrobe(raw: unknown): WardrobeItem[] | null {
  if (!Array.isArray(raw)) return null;
  return raw.map(normalizeWardrobeItem).filter((i): i is WardrobeItem => i !== null);
}

/**
 * The wardrobe sent with a recommendation request. Uploaded photos (data URLs) are left out:
 * they can be megabytes each and the engine never reads them. They are re-attached to the
 * returned look by `hydrateImages`.
 */
export const requestWardrobe = (items: WardrobeItem[]): WardrobeItem[] =>
  items.map((i) => (i.image.startsWith('data:') ? { ...i, image: '' } : i));

/** Put the user's uploaded photos back into a look (the API does not echo data URLs). */
export function hydrateImages<T extends Look>(look: T, wardrobe: WardrobeItem[]): T {
  const photo = new Map(wardrobe.map((w) => [w.id, w.image]));
  const fixPiece = (p: OutfitPiece): OutfitPiece =>
    !p.image && p.wardrobeItemId && photo.get(p.wardrobeItemId) ? { ...p, image: photo.get(p.wardrobeItemId)! } : p;
  return {
    ...look,
    items: look.items.map((item) => {
      const pieces = item.pieces.map(fixPiece);
      const image = item.image || pieces.find((p) => p.image)?.image || '';
      return { ...item, pieces, image };
    }),
    accessories: look.accessories.map(fixPiece),
  };
}

// ---- Shopping -------------------------------------------------------------------

const stem = (w: string) => (w.endsWith('s') && w.length > 3 ? w.slice(0, -1) : w);
const words = (t: string) => new Set((t.toLowerCase().match(/[a-z-]+/g) ?? []).filter((w) => w.length > 2).map(stem));
const overlap = (a: Set<string>, b: Set<string>) => [...a].some((w) => b.has(w));

/** Does the wardrobe already hold something of the same kind? (mirrors the backend's rule) */
export function ownsSimilar(wardrobe: WardrobeItem[], product: ShopItem): boolean {
  return wardrobe.some((w) => {
    if (w.category !== product.category) return false;
    const a = words(w.subcategory).size ? words(w.subcategory) : words(w.name);
    const b = words(product.subcategory).size ? words(product.subcategory) : words(product.name);
    return overlap(a, b);
  });
}

/** Products referenced by a look's missing items (suggestions and cheaper alternatives). */
export function lookProductIds(look: Look): Set<string> {
  const ids = new Set<string>();
  look.missingItems.forEach((m) => {
    if (m.suggestion) ids.add(m.suggestion.id);
    m.alternatives.forEach((a) => ids.add(a.id));
  });
  return ids;
}

/** Drop uploaded photos before persisting to localStorage; `hydrateImages` restores them on load. */
export function dehydrateImages<T extends Look>(look: T): T {
  const strip = (v: string) => (v.startsWith('data:') ? '' : v);
  const piece = (p: OutfitPiece): OutfitPiece => ({ ...p, image: strip(p.image) });
  return {
    ...look,
    items: look.items.map((i) => ({ ...i, image: strip(i.image), pieces: i.pieces.map(piece) })),
    accessories: look.accessories.map(piece),
  };
}
