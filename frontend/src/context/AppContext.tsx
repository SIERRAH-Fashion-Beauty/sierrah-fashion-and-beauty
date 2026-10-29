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
import {
  DEFAULT_PREFERENCES,
  DEMO_LOOK,
  SAMPLE_LOOKS,
  dehydrateImages,
  hydrateImages,
  isModernLook,
  normalizeWardrobe,
  requestWardrobe,
} from '../lib/looks';
import { STORAGE_KEYS, clearAll, loadJSON, saveJSON } from '../lib/storage';
import { ApiError, api } from '../services/api';
import type {
  ApiStatus,
  Appearance,
  GeneratedImage,
  ImageJob,
  ImageStatus,
  Look,
  LookPreferences,
  LookSession,
  SavedLook,
  WardrobeItem,
} from '../types';

interface Toast {
  id: number;
  message: string;
  tone: 'success' | 'error' | 'info';
}

export interface ModelOptions {
  appearance: Appearance;
  /** Opt in to sending photos of the owned garments as a loose visual guide. */
  useReferenceImages: boolean;
}

const DEFAULT_MODEL_OPTIONS: ModelOptions = { appearance: {}, useReferenceImages: false };

interface State {
  wardrobe: WardrobeItem[];
  saved: SavedLook[];
  preferences: LookPreferences;
  modelOptions: ModelOptions;
  session: LookSession | null;
  apiStatus: ApiStatus;
  imageStatus: ImageStatus | null;
  imageJobs: Record<string, ImageJob>;
  booting: boolean;
  syncing: boolean;
  generating: boolean;
  generateError: string | null;
  toast: Toast | null;
  itemModal: { open: boolean; editing: WardrobeItem | null; initialImage?: string };
}

type Action =
  | { type: 'wardrobe/set'; items: WardrobeItem[] }
  | { type: 'saved/set'; looks: SavedLook[] }
  | { type: 'prefs/patch'; patch: Partial<LookPreferences> }
  | { type: 'model/patch'; patch: Partial<ModelOptions> }
  | { type: 'session/set'; session: LookSession | null }
  | { type: 'session/active'; id: string }
  | { type: 'api/status'; status: ApiStatus }
  | { type: 'image/status'; status: ImageStatus | null }
  | { type: 'image/job'; id: string; job: ImageJob | null }
  | { type: 'look/image'; id: string; image: GeneratedImage }
  | { type: 'boot/done' }
  | { type: 'sync'; value: boolean }
  | { type: 'generating'; value: boolean; error?: string | null }
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
    case 'model/patch':
      return { ...state, modelOptions: { ...state.modelOptions, ...action.patch } };
    case 'session/set':
      return { ...state, session: action.session };
    case 'session/active':
      return state.session ? { ...state, session: { ...state.session, activeId: action.id } } : state;
    case 'api/status':
      return { ...state, apiStatus: action.status };
    case 'image/status':
      return { ...state, imageStatus: action.status };
    case 'image/job': {
      const jobs = { ...state.imageJobs };
      if (action.job) jobs[action.id] = action.job;
      else delete jobs[action.id];
      return { ...state, imageJobs: jobs };
    }
    case 'look/image': {
      const patch = <T extends Look>(l: T): T => (l.id === action.id ? { ...l, image: action.image } : l);
      return {
        ...state,
        session: state.session ? { ...state.session, looks: state.session.looks.map(patch) } : null,
        saved: state.saved.map(patch),
      };
    }
    case 'boot/done':
      return { ...state, booting: false };
    case 'sync':
      return { ...state, syncing: action.value };
    case 'generating':
      return { ...state, generating: action.value, generateError: action.error ?? null };
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
        saved: SAMPLE_LOOKS,
        preferences: DEFAULT_PREFERENCES,
        modelOptions: DEFAULT_MODEL_OPTIONS,
        session: null,
        imageJobs: {},
      };
    default:
      return state;
  }
}

