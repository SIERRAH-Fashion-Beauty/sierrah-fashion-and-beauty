import { useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Loader2, Plus, Search, Upload, X } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { CATEGORIES } from '../data/options';
import { fileToCompactDataUrl } from '../lib/imageFile';
import type { WardrobeCategory, WardrobeItem } from '../types';
import { EmptyState, GridSkeleton } from '../components/ui/Feedback';
import { CategoryIcon } from '../components/ui/icons';
import { ConfirmDialog } from '../components/ui/Modal';
import { ItemCard } from '../components/wardrobe/ItemCard';

const isCategory = (v: string | null): v is WardrobeCategory => !!v && CATEGORIES.some((c) => c.id === v);

export function WardrobePage() {
  const { wardrobe, booting, openItemModal, removeItem, saveWardrobe, syncing, showToast, resetDemo } = useApp();
  const [params, setParams] = useSearchParams();
  const param = params.get('category');
  const category = isCategory(param) ? param : null;
  const [query, setQuery] = useState('');
  const [toRemove, setToRemove] = useState<WardrobeItem | null>(null);
  const [reading, setReading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const setCategory = (c: WardrobeCategory | null) => {
    const next = new URLSearchParams(params);
    if (c) next.set('category', c);
    else next.delete('category');
    setParams(next, { replace: true });
  };

  const counts = useMemo(() => {
    const map = new Map<WardrobeCategory, number>();
    wardrobe.forEach((w) => map.set(w.category, (map.get(w.category) ?? 0) + 1));
    return map;
  }, [wardrobe]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return wardrobe.filter(
      (w) =>
        (!category || w.category === category) &&
        (!q || w.name.toLowerCase().includes(q) || w.color.toLowerCase().includes(q) || w.tags.some((t) => t.includes(q))),
    );
  }, [wardrobe, category, query]);

  async function onUpload(file?: File | null) {
    if (!file) return;
    setReading(true);
    try {
      const image = await fileToCompactDataUrl(file);
      openItemModal(null, image);
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Upload failed.', 'error');
    } finally {
      setReading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="section-title">My Wardrobe</h1>
          <p className="mt-1 text-sm text-cocoa/65">Upload or add the items you already own.</p>
        </div>
        <p className="text-sm text-cocoa/55" aria-live="polite">
          {wardrobe.length} {wardrobe.length === 1 ? 'item' : 'items'}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        <div className="min-w-0 space-y-5">
          {/* Category filters */}
          <div role="tablist" aria-label="Wardrobe categories" className="scrollbar-none -mx-4 flex gap-3 overflow-x-auto px-4 pb-1 sm:mx-0 sm:flex-wrap sm:px-0">
            <button
              type="button"
              role="tab"
              aria-selected={!category}
              onClick={() => setCategory(null)}
              className="group flex shrink-0 flex-col items-center gap-1.5"
            >
              <span
                className={`flex h-14 w-14 items-center justify-center rounded-full border text-sm font-medium transition ${
                  !category ? 'border-rosebrown bg-rosebrown text-cream shadow-soft' : 'border-dusty/60 bg-white/80 text-rosebrown group-hover:bg-blush/60'
                }`}
              >
                All
              </span>
              <span className="text-[11px] text-cocoa/70">{wardrobe.length}</span>
            </button>
            {CATEGORIES.map((c) => {
              const active = category === c.id;
              return (
                <button
                  key={c.id}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  onClick={() => setCategory(active ? null : c.id)}
                  className="group flex shrink-0 flex-col items-center gap-1.5"
                >
                  <span
                    className={`flex h-14 w-14 items-center justify-center rounded-full border transition ${
                      active ? 'border-rosebrown bg-rosebrown text-cream shadow-soft' : 'border-dusty/60 bg-white/80 text-rosebrown group-hover:bg-blush/60'
                    }`}
                  >
                    <CategoryIcon category={c.id} size={24} />
                  </span>
                  <span className={`text-[11px] ${active ? 'font-semibold text-rosebrown' : 'text-cocoa/70'}`}>
                    {c.label} <span className="text-cocoa/40">({counts.get(c.id) ?? 0})</span>
                  </span>
                </button>
              );
            })}
          </div>

          {/* Search */}
          <div className="relative max-w-sm">
            <Search size={16} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-rosebrown/60" />
            <input
              type="search"
              className="input pl-10"
              placeholder="Search by name, colour or tag"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Search wardrobe"
            />
            {query && (
              <button type="button" onClick={() => setQuery('')} aria-label="Clear search" className="absolute right-3 top-1/2 -translate-y-1/2 text-rosebrown/60 hover:text-rosebrown">
                <X size={16} />
              </button>
            )}
          </div>

          {/* Grid */}
          {booting && wardrobe.length === 0 ? (
            <GridSkeleton count={10} />
          ) : wardrobe.length === 0 ? (
            <EmptyState
              icon={<CategoryIcon category="dresses" size={30} />}
              title="Your wardrobe is empty"
              message="Add the pieces you love and SIERRAH will style them into complete looks."
              action={
                <>
                  <button type="button" className="btn-primary" onClick={() => openItemModal()}>
                    <Plus size={16} /> Add your first item
                  </button>
                  <button type="button" className="btn-outline" onClick={resetDemo}>
                    Load sample wardrobe
                  </button>
                </>
              }
            />
          ) : visible.length === 0 ? (
            <EmptyState
              icon={<Search size={28} strokeWidth={1.4} />}
              title="Nothing matches"
              message="Try a different category or search term."
              action={
                <button
                  type="button"
                  className="btn-outline"
                  onClick={() => {
                    setQuery('');
                    setCategory(null);
                  }}
                >
                  Clear filters
                </button>
              }
            />
          ) : (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-5">
              {visible.map((item) => (
                <ItemCard key={item.id} item={item} onEdit={(i) => openItemModal(i)} onRemove={setToRemove} />
              ))}
            </div>
          )}
        </div>

        {/* Upload panel */}
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <div className="card flex flex-col items-center gap-4 p-6 text-center">
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              disabled={reading}
              className="flex w-full flex-col items-center gap-2 rounded-2xl border-2 border-dashed border-dusty/70 bg-cream/60 px-4 py-8 text-rosebrown transition hover:bg-blush/40"
            >
              {reading ? <Loader2 className="animate-spin" size={28} /> : <Upload size={28} strokeWidth={1.3} />}
              <span className="text-sm font-medium">Upload Photo</span>
              <span className="text-xs text-cocoa/50">JPG, PNG or WebP</span>
            </button>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              className="sr-only"
              aria-label="Upload a clothing photo"
              onChange={(e) => void onUpload(e.target.files?.[0])}
            />
            <div className="flex w-full items-center gap-3 text-xs text-cocoa/40">
              <span className="h-px flex-1 bg-blush" /> or <span className="h-px flex-1 bg-blush" />
            </div>
            <button type="button" className="btn-primary w-full" onClick={() => openItemModal()}>
              <Plus size={16} /> Add Item
            </button>
          </div>
          <button type="button" className="btn-primary mt-4 hidden w-full lg:flex" onClick={() => void saveWardrobe()} disabled={syncing}>
            {syncing && <Loader2 size={16} className="animate-spin" />} Save Wardrobe
          </button>
        </aside>
      </div>

      {/* Mobile save */}
      <div className="mt-8 flex justify-end lg:hidden">
        <button type="button" className="btn-primary" onClick={() => void saveWardrobe()} disabled={syncing}>
          {syncing && <Loader2 size={16} className="animate-spin" />} Save Wardrobe
        </button>
      </div>

      <ConfirmDialog
        open={!!toRemove}
        title="Remove this item?"
        message={`“${toRemove?.name ?? ''}” will be removed from your wardrobe. Saved looks that already use it are not affected.`}
        confirmLabel="Remove"
        onCancel={() => setToRemove(null)}
        onConfirm={() => {
          if (toRemove) {
            removeItem(toRemove.id);
            showToast(`${toRemove.name} removed.`, 'info');
          }
          setToRemove(null);
        }}
      />
    </div>
  );
}
