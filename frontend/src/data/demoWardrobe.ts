import type { WardrobeItem } from '../types';

const created = '2026-10-29T10:00:00.000Z';

/**
 * Sample wardrobe shown on first launch. Stable IDs let the backend seed the
 * exact same items, so the app behaves identically online and offline.
 */
export const DEMO_WARDROBE: WardrobeItem[] = [
  { id: 'demo-floral-dress', name: 'Floral Dress', category: 'dresses', color: 'Blue', tags: ['casual', 'party', 'travel', 'western', 'elegant'], image: '/images/items/floral-dress.jpg', createdAt: created },
  { id: 'demo-blue-kurti', name: 'Blue Kurti', category: 'tops', color: 'Blue', tags: ['college', 'office', 'festival', 'traditional', 'comfortable', 'kurti'], image: '/images/items/blue-kurti.jpg', createdAt: created },
  { id: 'demo-white-top', name: 'White Top', category: 'tops', color: 'White', tags: ['college', 'casual', 'office', 'travel', 'minimal', 'simple', 'comfortable'], image: '/images/items/white-top.jpg', createdAt: created },
  { id: 'demo-jeans', name: 'Jeans', category: 'bottoms', color: 'Blue', tags: ['college', 'casual', 'travel', 'western', 'comfortable'], image: '/images/items/jeans.jpg', createdAt: created },
  { id: 'demo-black-skirt', name: 'Black Skirt', category: 'bottoms', color: 'Black', tags: ['office', 'party', 'western', 'elegant', 'minimal', 'trendy'], image: '/images/items/black-skirt.jpg', createdAt: created },
  { id: 'demo-sneakers', name: 'Sneakers', category: 'footwear', color: 'White', tags: ['college', 'casual', 'travel', 'comfortable', 'simple', 'sneakers'], image: '/images/items/sneakers.jpg', createdAt: created },
  { id: 'demo-heels', name: 'Heels', category: 'footwear', color: 'Beige', tags: ['office', 'party', 'wedding', 'elegant', 'heels'], image: '/images/items/heels.jpg', createdAt: created },
  { id: 'demo-handbag', name: 'Handbag', category: 'bags', color: 'Pink', tags: ['office', 'party', 'wedding', 'elegant', 'handbag'], image: '/images/items/handbag.jpg', createdAt: created },
  { id: 'demo-earrings', name: 'Earrings', category: 'jewellery', color: 'Gold', tags: ['college', 'office', 'party', 'wedding', 'elegant', 'minimal', 'earrings'], image: '/images/items/earrings.jpg', createdAt: created },
  { id: 'demo-watch', name: 'Watch', category: 'jewellery', color: 'Rose Gold', tags: ['college', 'office', 'casual', 'travel', 'minimal', 'watch'], image: '/images/items/watch.jpg', createdAt: created },
  { id: 'demo-lipstick', name: 'Lipstick', category: 'beauty', color: 'Red', tags: ['party', 'wedding', 'festival', 'office', 'lipstick'], image: '/images/items/lipstick.jpg', createdAt: created },
  { id: 'demo-foundation', name: 'Foundation', category: 'beauty', color: 'Beige', tags: ['party', 'wedding', 'office', 'foundation'], image: '/images/items/foundation.jpg', createdAt: created },
  { id: 'demo-compact', name: 'Compact', category: 'beauty', color: 'Pink', tags: ['college', 'casual', 'office', 'travel', 'compact', 'minimal'], image: '/images/items/compact.jpg', createdAt: created },
  { id: 'demo-perfume', name: 'Perfume', category: 'beauty', color: 'Pink', tags: ['party', 'wedding', 'festival', 'perfume'], image: '/images/items/perfume.jpg', createdAt: created },
  { id: 'demo-hair-serum', name: 'Hair Serum', category: 'beauty', color: 'Blue', tags: ['college', 'casual', 'travel', 'hair-serum'], image: '/images/items/hair-serum.jpg', createdAt: created },
  { id: 'demo-lavender-kurti', name: 'Lavender Kurti', category: 'tops', color: 'Purple', tags: ['college', 'casual', 'office', 'festival', 'traditional', 'comfortable', 'simple', 'kurti', 'lavender-kurti'], image: '/images/items/lavender-kurti.jpg', createdAt: created },
  { id: 'demo-white-trousers', name: 'White Trousers', category: 'bottoms', color: 'White', tags: ['college', 'casual', 'office', 'traditional', 'minimal', 'simple', 'comfortable'], image: '/images/items/white-trousers.jpg', createdAt: created },
  { id: 'demo-sling-bag', name: 'Beige Sling Bag', category: 'bags', color: 'Beige', tags: ['college', 'casual', 'travel', 'minimal', 'simple', 'sling-bag'], image: '/images/items/sling-bag.jpg', createdAt: created },
];
