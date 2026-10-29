import { BUDGETS, OCCASIONS, occasionLabel, styleLabel } from '../data/options';
import { SHOP_CATALOG, formatInr } from '../data/shopCatalog';
import type {
  Look,
  LookItem,
  LookPreferences,
  OccasionId,
  SavedLook,
  ShopItem,
  WardrobeCategory,
  WardrobeItem,
} from '../types';
import { uid } from './id';

/**
 * SIERRAH rule-based stylist.
 *
 * Works fully offline: it scores the user's own wardrobe against the chosen
 * occasion / style / colours first, and only suggests a (demo-priced) purchase
 * when nothing owned fits the slot. The AI image-generation step is a separate
 * pluggable service (see services/lookImage.ts).
 */

type ConcreteOccasion = Exclude<OccasionId, 'custom'>;

interface OccasionProfile {
  preferDress: boolean;
  outfit: [string, string];
  footwear: [string, string];
  bag: [string, string];
  jewellery: [string, string];
  makeup: [string, string];
  hair: [string, string];
  tips: string[];
}

const PROFILES: Record<ConcreteOccasion, OccasionProfile> = {
  college: {
    preferDress: false,
    outfit: ['Kurti & Trousers', 'Easy pastel separates that survive a full day on campus'],
    footwear: ['White Sneakers', 'Cushioned and easy to walk in'],
    bag: ['Sling Bag', 'Hands-free with room for the essentials'],
    jewellery: ['Light Earrings + Watch', 'Delicate pieces that stay out of the way'],
    makeup: ['Natural Look', 'Skin tint, soft lip and a touch of mascara'],
    hair: ['Soft Waves', 'Simple, everyday look'],
    tips: [
      'Stick to two main colours and let the bag or shoes add the third.',
      'Choose breathable cotton so you stay comfortable between lectures.',
      'Finish with a tiny pair of earrings rather than a big statement piece.',
    ],
  },
  casual: {
    preferDress: false,
    outfit: ['Relaxed Separates', 'Soft tee, easy bottoms and a light layer'],
    footwear: ['Canvas Sneakers', 'Comfortable for long walks and cafe stops'],
    bag: ['Crossbody Bag', 'Compact and secure'],
    jewellery: ['Everyday Jewellery', 'A watch or tiny studs is all you need'],
    makeup: ['Fresh Face', 'Tinted moisturiser and a glossy lip'],
    hair: ['Open Hair', 'Loose waves with a little serum for shine'],
    tips: [
      'Tuck in the front of your top to define your waist.',
      'Mix one textured piece (denim, knit) with one smooth piece.',
      'A neutral bag ties together almost any casual outfit.',
    ],
  },
  office: {
    preferDress: false,
    outfit: ['Smart Separates', 'Structured pieces in calm, polished tones'],
    footwear: ['Block Heels or Loafers', 'Professional and comfortable'],
    bag: ['Structured Handbag', 'Fits a laptop sleeve or planner'],
    jewellery: ['Minimal Earrings + Watch', 'Quietly polished'],
    makeup: ['Soft Neutral', 'Matte base, subtle lip and defined brows'],
    hair: ['Sleek Low Ponytail', 'Neat and meeting-ready'],
    tips: [
      'Keep the palette tonal: cream, black, navy or soft pastels.',
      'Let one accessory be the focus, not three.',
      'Carry a spare compact for a mid-day refresh.',
    ],
  },
  wedding: {
    preferDress: true,
    outfit: ['Silk Saree or Lehenga', 'Rich fabric in jewel or blush tones'],
    footwear: ['Embellished Heels', 'Dressy but dance-floor friendly'],
    bag: ['Potli or Clutch', 'Small, ornate and secure'],
    jewellery: ['Gold Jewellery Set', 'Jhumkas and a statement necklace'],
    makeup: ['Radiant Glam', 'Luminous base, kohl-lined eyes and a rose lip'],
    hair: ['Low Bun with Flowers', 'Classic and camera-ready'],
    tips: [
      'Pick one hero piece: either heavy jewellery or a heavy outfit, not both.',
      'Break in new heels at home before the day.',
      'Pin fresh flowers last so they stay crisp.',
    ],
  },
  party: {
    preferDress: true,
    outfit: ['Evening Dress', 'A satin or sequin piece that moves with you'],
    footwear: ['Strappy Heels', 'Elegant and secure'],
    bag: ['Mini Clutch', 'Just enough room for phone and lipstick'],
    jewellery: ['Statement Earrings', 'Let them catch the light'],
    makeup: ['Defined Eyes + Bold Lip', 'Winged liner and a rich lip colour'],
    hair: ['Sleek Waves', 'Glossy, brushed-out curls'],
    tips: [
      'If the outfit is bold, keep the jewellery to one standout piece.',
      'Carry lipstick for quick touch-ups.',
      'Choose fabrics that do not cling when you dance.',
    ],
  },
  travel: {
    preferDress: false,
    outfit: ['Breathable Layers', 'Light cotton or linen that packs well'],
    footwear: ['Walking Sneakers', 'Supportive for long days on your feet'],
    bag: ['Crossbody Bag', 'Zipped and hands-free'],
    jewellery: ['Minimal Pieces', 'Watch and small studs; nothing to lose'],
    makeup: ['Sun-Safe Basics', 'SPF, tinted balm and a touch of blush'],
    hair: ['Loose Braid', 'Heat-proof and low maintenance'],
    tips: [
      'Choose pieces that mix and match so one bag of clothes covers several days.',
      'Wear the bulkiest shoes on the journey.',
      'Pack a scarf: it doubles as a layer and an accessory.',
    ],
  },
  festival: {
    preferDress: true,
    outfit: ['Festive Ethnic Wear', 'Embroidered kurti set, saree or lehenga'],
    footwear: ['Embroidered Juttis', 'Traditional and comfortable'],
    bag: ['Potli Bag', 'Small and festive'],
    jewellery: ['Statement Earrings', 'Chandbalis or jhumkas with a bindi'],
    makeup: ['Warm Glow', 'Golden shimmer and a berry lip'],
    hair: ['Braided Half-Up', 'Add a gajra or small pins'],
    tips: [
      'Echo one colour from the outfit in your lips or bangles.',
      'Contrast a rich outfit with simple makeup, or the reverse.',
      'Keep a small safety-pin kit in your bag for dupatta emergencies.',
    ],
  },
};

