export type WardrobeCategory =
  | 'tops'
  | 'bottoms'
  | 'dresses'
  | 'footwear'
  | 'bags'
  | 'jewellery'
  | 'beauty';

export type OccasionId =
  | 'college'
  | 'casual'
  | 'office'
  | 'wedding'
  | 'party'
  | 'travel'
  | 'festival'
  | 'custom';

export type StyleId = 'casual' | 'traditional' | 'western' | 'elegant' | 'trendy';

export type BudgetId = 'under-500' | '500-1500' | '1500-3000' | '3000-plus';

export type PreferenceId = 'comfortable' | 'minimal' | 'trendy' | 'simple';

export interface WardrobeItem {
  id: string;
  name: string;
  category: WardrobeCategory;
  color: string;
  /** Free-form tags such as "casual", "party" or "cotton". */
  tags: string[];
  brand?: string;
  notes?: string;
  /** Public path ("/images/...") or an uploaded data URL. */
  image: string;
  createdAt: string;
}

export type LookSlot = 'outfit' | 'footwear' | 'bag' | 'jewellery' | 'makeup' | 'hairstyle';

/** wardrobe = you own it, suggested = optional purchase, tip = styling advice only. */
export type LookSource = 'wardrobe' | 'suggested' | 'tip';

export interface LookItem {
  slot: LookSlot;
  title: string;
  subtitle: string;
  image: string;
  source: LookSource;
  /** Present when source === "wardrobe". */
  wardrobeItemIds?: string[];
  /** Present when source === "suggested" and a catalog product matches. */
  shopItemId?: string;
}

export interface LookPreferences {
  occasion: OccasionId;
  customOccasion?: string;
  style: StyleId | null;
  colors: string[];
  budget: BudgetId;
  traits: PreferenceId[];
  notes: string;
}

export interface Look {
  id: string;
  title: string;
  occasion: OccasionId;
  occasionLabel: string;
  modelImage: string;
  preferences: LookPreferences;
  items: LookItem[];
  tips: string[];
  isDemo?: boolean;
  generatedAt: string;
}

export interface SavedLook extends Look {
  favorite: boolean;
  savedAt: string;
}

export interface ShopItem {
  id: string;
  name: string;
  category: WardrobeCategory;
  /** Demo price in INR. Not a live price. */
  price: number;
  image: string;
  /** Wardrobe tag that, if already owned, means this item isn't "missing". */
  fills: string;
  occasions: OccasionId[];
  description: string;
}

export interface Occasion {
  id: OccasionId;
  label: string;
  image?: string;
  blurb: string;
}

export type ApiStatus = 'checking' | 'online' | 'offline';
