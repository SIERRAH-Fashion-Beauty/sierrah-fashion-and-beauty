export type WardrobeCategory =
  | 'tops'
  | 'bottoms'
  | 'dresses'
  | 'kurtis'
  | 'sarees'
  | 'footwear'
  | 'bags'
  | 'jewellery'
  | 'makeup'
  | 'skincare';

export type ConcreteOccasion = 'college' | 'casual' | 'office' | 'wedding' | 'party' | 'travel' | 'festival';
export type OccasionId = ConcreteOccasion | 'custom';

export type StyleId = 'casual' | 'traditional' | 'western' | 'elegant' | 'trendy';

export type BudgetId = 'under-500' | '500-1500' | '1500-3000' | '3000-plus';

export type PreferenceId = 'comfortable' | 'minimal' | 'trendy' | 'simple';

export type ComfortLevel = 'low' | 'medium' | 'high';

export interface WardrobeItem {
  id: string;
  name: string;
  category: WardrobeCategory;
  subcategory: string;
  colors: string[];
  styles: StyleId[];
  /** Occasions this item is suitable for. */
  occasions: ConcreteOccasion[];
  fabric: string;
  /** 1 (stiff) to 5 (very comfortable). */
  comfort: number;
  /** Optional price paid, in INR. */
  price?: number | null;
  brand?: string | null;
  notes?: string | null;
  /** Free-form tags such as "festive" or "office-wear". */
  tags: string[];
  /** Public path ("/images/...") or an uploaded data URL. */
  image: string;
  createdAt: string;
}

export type LookSlot = 'outfit' | 'footwear' | 'bag' | 'jewellery' | 'makeup' | 'hairstyle';

/** wardrobe = you own it, shopping = suggested purchase, tip = styling advice only. */
export type LookSource = 'wardrobe' | 'shopping' | 'tip';

export interface OutfitPiece {
  category: WardrobeCategory;
  name: string;
  subcategory: string;
  colors: string[];
  fabric: string;
  image: string;
  source: 'wardrobe' | 'shopping';
  wardrobeItemId?: string | null;
  shopItemId?: string | null;
  price?: number | null;
}

export interface LookItem {
  slot: LookSlot;
  title: string;
  category: string;
  detail: string;
  image: string;
  source: LookSource;
  pieces: OutfitPiece[];
  wardrobeItemIds: string[];
  shopItemId?: string | null;
}

export interface Appearance {
  skinTone?: 'fair' | 'wheatish' | 'medium' | 'olive' | 'tan' | 'deep' | null;
  hairLength?: 'short' | 'medium' | 'long' | null;
  hairTexture?: 'straight' | 'wavy' | 'curly' | null;
  build?: 'slim' | 'athletic' | 'average' | 'curvy' | 'plus-size' | null;
}

export interface LookPreferences {
  occasion: OccasionId;
  customOccasion?: string | null;
  style: StyleId | null;
  colors: string[];
  budget: BudgetId;
  comfort: ComfortLevel;
  traits: PreferenceId[];
  notes: string;
}

export interface ScorePart {
  key: string;
  label: string;
  points: number;
  maxPoints: number;
}

export interface GeneratedImage {
  /** Server path ("/media/generated/...") of the stored AI image. */
  url: string;
  provider: string;
  model: string;
  generatedAt: string;
  kind: 'ai-generated';
  usedReferenceImages: boolean;
}

export interface ShopItem {
  id: string;
  name: string;
  category: WardrobeCategory;
  subcategory: string;
  colors: string[];
  /** Demo price in INR. Not a live price. */
  price: number;
  priceIsDemo: boolean;
  image: string;
  occasions: ConcreteOccasion[];
  styles: StyleId[];
  fabric: string;
  comfort: number;
  description: string;
  ownedSimilar?: boolean;
}

export interface MissingItem {
  slot: LookSlot;
  category: string;
  label: string;
  reason: string;
  suggestion?: ShopItem | null;
  alternatives: ShopItem[];
  withinBudget: boolean;
}

/** One recommended outfit, exactly as the Python engine returned it. */
export interface Look {
  id: string;
  requestId: string;
  rank: number;
  title: string;
  score: number;
  scoreLabel: string;
  breakdown: ScorePart[];
  whyItWorks: string[];
  occasion: OccasionId;
  occasionLabel: string;
  resolvedOccasion: ConcreteOccasion;
  preferences: LookPreferences;
  appearance?: Appearance | null;
  items: LookItem[];
  accessories: OutfitPiece[];
  stylingTips: string[];
  missingItems: MissingItem[];
  suggestedTotal: number;
  budgetMax?: number | null;
  image?: GeneratedImage | null;
  generatedAt: string;
  /** Front-end only: the built-in sample look shown before the first recommendation. */
  isDemo?: boolean;
}

export interface SavedLook extends Look {
  favorite: boolean;
  savedAt: string;
  isSample?: boolean;
}

/** The latest recommendation response (all options) kept so the user can switch between them. */
export interface LookSession {
  requestId: string;
  looks: Look[];
  activeId: string;
  limitations: string[];
  wardrobeSize: number;
  engineVersion: string;
}

export interface Occasion {
  id: OccasionId;
  label: string;
  image?: string;
  blurb: string;
}

export type ApiStatus = 'checking' | 'online' | 'offline';

export interface ImageStatus {
  configured: boolean;
  provider: string;
  model?: string | null;
  message: string;
}

export type ImageJob =
  | { status: 'loading' }
  | { status: 'error'; message: string; retryable: boolean }
  | { status: 'not_configured'; message: string };
