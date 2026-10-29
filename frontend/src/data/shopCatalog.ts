import type { ShopItem } from '../types';

/**
 * Demo catalog. Prices are illustrative only; SIERRAH does not connect to any
 * live retailer in this build and no purchases can be made.
 */
export const SHOP_CATALOG: ShopItem[] = [
  { id: 'shop-white-sneakers', name: 'White Sneakers', category: 'footwear', price: 1299, image: '/images/shop/chunky-sneakers.jpg', fills: 'sneakers', occasions: ['college', 'casual', 'travel'], description: 'Clean everyday sneakers that go with almost everything.' },
  { id: 'shop-shoulder-bag', name: 'Shoulder Bag', category: 'bags', price: 999, image: '/images/shop/shoulder-bag.jpg', fills: 'shoulder-bag', occasions: ['college', 'casual', 'office', 'party'], description: 'A tan chain-strap bag that lifts simple outfits.' },
  { id: 'shop-hair-serum', name: 'Hair Serum', category: 'beauty', price: 499, image: '/images/items/hair-serum.jpg', fills: 'hair-serum', occasions: ['college', 'casual', 'travel', 'wedding', 'festival'], description: 'Smooths frizz for soft, glossy waves.' },
  { id: 'shop-crossbody-bag', name: 'Crossbody Bag', category: 'bags', price: 1199, image: '/images/shop/crossbody-bag.jpg', fills: 'crossbody-bag', occasions: ['college', 'casual', 'travel'], description: 'Hands-free pink crossbody for busy days.' },
  { id: 'shop-sling-bag', name: 'Beige Sling Bag', category: 'bags', price: 899, image: '/images/look/bag.jpg', fills: 'sling-bag', occasions: ['college', 'casual', 'travel'], description: 'Neutral sling that pairs with pastel kurtis.' },
  { id: 'shop-statement-earrings', name: 'Statement Earrings', category: 'jewellery', price: 799, image: '/images/shop/statement-earrings.jpg', fills: 'statement-earrings', occasions: ['wedding', 'festival', 'party'], description: 'Kundan-style chandbalis for festive outfits.' },
  { id: 'shop-pearl-drops', name: 'Pearl Drop Earrings', category: 'jewellery', price: 599, image: '/images/look/jewellery.jpg', fills: 'pearl-drops', occasions: ['college', 'office', 'casual', 'party'], description: 'Light pearl drops for a soft, polished finish.' },
  { id: 'shop-pink-kurti', name: 'Pink Kurti', category: 'tops', price: 1499, image: '/images/shop/pink-kurti.jpg', fills: 'pink-kurti', occasions: ['college', 'office', 'festival'], description: 'Embroidered cotton kurti in a dusty rose shade.' },
  { id: 'shop-grey-top', name: 'Grey Shirt Top', category: 'tops', price: 899, image: '/images/shop/grey-top.jpg', fills: 'grey-top', occasions: ['office', 'college', 'casual'], description: 'A twist-front top that dresses up jeans or skirts.' },
  { id: 'shop-nude-makeup', name: 'Nude Makeup Set', category: 'beauty', price: 1299, image: '/images/look/makeup.jpg', fills: 'nude-makeup', occasions: ['college', 'casual', 'office', 'travel'], description: 'Lip balm, blush duo and mascara for a fresh face.' },
];

export const getShopItem = (id: string): ShopItem | undefined => SHOP_CATALOG.find((s) => s.id === id);

export const formatInr = (n: number): string => `₹${n.toLocaleString('en-IN')}`;