const KEYWORDS: { match: RegExp; occasion: ConcreteOccasion }[] = [
  { match: /wedding|shaadi|sangeet|mehendi|engagement|reception/i, occasion: 'wedding' },
  { match: /festival|diwali|puja|pooja|eid|navratri|onam|pongal|holi/i, occasion: 'festival' },
  { match: /office|work|interview|meeting|presentation|corporate/i, occasion: 'office' },
  { match: /party|club|night|birthday|date|dinner|cocktail/i, occasion: 'party' },
  { match: /travel|trip|vacation|holiday|flight|beach|hike/i, occasion: 'travel' },
  { match: /college|campus|class|school|exam|university/i, occasion: 'college' },
];

/** Maps "custom" onto the closest built-in occasion using keywords. */
export function resolveOccasion(prefs: Pick<LookPreferences, 'occasion' | 'customOccasion' | 'notes'>): ConcreteOccasion {
  if (prefs.occasion !== 'custom') return prefs.occasion;
  const text = `${prefs.customOccasion ?? ''} ${prefs.notes ?? ''}`;
  return KEYWORDS.find((k) => k.match.test(text))?.occasion ?? 'casual';
}

const norm = (s: string) => s.trim().toLowerCase();
const hasTag = (item: WardrobeItem, tag: string) => item.tags.some((t) => norm(t) === norm(tag));

