import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  type ReactNode,
} from 'react';
import { DEMO_WARDROBE } from '../data/demoWardrobe';
import { uid } from '../lib/id';
import { DEFAULT_PREFERENCES, buildDemoLook, buildSeedSavedLooks, generateLook } from '../lib/stylist';
import { STORAGE_KEYS, clearAll, loadJSON, saveJSON } from '../lib/storage';
import { api } from '../services/api';
import { resolveLookImage } from '../services/lookImage';
import type { ApiStatus, Look, LookPreferences, SavedLook, WardrobeItem } from '../types';

interface Toast {
  id: number;
  message: string;
  tone: 'success' | 'error' | 'info';
}

interface State {
  wardrobe: WardrobeItem[];
  saved: SavedLook[];
  preferences: LookPreferences;
  currentLook: Look | null;
  apiStatus: ApiStatus;
  booting: boolean;
  syncing: boolean;
  generating: boolean;
  toast: Toast | null;
  itemModal: { open: boolean; editing: WardrobeItem | null; initialImage?: string };
}

type Action =
  | { type: 'wardrobe/set'; items: WardrobeItem[] }
  | { type: 'saved/set'; looks: SavedLook[] }
  | { type: 'prefs/patch'; patch: Partial<LookPreferences> }
  | { type: 'look/set'; look: Look | null }
  | { type: 'api/status'; status: ApiStatus }
  | { type: 'boot/done' }
  | { type: 'sync'; value: boolean }
  | { type: 'generating'; value: boolean }
  | { type: 'toast'; toast: Toast | null }
  | { type: 'modal'; open: boolean; editing?: WardrobeItem | null; initialImage?: string }
  | { type: 'reset'; wardrobe: WardrobeItem[] };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'wardrobe/set':
      return { ...state, wardrobe: action.items };
    case 'saved/set':
      return { ...state, saved: action.looks };
    case 'prefs/patch':
      return { ...state, preferences: { ...state.preferences, ...action.patch } };
    case 'look/set':
      return { ...state, currentLook: action.look };
    case 'api/status':
      return { ...state, apiStatus: action.status };
    case 'boot/done':
      return { ...state, booting: false };
    case 'sync':
      return { ...state, syncing: action.value };
    case 'generating':
      return { ...state, generating: action.value };
    case 'toast':
      return { ...state, toast: action.toast };
    case 'modal':
      return {
        ...state,
        itemModal: { open: action.open, editing: action.editing ?? null, initialImage: action.initialImage },
      };
    case 'reset':
      return {
        ...state,
        wardrobe: action.wardrobe,
        saved: buildSeedSavedLooks(action.wardrobe),
        preferences: DEFAULT_PREFERENCES,
        currentLook: null,
      };
    default:
      return state;
  }
}

function initState(): State {
  const stored = loadJSON<WardrobeItem[] | null>(STORAGE_KEYS.wardrobe, null);
  return {
    wardrobe: stored ?? DEMO_WARDROBE,
    // `null` means "never stored", so first launch gets sample looks while a user who
    // deleted everything keeps an empty list.
    saved: loadJSON<SavedLook[] | null>(STORAGE_KEYS.saved, null) ?? buildSeedSavedLooks(stored ?? DEMO_WARDROBE),
    preferences: { ...DEFAULT_PREFERENCES, ...loadJSON<Partial<LookPreferences>>(STORAGE_KEYS.preferences, {}) },
    currentLook: loadJSON<Look | null>(STORAGE_KEYS.currentLook, null),
    apiStatus: 'checking',
    booting: true,
    syncing: false,
    generating: false,
    toast: null,
    itemModal: { open: false, editing: null },
  };
}

export type NewWardrobeItem = Omit<WardrobeItem, 'id' | 'createdAt'> & { id?: string };