function initState(): State {
  const storedWardrobe = normalizeWardrobe(loadJSON<unknown>(STORAGE_KEYS.wardrobe, null));
  const wardrobe = storedWardrobe ?? DEMO_WARDROBE;

  // Older builds stored looks in another shape; those cannot be reopened, so they are dropped.
  // `null` means "never stored", so first launch gets sample looks while a user who deleted
  // everything keeps an empty list.
  const storedSaved = loadJSON<unknown[] | null>(STORAGE_KEYS.saved, null);
  const modernSaved = storedSaved?.filter(isModernLook).map((l) => hydrateImages(l as SavedLook, wardrobe)) as
    | SavedLook[]
    | undefined;
  const saved = storedSaved === null || (storedSaved.length > 0 && !modernSaved?.length) ? SAMPLE_LOOKS : modernSaved ?? [];

  const storedSession = loadJSON<LookSession | null>(STORAGE_KEYS.session, null);
  const session =
    storedSession && Array.isArray(storedSession.looks) && storedSession.looks.length && storedSession.looks.every(isModernLook)
      ? { ...storedSession, looks: storedSession.looks.map((l) => hydrateImages(l, wardrobe)) }
      : null;

  return {
    wardrobe,
    saved,
    preferences: { ...DEFAULT_PREFERENCES, ...loadJSON<Partial<LookPreferences>>(STORAGE_KEYS.preferences, {}) },
    modelOptions: { ...DEFAULT_MODEL_OPTIONS, ...loadJSON<Partial<ModelOptions>>(STORAGE_KEYS.modelOptions, {}) },
    session,
    apiStatus: 'checking',
    imageStatus: null,
    imageJobs: {},
    booting: true,
    syncing: false,
    generating: false,
    generateError: null,
    toast: null,
    itemModal: { open: false, editing: null },
  };
}

export type NewWardrobeItem = Omit<WardrobeItem, 'id' | 'createdAt'> & { id?: string };

