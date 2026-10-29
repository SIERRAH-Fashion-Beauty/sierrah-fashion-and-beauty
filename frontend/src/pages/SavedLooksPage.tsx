import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bookmark, Heart, Sparkles, Trash2 } from 'lucide-react';
import { EmptyState, Skeleton } from '../components/ui/Feedback';
import { ConfirmDialog } from '../components/ui/Modal';
import { SmartImage } from '../components/ui/SmartImage';
import { useApp } from '../context/AppContext';
import type { SavedLook } from '../types';

export function SavedLooksPage() {
  const { saved, booting, openLook, toggleFavorite, deleteSaved, showToast } = useApp();
  const navigate = useNavigate();
  const [filter, setFilter] = useState<string>('all');
  const [toDelete, setToDelete] = useState<SavedLook | null>(null);

  const filters = useMemo(() => {
    const labels = Array.from(new Set(saved.map((s) => s.occasionLabel)));
    return ['all', ...labels, ...(saved.some((s) => s.favorite) ? ['favorites'] : [])];
  }, [saved]);

  // If the active filter disappears (e.g. after deleting), fall back to "all".
  const active = filters.includes(filter) ? filter : 'all';
  const visible = saved.filter((s) => (active === 'all' ? true : active === 'favorites' ? s.favorite : s.occasionLabel === active));

  const open = (look: SavedLook) => {
    openLook(look);
    navigate('/look');
  };

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="section-title">My Saved Looks</h1>
          <p className="mt-1 text-sm text-cocoa/65">Your favorite styles, all in one place.</p>
        </div>
        {saved.length > 0 && <p className="text-sm text-cocoa/55">{saved.length} saved</p>}
      </div>

      {booting && saved.length === 0 ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4" role="status" aria-label="Loading saved looks">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="aspect-[3/4]" />
          ))}
        </div>
      ) : saved.length === 0 ? (
        <EmptyState
          icon={<Bookmark size={28} strokeWidth={1.4} />}
          title="No saved looks yet"
          message="Style a look from your wardrobe and tap Save Look. It will wait for you here."
          action={
            <Link to="/style" className="btn-primary">
              <Sparkles size={16} /> Start styling
            </Link>
          }
        />
      ) : (
        <>
          <div className="scrollbar-none -mx-4 mb-6 flex gap-2 overflow-x-auto px-4 sm:mx-0 sm:flex-wrap sm:px-0" role="group" aria-label="Filter saved looks">
            {filters.map((f) => (
              <button key={f} type="button" aria-pressed={active === f} onClick={() => setFilter(f)} className={`pill shrink-0 capitalize ${active === f ? 'pill-active' : ''}`}>
                {f === 'favorites' && <Heart size={14} fill="currentColor" />}
                {f}
              </button>
            ))}
          </div>

          {visible.length === 0 ? (
            <EmptyState title="No looks in this filter" message="Try another occasion or view everything." action={<button type="button" className="btn-outline" onClick={() => setFilter('all')}>Show all</button>} />
          ) : (
            <div className="grid grid-cols-2 gap-4 sm:gap-5 lg:grid-cols-4">
              {visible.map((look) => (
                <article key={look.id} className="card group relative animate-fade-up overflow-hidden transition hover:-translate-y-1 hover:shadow-soft">
                  <button type="button" onClick={() => open(look)} className="block w-full text-left" aria-label={`Open ${look.title}`}>
                    <SmartImage src={look.modelImage} alt={look.title} className="aspect-[3/4]" position="50% 20%" imgClassName="transition duration-700 group-hover:scale-105" />
                    <div className="py-3 pl-3.5 pr-10">
                      <p className="truncate font-sans text-sm font-medium text-cocoa">{look.title}</p>
                      <p className="mt-0.5 text-[11px] text-cocoa/50">
                        {look.occasionLabel} · Saved {new Date(look.savedAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                      </p>
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => toggleFavorite(look.id)}
                    aria-pressed={look.favorite}
                    aria-label={look.favorite ? `Remove ${look.title} from favorites` : `Add ${look.title} to favorites`}
                    className={`absolute right-2.5 top-2.5 flex h-8 w-8 items-center justify-center rounded-full shadow-card transition active:scale-90 ${
                      look.favorite ? 'bg-rosebrown text-cream' : 'bg-white/90 text-rosebrown hover:bg-white'
                    }`}
                  >
                    <Heart size={16} fill={look.favorite ? 'currentColor' : 'none'} />
                  </button>
                  <button
                    type="button"
                    onClick={() => setToDelete(look)}
                    aria-label={`Delete ${look.title}`}
                    className="absolute bottom-3 right-2.5 flex h-8 w-8 items-center justify-center rounded-full text-cocoa/40 transition hover:bg-blush/70 hover:text-rosebrown"
                  >
                    <Trash2 size={15} />
                  </button>
                </article>
              ))}
            </div>
          )}
        </>
      )}

      <ConfirmDialog
        open={!!toDelete}
        title="Delete this look?"
        message={`“${toDelete?.title ?? ''}” will be removed from your saved looks.`}
        onCancel={() => setToDelete(null)}
        onConfirm={() => {
          if (toDelete) {
            deleteSaved(toDelete.id);
            showToast('Look deleted.', 'info');
          }
          setToDelete(null);
        }}
      />
    </div>
  );
}
