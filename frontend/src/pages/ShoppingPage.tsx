import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Info, ShoppingBag } from 'lucide-react';
import { FlowSteps } from '../components/layout/FlowSteps';
import { EmptyState } from '../components/ui/Feedback';
import { FloralBranch } from '../components/ui/Floral';
import { CategoryIcon } from '../components/ui/icons';
import { Modal } from '../components/ui/Modal';
import { SmartImage } from '../components/ui/SmartImage';
import { useApp } from '../context/AppContext';
import { BUDGETS, CATEGORIES, ITEM_OCCASIONS, categoryLabel } from '../data/options';
import { SHOP_CATALOG, formatInr } from '../data/shopCatalog';
import { lookProductIds, ownsSimilar } from '../lib/looks';
import { api } from '../services/api';
import type { ShopItem, WardrobeCategory } from '../types';

function ShopCard({ item, tag, onView }: { item: ShopItem; tag?: string; onView: (i: ShopItem) => void }) {
  return (
    <article className="card group flex flex-col overflow-hidden transition hover:-translate-y-1 hover:shadow-soft">
      <div className="relative">
        <SmartImage src={item.image} alt={item.name} category={item.category} className="aspect-square" imgClassName="transition duration-500 group-hover:scale-105" />
        {tag && (
          <span className="absolute left-2.5 top-2.5 rounded-full bg-white/90 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-rosebrown shadow-card">
            {tag}
          </span>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-1 p-3.5">
        <h3 className="font-sans text-sm font-medium text-cocoa">{item.name}</h3>
        <p className="text-xs text-cocoa/50">{categoryLabel(item.category)}</p>
        <p className="mt-1 flex items-baseline gap-1.5">
          <span className="font-serif text-xl font-semibold text-rosebrown">{formatInr(item.price)}</span>
          <span className="rounded bg-blush/70 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-rosebrown">Demo price</span>
        </p>
        <button type="button" className="btn-primary mt-auto w-full px-4 py-2 text-xs" onClick={() => onView(item)}>
          View Options
        </button>
      </div>
    </article>
  );
}

export function ShoppingPage() {
  const { wardrobe, displayLook, apiStatus } = useApp();
  const [catalog, setCatalog] = useState<ShopItem[]>(SHOP_CATALOG);
  const [category, setCategory] = useState<WardrobeCategory | 'all'>('all');
  const [budget, setBudget] = useState<string>('any');
  const [viewing, setViewing] = useState<ShopItem | null>(null);

  // The API serves the same demo catalog; the bundled copy is the offline fallback.
  useEffect(() => {
    if (apiStatus !== 'online') return;
    let cancelled = false;
    api
      .getCatalog()
      .then((items) => !cancelled && items.length && setCatalog(items))
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [apiStatus]);

  // Ownership is judged against the wardrobe on screen, so it is right even before a sync.
  const missing = useMemo(() => catalog.filter((p) => !ownsSimilar(wardrobe, p)), [catalog, wardrobe]);
  const missingIds = useMemo(() => new Set(missing.map((m) => m.id)), [missing]);
  const lookIds = useMemo(() => lookProductIds(displayLook), [displayLook]);

  const max = BUDGETS.find((b) => b.id === budget)?.max ?? Infinity;
  const passes = (s: ShopItem) => (category === 'all' || s.category === category) && s.price <= max;

  const missingShown = missing.filter(passes).sort((a, b) => Number(lookIds.has(b.id)) - Number(lookIds.has(a.id)));
  const moreShown = catalog.filter((s) => !missingIds.has(s.id) && passes(s));
  const categoriesInCatalog = CATEGORIES.filter((c) => catalog.some((s) => s.category === c.id));

  return (
    <div>
      <FlowSteps />
      <div className="mb-5">
        <h1 className="section-title">Smart Shopping Suggestions</h1>
        <p className="mt-1 text-sm text-cocoa/65">Only what you need. Budget-friendly options.</p>
      </div>

      <div className="mb-6 flex items-start gap-3 rounded-2xl border border-dusty/50 bg-blush/40 px-4 py-3 text-sm text-rosebrown" role="note">
        <Info size={18} className="mt-0.5 shrink-0" />
        <p>
          <strong>Demo mode:</strong> products and prices below are illustrative. SIERRAH isn&apos;t connected to any live store, so nothing here can be purchased.
        </p>
      </div>

      {/* Filters */}
      <div className="mb-8 flex flex-wrap items-center gap-3">
        <div className="scrollbar-none -mx-4 flex gap-2 overflow-x-auto px-4 sm:mx-0 sm:flex-wrap sm:px-0" role="group" aria-label="Filter by category">
          <button type="button" aria-pressed={category === 'all'} onClick={() => setCategory('all')} className={`pill shrink-0 ${category === 'all' ? 'pill-active' : ''}`}>
            All
          </button>
          {categoriesInCatalog.map((c) => (
            <button
              key={c.id}
              type="button"
              aria-pressed={category === c.id}
              onClick={() => setCategory(c.id)}
              className={`pill shrink-0 ${category === c.id ? 'pill-active' : ''}`}
            >
              <CategoryIcon category={c.id} size={16} /> {c.label}
            </button>
          ))}
        </div>
        <label className="ml-auto flex items-center gap-2 text-sm text-cocoa/70">
          <span className="sr-only sm:not-sr-only">Budget</span>
          <select className="input w-auto py-2 pr-8" value={budget} onChange={(e) => setBudget(e.target.value)} aria-label="Filter by budget">
            <option value="any">Any budget</option>
            {BUDGETS.filter((b) => b.max !== Infinity).map((b) => (
              <option key={b.id} value={b.id}>
                Up to ₹{b.max.toLocaleString('en-IN')}
              </option>
            ))}
          </select>
        </label>
      </div>

      {/* Missing */}
      <section aria-labelledby="missing-title" className="mb-10">
        <div className="mb-4 flex items-baseline justify-between gap-3">
          <h2 id="missing-title" className="font-serif text-2xl text-cocoa">
            Missing Items
          </h2>
          <span className="text-xs text-cocoa/50">{missingShown.length} suggested</span>
        </div>
        {missingShown.length ? (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {missingShown.map((s) => (
              <ShopCard key={s.id} item={s} tag={lookIds.has(s.id) ? 'For your look' : undefined} onView={setViewing} />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={<ShoppingBag size={28} strokeWidth={1.4} />}
            title="Nothing missing here"
            message="Your wardrobe already covers this filter. Try another category or budget."
            action={
              <button type="button" className="btn-outline" onClick={() => { setCategory('all'); setBudget('any'); }}>
                Reset filters
              </button>
            }
          />
        )}
      </section>

      {/* More */}
      {moreShown.length > 0 && (
        <section aria-labelledby="more-title" className="mb-10">
          <div className="mb-1 flex items-baseline justify-between gap-3">
            <h2 id="more-title" className="font-serif text-2xl text-cocoa">
              More Budget-Friendly Options
            </h2>
            <span className="text-xs text-cocoa/50">{moreShown.length} items</span>
          </div>
          <p className="mb-4 text-xs text-cocoa/55">You may already own something similar, so these are optional.</p>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {moreShown.map((s) => (
              <ShopCard key={s.id} item={s} tag="You own similar" onView={setViewing} />
            ))}
          </div>
        </section>
      )}

      {/* Message */}
      <aside className="card relative overflow-hidden px-6 py-10 text-center">
        <FloralBranch className="pointer-events-none absolute -left-3 bottom-0 h-40 text-dusty/50" />
        <FloralBranch flip className="pointer-events-none absolute -right-3 bottom-0 h-40 text-dusty/50" />
        <p className="relative mx-auto max-w-lg font-serif text-2xl italic leading-snug text-rosebrown sm:text-3xl">
          &ldquo;You already have so much! SIERRAH helps you style it better, not buy more.&rdquo;
        </p>
        <p className="relative mt-3 text-sm text-cocoa/60">
          Your wardrobe holds {wardrobe.length} pieces.{' '}
          <Link to="/style" className="font-medium text-rosebrown underline underline-offset-2">
            Style another look
          </Link>
        </p>
      </aside>

      <Modal
        open={!!viewing}
        onClose={() => setViewing(null)}
        title={viewing?.name ?? ''}
        description="Demo product details"
        footer={
          <button type="button" className="btn-primary" onClick={() => setViewing(null)} data-autofocus>
            Got it
          </button>
        }
      >
        {viewing && (
          <div className="grid gap-5 sm:grid-cols-[200px_1fr]">
            <SmartImage src={viewing.image} alt={viewing.name} category={viewing.category} className="aspect-square rounded-2xl" />
            <div className="space-y-3 text-sm">
              <p className="font-serif text-3xl font-semibold text-rosebrown">
                {formatInr(viewing.price)} <span className="ml-1 align-middle text-[10px] font-sans font-semibold uppercase tracking-wider text-cocoa/50">Demo price</span>
              </p>
              <p className="text-cocoa/75">{viewing.description}</p>
              <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-xs text-cocoa/65">
                <dt className="font-semibold text-cocoa/80">Category</dt>
                <dd>{categoryLabel(viewing.category)}{viewing.subcategory ? ` · ${viewing.subcategory}` : ''}</dd>
                {viewing.colors.length > 0 && (
                  <>
                    <dt className="font-semibold text-cocoa/80">Colours</dt>
                    <dd>{viewing.colors.join(', ')}</dd>
                  </>
                )}
                {viewing.fabric && (
                  <>
                    <dt className="font-semibold text-cocoa/80">Fabric</dt>
                    <dd>{viewing.fabric}</dd>
                  </>
                )}
                <dt className="font-semibold text-cocoa/80">Comfort</dt>
                <dd>{viewing.comfort} / 5</dd>
              </dl>
              <p className="text-xs text-cocoa/55">
                Styles well for: {viewing.occasions.map((o) => ITEM_OCCASIONS.find((x) => x.id === o)?.label).join(', ')}
              </p>
              <p className="rounded-xl bg-blush/50 p-3 text-xs leading-relaxed text-rosebrown">
                SIERRAH is not connected to live retailers yet, so there is no real listing, stock or checkout for this product. This card shows how smart suggestions will look.
              </p>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
