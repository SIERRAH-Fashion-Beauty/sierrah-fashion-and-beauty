const PREFIX = 'sierrah:';

export const STORAGE_KEYS = {
  wardrobe: 'wardrobe',
  saved: 'saved-looks',
  preferences: 'preferences',
  currentLook: 'current-look',
  /** True when local changes have not reached the backend yet. */
  dirty: 'dirty-sync',
} as const;

export function loadJSON<T>(key: string, fallback: T): T {
  try {
    const raw = window.localStorage.getItem(PREFIX + key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

/** Returns false when the browser refuses (quota, private mode). */
export function saveJSON(key: string, value: unknown): boolean {
  try {
    window.localStorage.setItem(PREFIX + key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

export function clearAll(): void {
  try {
    Object.keys(window.localStorage)
      .filter((k) => k.startsWith(PREFIX))
      .forEach((k) => window.localStorage.removeItem(k));
  } catch {
    /* ignore */
  }
}
