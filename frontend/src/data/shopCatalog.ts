import type { ShopItem } from '../types';
import catalog from './seed/shopCatalog.json';

/**
 * Offline copy of the demo catalog (the API serves the same data at /api/catalog).
 * Prices are illustrative only; SIERRAH does not connect to any live retailer and no
 * purchases can be made.
 */
export const SHOP_CATALOG = catalog as unknown as ShopItem[];

export const formatInr = (n: number): string => `₹${n.toLocaleString('en-IN')}`;