interface AppContextValue extends State {
  /** The look to display: the active recommendation, or the sample look. */
  displayLook: Look;
  /** Every outfit option from the latest request (empty before the first recommendation). */
  options: Look[];
  limitations: string[];
  addItem: (item: NewWardrobeItem) => WardrobeItem;
  updateItem: (item: WardrobeItem) => void;
  removeItem: (id: string) => void;
  saveWardrobe: () => Promise<void>;
  patchPreferences: (patch: Partial<LookPreferences>) => void;
  patchModelOptions: (patch: Partial<ModelOptions>) => void;
  generate: () => Promise<LookSession>;
  selectLook: (id: string) => void;
  generateImage: (lookId: string, opts?: { regenerate?: boolean }) => Promise<void>;
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

const hasAppearance = (a: Appearance) => Object.values(a).some(Boolean);

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
      saveJSON(STORAGE_KEYS.saved, state.saved.map(dehydrateImages)) &&
      saveJSON(STORAGE_KEYS.preferences, state.preferences) &&
      saveJSON(STORAGE_KEYS.modelOptions, state.modelOptions) &&
      saveJSON(
        STORAGE_KEYS.session,
        state.session ? { ...state.session, looks: state.session.looks.map(dehydrateImages) } : null,
      );
    if (!ok && !quotaWarned.current) {
      quotaWarned.current = true;
      showToast('Your browser storage is full. Recent changes may not persist on this device.', 'error');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.wardrobe, state.saved, state.preferences, state.modelOptions, state.session]);

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
        .catch((err) => {
          // A validation error (4xx) is not an outage; only an unreachable server is.
          if (err instanceof ApiError && !err.unreachable && err.status && err.status < 500) {
            showToast(`The server rejected a change: ${err.message}`, 'error');
            return;
          }
          markOffline();
        });
    },
    [markDirty, markOffline, showToast],
  );

  const boot = useCallback(async () => {
    dispatch({ type: 'api/status', status: 'checking' });
    try {
      const health = await api.health();
      dispatch({ type: 'image/status', status: health.imageGeneration ?? null });
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
        if (remoteSaved.length) {
          const wardrobe = remoteWardrobe.length ? remoteWardrobe : local.wardrobe;
          dispatch({ type: 'saved/set', looks: remoteSaved.map((l) => hydrateImages(l, wardrobe)) });
        } else if (local.saved.length) await api.replaceSavedLooks(local.saved);
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
      markDirty(false);
      dispatch({ type: 'api/status', status: 'online' });
      showToast('Wardrobe saved and synced.');
    } catch (err) {
      if (err instanceof ApiError && !err.unreachable) {
        showToast(`Could not save the wardrobe: ${err.message}`, 'error');
      } else {
        markDirty(true);
        dispatch({ type: 'api/status', status: 'offline' });
        showToast('Wardrobe saved on this device. Start the backend to sync it.', 'info');
      }
    } finally {
      dispatch({ type: 'sync', value: false });
    }
  }, [markDirty, showToast]);

  // ---- Styling -----------------------------------------------------------
  const patchPreferences = useCallback((patch: Partial<LookPreferences>) => {
    dispatch({ type: 'prefs/patch', patch });
  }, []);

  const patchModelOptions = useCallback((patch: Partial<ModelOptions>) => {
    dispatch({ type: 'model/patch', patch });
  }, []);

  const generateImage = useCallback<AppContextValue['generateImage']>(
    async (lookId, opts) => {
      const { modelOptions } = stateRef.current;
      dispatch({ type: 'image/job', id: lookId, job: { status: 'loading' } });
      try {
        const res = await api.generateImage(lookId, {
          regenerate: opts?.regenerate ?? false,
          appearance: hasAppearance(modelOptions.appearance) ? modelOptions.appearance : null,
          useReferenceImages: modelOptions.useReferenceImages,
        });
        if (res.status === 'not_configured' || !res.image) {
          dispatch({ type: 'image/status', status: { configured: false, provider: 'none', message: res.message } });
          dispatch({ type: 'image/job', id: lookId, job: { status: 'not_configured', message: res.message } });
          return;
        }
        dispatch({ type: 'look/image', id: lookId, image: res.image });
        dispatch({ type: 'image/job', id: lookId, job: null });
        dispatch({ type: 'api/status', status: 'online' });
      } catch (err) {
        const e = err instanceof ApiError ? err : new ApiError('Something went wrong while creating the preview.');
        if (e.unreachable) dispatch({ type: 'api/status', status: 'offline' });
        dispatch({
          type: 'image/job',
          id: lookId,
          job: { status: 'error', message: e.message, retryable: e.retryable || e.status === 404 || e.unreachable },
        });
      }
    },
    [],
  );

  const generate = useCallback(async () => {
    dispatch({ type: 'generating', value: true });
    try {
      const { preferences, wardrobe, modelOptions } = stateRef.current;
      const res = await api.recommend({
        ...preferences,
        customOccasion: preferences.customOccasion?.trim() || null,
        comfort: preferences.traits.includes('comfortable') ? 'high' : preferences.comfort,
        wardrobe: requestWardrobe(wardrobe),
        maxOutfits: 3,
        appearance: hasAppearance(modelOptions.appearance) ? modelOptions.appearance : null,
      });
      const looks = res.outfits.map((o) => hydrateImages(o, wardrobe));
      const session: LookSession = {
        requestId: res.requestId,
        looks,
        activeId: looks[0].id,
        limitations: res.limitations,
        wardrobeSize: res.wardrobeSize,
        engineVersion: res.engineVersion,
      };
      dispatch({ type: 'session/set', session });
      dispatch({ type: 'api/status', status: 'online' });
      dispatch({ type: 'generating', value: false });
      // Only the top option is created automatically (and only when a provider is set up),
      // so a single click never spends money on several images.
      if (stateRef.current.imageStatus?.configured) void generateImage(looks[0].id);
      return session;
    } catch (err) {
      const e = err instanceof ApiError ? err : new ApiError('We could not create your look. Please try again.');
      if (e.unreachable) dispatch({ type: 'api/status', status: 'offline' });
      dispatch({ type: 'generating', value: false, error: e.message });
      throw e;
    }
  }, [generateImage]);

  const selectLook = useCallback((id: string) => dispatch({ type: 'session/active', id }), []);

  const openLook = useCallback((look: Look) => {
    // Reopening a saved look shows exactly what was saved: no request is made.
    const hydrated = hydrateImages(look, stateRef.current.wardrobe);
    dispatch({
      type: 'session/set',
      session: {
        requestId: look.requestId,
        looks: [hydrated],
        activeId: look.id,
        limitations: [],
        wardrobeSize: stateRef.current.wardrobe.length,
        engineVersion: '',
      },
    });
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
      if (look.isDemo) {
        const session = stateRef.current.session;
        const copy = { ...look, id: saved.id, isDemo: false };
        dispatch({
          type: 'session/set',
          session: {
            requestId: look.requestId,
            looks: [copy],
            activeId: copy.id,
            limitations: session?.limitations ?? [],
            wardrobeSize: stateRef.current.wardrobe.length,
            engineVersion: session?.engineVersion ?? '',
          },
        });
      }
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
    dispatch({ type: 'reset', wardrobe: DEMO_WARDROBE });
    background(async () => {
      await api.replaceWardrobe(DEMO_WARDROBE);
      await api.replaceSavedLooks(SAMPLE_LOOKS);
    });
    showToast('Demo data restored.');
  }, [background, showToast]);

  const options = useMemo(() => state.session?.looks ?? [], [state.session]);
  const displayLook = useMemo(() => {
    const active = state.session?.looks.find((l) => l.id === state.session?.activeId);
    return active ?? state.session?.looks[0] ?? DEMO_LOOK;
  }, [state.session]);
  const limitations = state.session?.limitations ?? [];

  const value = useMemo<AppContextValue>(
    () => ({
      ...state,
      displayLook,
      options,
      limitations,
      addItem,
      updateItem,
      removeItem,
      saveWardrobe,
      patchPreferences,
      patchModelOptions,
      generate,
      selectLook,
      generateImage,
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
      options,
      limitations,
      addItem,
      updateItem,
      removeItem,
      saveWardrobe,
      patchPreferences,
      patchModelOptions,
      generate,
      selectLook,
      generateImage,
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