function scoreItem(item: WardrobeItem, prefs: LookPreferences, occasion: ConcreteOccasion): number {
  let score = 0;
  if (hasTag(item, occasion)) score += 4;
  if (prefs.style && hasTag(item, prefs.style)) score += 2;
  for (const trait of prefs.traits) if (hasTag(item, trait)) score += 1.2;
  if (prefs.colors.some((c) => norm(c) === norm(item.color))) score += 2.5;
  const note = norm(prefs.notes ?? '');
  if (note) {
    if (note.includes(norm(item.name))) score += 2;
    if (item.tags.some((t) => note.includes(norm(t)))) score += 0.8;
  }
  return score;
}

const fitsOccasion = (item: WardrobeItem, occasion: ConcreteOccasion) => hasTag(item, occasion);

function ranked(
  wardrobe: WardrobeItem[],
  categories: WardrobeCategory[],
  prefs: LookPreferences,
  occasion: ConcreteOccasion,
  requireFit = true,
) {
  return wardrobe
    .filter((w) => categories.includes(w.category))
    .filter((w) => !requireFit || fitsOccasion(w, occasion))
    .map((item) => ({ item, score: scoreItem(item, prefs, occasion) }))
    .sort((a, b) => b.score - a.score);
}

const budgetMax = (prefs: LookPreferences) => BUDGETS.find((b) => b.id === prefs.budget)?.max ?? Infinity;
const isOwned = (wardrobe: WardrobeItem[], shop: ShopItem) => wardrobe.some((w) => hasTag(w, shop.fills));

function suggestPurchase(
  wardrobe: WardrobeItem[],
  categories: WardrobeCategory[],
  prefs: LookPreferences,
  occasion: ConcreteOccasion,
): ShopItem | undefined {
  const max = budgetMax(prefs);
  return SHOP_CATALOG.filter((s) => categories.includes(s.category))
    .filter((s) => s.price <= max && !isOwned(wardrobe, s))
    .filter((s) => s.occasions.includes(occasion))
    .map((s) => ({ s, score: (prefs.colors.some((c) => norm(s.name).includes(norm(c))) ? 2 : 0) - s.price / 10000 }))
    .sort((a, b) => b.score - a.score)[0]?.s;
}

const OUTFIT_PHOTOS: Record<string, string> = {
  'demo-lavender-kurti|demo-white-trousers': '/images/look/outfit.jpg',
};
const MODEL_PHOTOS: Record<string, string> = {
  'demo-lavender-kurti|demo-white-trousers': '/images/models/look-model.jpg',
};

function suggestedItem(
  slot: LookItem['slot'],
  shop: ShopItem | undefined,
  fallback: [string, string],
  fallbackImage: string,
): LookItem {
  if (shop) {
    return {
      slot,
      title: shop.name,
      subtitle: `Suggested purchase · demo price ${formatInr(shop.price)}`,
      image: shop.image,
      source: 'suggested',
      shopItemId: shop.id,
    };
  }
  return {
    slot,
    title: fallback[0],
    subtitle: `Suggested · ${fallback[1]}`,
    image: fallbackImage,
    source: 'suggested',
  };
}

function wardrobeItem(slot: LookItem['slot'], items: WardrobeItem[], title?: string, image?: string): LookItem {
  return {
    slot,
    title: title ?? items.map((i) => i.name).join(' + '),
    subtitle: 'From your wardrobe',
    image: image ?? items[0].image,
    source: 'wardrobe',
    wardrobeItemIds: items.map((i) => i.id),
  };
}

