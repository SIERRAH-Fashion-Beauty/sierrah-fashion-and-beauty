import type { Appearance, BudgetId, ComfortLevel, ConcreteOccasion, Occasion, PreferenceId, StyleId, WardrobeCategory } from '../types';

export const CATEGORIES: { id: WardrobeCategory; label: string }[] = [
  { id: 'tops', label: 'Tops' },
  { id: 'bottoms', label: 'Bottoms' },
  { id: 'dresses', label: 'Dresses' },
  { id: 'kurtis', label: 'Kurtis' },
  { id: 'sarees', label: 'Sarees' },
  { id: 'footwear', label: 'Footwear' },
  { id: 'bags', label: 'Bags' },
  { id: 'jewellery', label: 'Jewellery' },
  { id: 'makeup', label: 'Makeup' },
  { id: 'skincare', label: 'Skincare' },
];

export const COMFORT_LEVELS: { id: ComfortLevel; label: string }[] = [
  { id: 'low', label: 'Style first' },
  { id: 'medium', label: 'Balanced' },
  { id: 'high', label: 'Comfort first' },
];

export const COMFORT_RATINGS: { value: number; label: string }[] = [
  { value: 1, label: '1 · Stiff' },
  { value: 2, label: '2 · Dressy' },
  { value: 3, label: '3 · Balanced' },
  { value: 4, label: '4 · Comfortable' },
  { value: 5, label: '5 · Very comfortable' },
];

/** Optional model-appearance choices. Only these fixed values ever reach the image prompt. */
export const APPEARANCE_OPTIONS: { key: keyof Appearance; label: string; values: string[] }[] = [
  { key: 'skinTone', label: 'Skin tone', values: ['fair', 'wheatish', 'medium', 'olive', 'tan', 'deep'] },
  { key: 'hairLength', label: 'Hair length', values: ['short', 'medium', 'long'] },
  { key: 'hairTexture', label: 'Hair texture', values: ['straight', 'wavy', 'curly'] },
  { key: 'build', label: 'Body build', values: ['slim', 'athletic', 'average', 'curvy', 'plus-size'] },
];

/** Concrete occasions a wardrobe item can be tagged for. */
export const ITEM_OCCASIONS: { id: ConcreteOccasion; label: string }[] = [
  { id: 'college', label: 'College' },
  { id: 'casual', label: 'Casual' },
  { id: 'office', label: 'Office' },
  { id: 'wedding', label: 'Wedding' },
  { id: 'party', label: 'Party' },
  { id: 'travel', label: 'Travel' },
  { id: 'festival', label: 'Festival' },
];

/** Curated editorial photos. They are illustrations, never presented as AI-generated. */
export const SAMPLE_MODEL_PHOTO: Record<string, string> = {
  college: '/images/models/college.jpg',
  casual: '/images/models/casual.jpg',
  office: '/images/models/office.jpg',
  wedding: '/images/models/wedding.jpg',
  party: '/images/models/party.jpg',
  travel: '/images/models/travel.jpg',
  festival: '/images/models/festival.jpg',
};

export const OCCASIONS: Occasion[] = [
  { id: 'college', label: 'College', image: '/images/models/college.jpg', blurb: 'Comfortable and put-together for campus days.' },
  { id: 'casual', label: 'Casual', image: '/images/models/casual.jpg', blurb: 'Easy, effortless looks for everyday outings.' },
  { id: 'office', label: 'Office', image: '/images/models/office.jpg', blurb: 'Polished and professional, never stiff.' },
  { id: 'wedding', label: 'Wedding', image: '/images/models/wedding.jpg', blurb: 'Rich textures and heirloom sparkle.' },
  { id: 'party', label: 'Party', image: '/images/models/party.jpg', blurb: 'Evening glamour with a confident edge.' },
  { id: 'travel', label: 'Travel', image: '/images/models/travel.jpg', blurb: 'Breathable, practical and photogenic.' },
  { id: 'festival', label: 'Festival', image: '/images/models/festival.jpg', blurb: 'Colour, gold and celebration.' },
  { id: 'custom', label: 'Custom Occasion', blurb: 'Describe your event and we will style it.' },
];

export const STYLES: { id: StyleId; label: string }[] = [
  { id: 'casual', label: 'Casual' },
  { id: 'traditional', label: 'Traditional' },
  { id: 'western', label: 'Western' },
  { id: 'elegant', label: 'Elegant' },
  { id: 'trendy', label: 'Trendy' },
];

export const COLOR_OPTIONS: { name: string; hex: string }[] = [
  { name: 'Pink', hex: '#E58E9B' },
  { name: 'Purple', hex: '#A78BCB' },
  { name: 'Blue', hex: '#7A96D8' },
  { name: 'Green', hex: '#4F8A62' },
  { name: 'Beige', hex: '#E0C9A8' },
  { name: 'Brown', hex: '#7A4333' },
  { name: 'Black', hex: '#2B2B2B' },
  { name: 'White', hex: '#FFFFFF' },
  { name: 'Red', hex: '#C0443F' },
  { name: 'Yellow', hex: '#E8C25B' },
];

export const BUDGETS: { id: BudgetId; label: string; max: number }[] = [
  { id: 'under-500', label: 'Under ₹500', max: 500 },
  { id: '500-1500', label: '₹500 – ₹1,500', max: 1500 },
  { id: '1500-3000', label: '₹1,500 – ₹3,000', max: 3000 },
  { id: '3000-plus', label: '₹3,000+', max: Number.POSITIVE_INFINITY },
];

export const PREFERENCES: { id: PreferenceId; label: string }[] = [
  { id: 'comfortable', label: 'Comfortable' },
  { id: 'minimal', label: 'Minimal' },
  { id: 'trendy', label: 'Trendy' },
  { id: 'simple', label: 'Simple' },
];

export const budgetLabel = (id: BudgetId): string => BUDGETS.find((b) => b.id === id)?.label ?? id;
export const occasionLabel = (id: string, custom?: string): string =>
  id === 'custom' && custom?.trim() ? custom.trim() : OCCASIONS.find((o) => o.id === id)?.label ?? id;
export const styleLabel = (id: string | null): string => STYLES.find((s) => s.id === id)?.label ?? '';
export const categoryLabel = (id: WardrobeCategory): string => CATEGORIES.find((c) => c.id === id)?.label ?? id;