interface AppContextValue extends State {
  /** The look to display: the generated one, or the lavender demo look. */
  displayLook: Look;
  addItem: (item: NewWardrobeItem) => WardrobeItem;
  updateItem: (item: WardrobeItem) => void;
  removeItem: (id: string) => void;
  saveWardrobe: () => Promise<void>;
  patchPreferences: (patch: Partial<LookPreferences>) => void;
  generate: () => Promise<Look>;
  openLook: (look: Look) => void;
  saveLook: (look: Look, opts?: { favorite?: boolean }) => SavedLook | null;
  isSaved: (lookId: string) => SavedLook | undefined;
  toggleFavorite: (lookId: string) => void;
  deleteSaved: (lookId: string) => void;
  openItemModal: (editing?: WardrobeItem | null, initialImage?: string) => void;
  closeItemModal: () => void;
  showToast: (message: string, tone?: Toast['tone']) => void;
  retryConnection: () => void;
  resetDemo: () => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, undefined, initState);
  const stateRef = useRef(state);
  stateRef.current = state;
  const toastTimer = useRef<number | undefined>(undefined);
  const offlineNotified = useRef(false);

  // ---- Persistence -------------------------------------------------------
  const quotaWarned = useRef(false);
  useEffect(() => {
    const ok =
      saveJSON(STORAGE_KEYS.wardrobe, state.wardrobe) &&
      saveJSON(STORAGE_KEYS.saved, state.saved) &&
      saveJSON(STORAGE_KEYS.preferences, state.preferences) &&
      saveJSON(STORAGE_KEYS.currentLook, state.currentLook);
    if (!ok && !quotaWarned.current) {
      quotaWarned.current = true;
      showToast('Your browser storage is full. Recent changes may not persist on this device.', 'error');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.wardrobe, state.saved, state.preferences, state.currentLook]);

  // ---- Toasts ------------------------------------------------------------
  const showToast = useCallback((message: string, tone: Toast['tone'] = 'success') => {
    window.clearTimeout(toastTimer.current);
    dispatch({ type: 'toast', toast: { id: Date.now(), message, tone } });
    toastTimer.current = window.setTimeout(() => dispatch({ type: 'toast', toast: null }), 3200);
  }, []);

  // ---- Backend sync helpers ---------------------------------------------
  // `dirty` is persisted so changes made while the server is down are pushed up on the
  // next connection instead of being overwritten by the server's older copy.
  const markDirty = useCallback((value: boolean) => {
    saveJSON(STORAGE_KEYS.dirty, value);
  }, []);

  const markOffline = useCallback(() => {
    markDirty(true);
    dispatch({ type: 'api/status', status: 'offline' });
    if (!offlineNotified.current) {
      offlineNotified.current = true;
      showToast('Server unreachable. Your changes are saved on this device.', 'info');
    }
  }, [markDirty, showToast]);

  const background = useCallback(
    (fn: () => Promise<unknown>) => {
      if (stateRef.current.apiStatus === 'offline') {
        markDirty(true);
        return;
      }
      fn()
        .then(() => dispatch({ type: 'api/status', status: 'online' }))
        .catch(markOffline);
    },
    [markDirty, markOffline],
  );

  const boot = useCallback(async () => {
    dispatch({ type: 'api/status', status: 'checking' });
    try {
      await api.health();
      const local = stateRef.current;
      if (loadJSON<boolean>(STORAGE_KEYS.dirty, false)) {
        // Local edits are newer than the server's copy: push them up.
        await api.replaceWardrobe(local.wardrobe);
        await api.replaceSavedLooks(local.saved);
        markDirty(false);
      } else {
        const [remoteWardrobe, remoteSaved] = await Promise.all([api.getWardrobe(), api.getSavedLooks()]);
        if (remoteWardrobe.length) dispatch({ type: 'wardrobe/set', items: remoteWardrobe });
        else if (local.wardrobe.length) await api.replaceWardrobe(local.wardrobe);
        if (remoteSaved.length) dispatch({ type: 'saved/set', looks: remoteSaved });
        else if (local.saved.length) await api.replaceSavedLooks(local.saved);
      }
      offlineNotified.current = false;
      dispatch({ type: 'api/status', status: 'online' });
    } catch {
      dispatch({ type: 'api/status', status: 'offline' });
    } finally {
      dispatch({ type: 'boot/done' });
    }
  }, [markDirty]);

  useEffect(() => {
    void boot();
  }, [boot]);

  // ---- Wardrobe ----------------------------------------------------------
  const addItem = useCallback<AppContextValue['addItem']>(
    (input) => {
      const item: WardrobeItem = {
        ...input,
        id: input.id ?? uid('item'),
        createdAt: new Date().toISOString(),
      };
      dispatch({ type: 'wardrobe/set', items: [item, ...stateRef.current.wardrobe] });
      background(() => api.createWardrobeItem(item));
      return item;
    },
    [background],
  );

  const updateItem = useCallback<AppContextValue['updateItem']>(
    (item) => {
      dispatch({
        type: 'wardrobe/set',
        items: stateRef.current.wardrobe.map((w) => (w.id === item.id ? item : w)),
      });
      background(() => api.updateWardrobeItem(item));
    },
    [background],
  );

  const removeItem = useCallback<AppContextValue['removeItem']>(
    (id) => {
      dispatch({ type: 'wardrobe/set', items: stateRef.current.wardrobe.filter((w) => w.id !== id) });
      background(() => api.deleteWardrobeItem(id));
    },
    [background],
  );

  const saveWardrobe = useCallback(async () => {
    dispatch({ type: 'sync', value: true });
    try {
      await api.replaceWardrobe(stateRef.current.wardrobe);
      dispatch({ type: 'api/status', status: 'online' });
      showToast('Wardrobe saved and synced.');
    } catch {
      dispatch({ type: 'api/status', status: 'offline' });
      showToast('Wardrobe saved on this device. Start the backend to sync it.', 'info');
    } finally {
      dispatch({ type: 'sync', value: false });
    }
  }, [showToast]);

  // ---- Styling -----------------------------------------------------------
  const patchPreferences = useCallback((patch: Partial<LookPreferences>) => {
    dispatch({ type: 'prefs/patch', patch });
  }, []);

  const generate = useCallback(async () => {
    dispatch({ type: 'generating', value: true });
    try {
      const { preferences, wardrobe, apiStatus } = stateRef.current;
      const look = generateLook(preferences, wardrobe);
      const [modelImage] = await Promise.all([
        apiStatus === 'offline' ? Promise.resolve(look.modelImage) : resolveLookImage(look),
        new Promise((r) => setTimeout(r, 900)),
      ]);
      const finished = { ...look, modelImage };
      dispatch({ type: 'look/set', look: finished });
      return finished;
    } finally {
      dispatch({ type: 'generating', value: false });
    }
  }, []);

  const openLook = useCallback((look: Look) => {
    dispatch({ type: 'look/set', look });
    dispatch({ type: 'prefs/patch', patch: look.preferences });
  }, []);

  // ---- Saved looks -------------------------------------------------------
  const isSaved = useCallback<AppContextValue['isSaved']>(
    (lookId) => stateRef.current.saved.find((s) => s.id === lookId),
    // `state.saved` is read via ref but the callback identity must change so consumers re-render
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [state.saved],
  );

  const saveLook = useCallback<AppContextValue['saveLook']>(
    (look, opts) => {
      const existing = stateRef.current.saved.find((s) => s.id === look.id);
      if (existing) return existing;
      const saved: SavedLook = {
        ...look,
        isDemo: undefined,
        id: look.isDemo ? uid('look') : look.id,
        favorite: opts?.favorite ?? false,
        savedAt: new Date().toISOString(),
      };
      dispatch({ type: 'saved/set', looks: [saved, ...stateRef.current.saved] });
      if (look.isDemo) dispatch({ type: 'look/set', look: { ...look, id: saved.id, isDemo: false } });
      background(() => api.createSavedLook(saved));
      return saved;
    },
    [background],
  );

  const toggleFavorite = useCallback<AppContextValue['toggleFavorite']>(
    (lookId) => {
      const current = stateRef.current.saved.find((s) => s.id === lookId);
      if (!current) return;
      const favorite = !current.favorite;
      dispatch({
        type: 'saved/set',
        looks: stateRef.current.saved.map((s) => (s.id === lookId ? { ...s, favorite } : s)),
      });
      background(() => api.setLookFavorite(lookId, favorite));
    },
    [background],
  );

  const deleteSaved = useCallback<AppContextValue['deleteSaved']>(
    (lookId) => {
      dispatch({ type: 'saved/set', looks: stateRef.current.saved.filter((s) => s.id !== lookId) });
      background(() => api.deleteSavedLook(lookId));
    },
    [background],
  );

  // ---- UI ------------------------------------------------------------------
  const openItemModal = useCallback((editing: WardrobeItem | null = null, initialImage?: string) => {
    dispatch({ type: 'modal', open: true, editing, initialImage });
  }, []);
  const closeItemModal = useCallback(() => dispatch({ type: 'modal', open: false }), []);

  const resetDemo = useCallback(() => {
    clearAll();
    const previous = stateRef.current.saved;
    dispatch({ type: 'reset', wardrobe: DEMO_WARDROBE });
    const seeds = buildSeedSavedLooks(DEMO_WARDROBE);
    background(async () => {
      await api.replaceWardrobe(DEMO_WARDROBE);
      for (const s of previous) await api.deleteSavedLook(s.id);
      for (const s of seeds) await api.createSavedLook(s);
    });
    showToast('Demo data restored.');
  }, [background, showToast]);

  const displayLook = useMemo(
    () => state.currentLook ?? buildDemoLook(state.wardrobe.length ? state.wardrobe : DEMO_WARDROBE),
    [state.currentLook, state.wardrobe],
  );

  const value = useMemo<AppContextValue>(
    () => ({
      ...state,
      displayLook,
      addItem,
      updateItem,
      removeItem,
      saveWardrobe,
      patchPreferences,
      generate,
      openLook,
      saveLook,
      isSaved,
      toggleFavorite,
      deleteSaved,
      openItemModal,
      closeItemModal,
      showToast,
      retryConnection: () => void boot(),
      resetDemo,
    }),
    [
      state,
      displayLook,
      addItem,
      updateItem,
      removeItem,
      saveWardrobe,
      patchPreferences,
      generate,
      openLook,
      saveLook,
      isSaved,
      toggleFavorite,
      deleteSaved,
      openItemModal,
      closeItemModal,
      showToast,
      boot,
      resetDemo,
    ],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useApp(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used inside <AppProvider>');
  return ctx;
}