export function generateLook(prefs: LookPreferences, wardrobe: WardrobeItem[]): Look {
  const occasion = resolveOccasion(prefs);
  const profile = PROFILES[occasion];
  const occasionModel = OCCASIONS.find((o) => o.id === occasion)?.image ?? '/images/models/hero.jpg';
  const items: LookItem[] = [];
  let modelImage = occasionModel;

  // ---- Outfit -----------------------------------------------------------
  const tops = ranked(wardrobe, ['tops'], prefs, occasion);
  const bottoms = ranked(wardrobe, ['bottoms'], prefs, occasion);
  const dresses = ranked(wardrobe, ['dresses'], prefs, occasion);

  let bestPair: { top: WardrobeItem; bottom: WardrobeItem; score: number } | undefined;
  for (const t of tops) {
    for (const b of bottoms) {
      const kurtiWithSkirt = hasTag(t.item, 'kurti') && /skirt/i.test(b.item.name);
      const neutral = ['white', 'black', 'beige', 'blue'].includes(norm(b.item.color)) ? 0.8 : 0;
      const score = (t.score + b.score) / 2 + neutral - (kurtiWithSkirt ? 6 : 0);
      if (!bestPair || score > bestPair.score) bestPair = { top: t.item, bottom: b.item, score };
    }
  }
  const bestDress = dresses[0];
  const pairScore = bestPair && bestPair.score > 0 ? bestPair.score : -1;
  const dressScore = bestDress ? bestDress.score + (profile.preferDress ? 1.5 : -0.5) : -1;

  if (bestDress && dressScore >= pairScore && dressScore > 0) {
    items.push(wardrobeItem('outfit', [bestDress.item]));
  } else if (bestPair && pairScore > 0) {
    const key = `${bestPair.top.id}|${bestPair.bottom.id}`;
    items.push(
      wardrobeItem('outfit', [bestPair.top, bestPair.bottom], undefined, OUTFIT_PHOTOS[key] ?? bestPair.top.image),
    );
    if (MODEL_PHOTOS[key]) modelImage = MODEL_PHOTOS[key];
  } else {
    items.push(
      suggestedItem('outfit', suggestPurchase(wardrobe, ['tops', 'dresses'], prefs, occasion), profile.outfit, occasionModel),
    );
  }

  // ---- Footwear / Bag ----------------------------------------------------
  const shoe = ranked(wardrobe, ['footwear'], prefs, occasion)[0];
  items.push(
    shoe
      ? wardrobeItem('footwear', [shoe.item])
      : suggestedItem('footwear', suggestPurchase(wardrobe, ['footwear'], prefs, occasion), profile.footwear, '/images/items/sneakers.jpg'),
  );

  const bag = ranked(wardrobe, ['bags'], prefs, occasion)[0];
  items.push(
    bag
      ? wardrobeItem('bag', [bag.item])
      : suggestedItem('bag', suggestPurchase(wardrobe, ['bags'], prefs, occasion), profile.bag, '/images/items/handbag.jpg'),
  );

  // ---- Jewellery ---------------------------------------------------------
  const jewels = ranked(wardrobe, ['jewellery'], prefs, occasion).slice(0, 2);
  items.push(
    jewels.length
      ? wardrobeItem('jewellery', jewels.map((j) => j.item))
      : suggestedItem('jewellery', suggestPurchase(wardrobe, ['jewellery'], prefs, occasion), profile.jewellery, '/images/look/jewellery.jpg'),
  );

  // ---- Makeup ------------------------------------------------------------
  const makeupPool = ranked(wardrobe, ['beauty'], prefs, occasion).filter((b) =>
    ['lipstick', 'foundation', 'compact'].some((t) => hasTag(b.item, t)),
  );
  if (makeupPool.length) {
    const used = makeupPool.slice(0, 3).map((m) => m.item);
    items.push({
      slot: 'makeup',
      title: profile.makeup[0],
      subtitle: `${profile.makeup[1]} · uses your ${used.map((u) => u.name).join(', ')}`,
      image: '/images/look/makeup.jpg',
      source: 'wardrobe',
      wardrobeItemIds: used.map((u) => u.id),
    });
  } else {
    const shop = suggestPurchase(wardrobe, ['beauty'], prefs, occasion);
    const base = suggestedItem('makeup', shop, profile.makeup, '/images/look/makeup.jpg');
    items.push({ ...base, title: profile.makeup[0], image: '/images/look/makeup.jpg' });
  }

  // ---- Hairstyle ---------------------------------------------------------
  const serum = wardrobe.find((w) => hasTag(w, 'hair-serum'));
  items.push({
    slot: 'hairstyle',
    title: profile.hair[0],
    subtitle: serum ? `${profile.hair[1]} · finish with your ${serum.name}` : profile.hair[1],
    image: '/images/look/hairstyle.jpg',
    source: 'tip',
  });

  // ---- Tips --------------------------------------------------------------
  const tips = [...profile.tips];
  if (prefs.colors.length) {
    tips.push(`You picked ${prefs.colors.join(', ')}. Repeat one of them in a small accessory for a cohesive finish.`);
  }
  if (prefs.notes?.trim()) tips.push(`Noted: "${prefs.notes.trim()}". We kept this in mind when choosing pieces.`);

  const label = occasionLabel(prefs.occasion, prefs.customOccasion);
  const style = styleLabel(prefs.style);

  return {
    id: uid('look'),
    title: `${label}${style ? ` ${style}` : ''} Look`,
    occasion: prefs.occasion,
    occasionLabel: label,
    modelImage,
    preferences: prefs,
    items,
    tips,
    generatedAt: new Date().toISOString(),
  };
}

export const DEFAULT_PREFERENCES: LookPreferences = {
  occasion: 'college',
  customOccasion: '',
  style: 'casual',
  colors: [],
  budget: '500-1500',
  traits: ['comfortable'],
  notes: '',
};

/** Sample look shown before the user has generated one (lavender kurti demo). */
export function buildDemoLook(wardrobe: WardrobeItem[]): Look {
  const look = generateLook(
    { ...DEFAULT_PREFERENCES, colors: ['Purple'], traits: ['comfortable', 'simple'] },
    wardrobe,
  );
  return { ...look, id: 'demo-look', isDemo: true, title: 'College Casual Look' };
}

/** Sample saved looks so "My Saved Looks" is populated on first launch. */
export function buildSeedSavedLooks(wardrobe: WardrobeItem[]): SavedLook[] {
  const seeds: { key: string; prefs: Partial<LookPreferences>; favorite: boolean }[] = [
    { key: 'college', prefs: { occasion: 'college', style: 'casual', colors: ['Purple'], traits: ['comfortable', 'simple'] }, favorite: false },
    { key: 'office', prefs: { occasion: 'office', style: 'elegant', colors: ['Black', 'White'], traits: ['minimal'] }, favorite: true },
    { key: 'wedding', prefs: { occasion: 'wedding', style: 'traditional', colors: ['Red'], budget: '1500-3000', traits: [] }, favorite: false },
    { key: 'party', prefs: { occasion: 'party', style: 'elegant', colors: ['Black'], budget: '1500-3000', traits: ['trendy'] }, favorite: true },
  ];
  return seeds.map((s, i) => {
    const look = generateLook({ ...DEFAULT_PREFERENCES, ...s.prefs }, wardrobe);
    const savedAt = new Date(Date.UTC(2026, 9, 28 - i, 9, 0, 0)).toISOString();
    return { ...look, id: `seed-${s.key}`, generatedAt: savedAt, savedAt, favorite: s.favorite };
  });
}

/** Catalog items that the user's wardrobe doesn't already cover. */
export function findMissingItems(wardrobe: WardrobeItem[]): ShopItem[] {
  return SHOP_CATALOG.filter((s) => !isOwned(wardrobe, s));
}

export function suggestedTotal(look: Look): number {
  return look.items.reduce((sum, i) => {
    if (i.source !== 'suggested' || !i.shopItemId) return sum;
    return sum + (SHOP_CATALOG.find((s) => s.id === i.shopItemId)?.price ?? 0);
  }, 0);
}
