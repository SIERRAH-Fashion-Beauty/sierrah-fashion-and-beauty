import { Link } from 'react-router-dom';
import { Bookmark, BookmarkCheck, Heart, Lightbulb, ShoppingBag } from 'lucide-react';
import { FlowSteps } from '../components/layout/FlowSteps';
import { SLOT_META, SourceBadge, bySlot, itemDetail } from '../components/look/LookParts';
import { SmartImage } from '../components/ui/SmartImage';
import { useApp } from '../context/AppContext';
import { suggestedTotal } from '../lib/stylist';
import { formatInr } from '../data/shopCatalog';
import type { Look, LookSlot } from '../types';

function SlotCard({ look, slot }: { look: Look; slot: LookSlot }) {
  const item = bySlot(look, slot);
  if (!item) return null;
  const detail = itemDetail(item);
  return (
    <article className="card flex flex-col overflow-hidden transition hover:-translate-y-0.5 hover:shadow-soft">
      <SmartImage src={item.image} alt={item.title} className="aspect-[4/3]" />
      <div className="space-y-1 p-3">
        <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-rosebrown">
          {SLOT_META[slot].icon(13)} {SLOT_META[slot].label}
        </p>
        <h3 className="font-sans text-sm font-medium leading-snug text-cocoa">{item.title}</h3>
        {detail && <p className="line-clamp-2 text-[11px] text-cocoa/55">{detail}</p>}
        <SourceBadge source={item.source} short />
      </div>
    </article>
  );
}

export function PreviewPage() {
  const { displayLook: look, saveLook, isSaved, toggleFavorite, showToast } = useApp();
  const saved = isSaved(look.id);
  const favorite = !!saved?.favorite;
  const total = suggestedTotal(look);

  const onSave = () => {
    saveLook(look);
    showToast('Look saved to My Saved Looks.');
  };

  const onFavorite = () => {
    if (!saved) {
      saveLook(look, { favorite: true });
      showToast('Saved and added to favorites.');
    } else {
      toggleFavorite(saved.id);
      showToast(saved.favorite ? 'Removed from favorites.' : 'Added to favorites.', saved.favorite ? 'info' : 'success');
    }
  };

  return (
    <div>
      <FlowSteps />
      <div className="mb-6">
        <h1 className="section-title">Complete Look Preview</h1>
        <p className="mt-1 text-sm text-cocoa/65">See how everything comes together.</p>
      </div>

      <div className="grid items-start gap-5 md:grid-cols-[1fr_minmax(260px,340px)_1fr] lg:gap-8">
        {/* Model: first on mobile, centred on desktop */}
        <div className="order-first md:sticky md:top-24 md:order-none md:col-start-2 md:row-start-1">
          <figure className="mx-auto max-w-sm overflow-hidden rounded-3xl border border-blush bg-white shadow-lift md:max-w-none">
            <SmartImage src={look.modelImage} alt={`Model wearing the ${look.title}`} className="aspect-[3/4]" position="50% 20%" eager />
          </figure>
          <p className="mt-3 text-center font-serif text-xl text-cocoa">{look.title}</p>
          <div className="mt-4 flex items-center justify-center gap-3">
            {saved ? (
              <Link to="/saved" className="btn-soft px-7">
                <BookmarkCheck size={16} /> Saved
              </Link>
            ) : (
              <button type="button" className="btn-primary px-8" onClick={onSave}>
                <Bookmark size={16} /> Save Look
              </button>
            )}
            <button
              type="button"
              onClick={onFavorite}
              aria-pressed={favorite}
              aria-label={favorite ? 'Remove from favorites' : 'Add to favorites'}
              className={`flex h-11 w-11 items-center justify-center rounded-full border transition active:scale-90 ${
                favorite ? 'border-rosebrown bg-rosebrown text-cream' : 'border-dusty bg-white/80 text-rosebrown hover:bg-blush/50'
              }`}
            >
              <Heart size={18} fill={favorite ? 'currentColor' : 'none'} />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 md:col-start-1 md:row-start-1 md:grid-cols-1">
          <SlotCard look={look} slot="outfit" />
          <SlotCard look={look} slot="bag" />
          <SlotCard look={look} slot="footwear" />
        </div>
        <div className="grid grid-cols-2 gap-4 md:col-start-3 md:row-start-1 md:grid-cols-1">
          <SlotCard look={look} slot="jewellery" />
          <SlotCard look={look} slot="makeup" />
          <SlotCard look={look} slot="hairstyle" />
        </div>
      </div>

      {/* Tips */}
      <section aria-labelledby="tips-title" className="card mt-10 p-6 sm:p-8">
        <h2 id="tips-title" className="flex items-center gap-2 font-serif text-2xl text-cocoa">
          <Lightbulb size={22} className="text-rosegold" strokeWidth={1.5} /> Styling Tips
        </h2>
        <ul className="mt-4 grid gap-3 md:grid-cols-2">
          {look.tips.map((tip, i) => (
            <li key={i} className="flex gap-3 text-sm leading-relaxed text-cocoa/80">
              <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blush text-xs font-semibold text-rosebrown">
                {i + 1}
              </span>
              {tip}
            </li>
          ))}
        </ul>
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-blush/70 pt-5 text-sm">
          <p className="text-cocoa/65">
            {total > 0 ? (
              <>
                Optional purchases for this look: <strong className="text-rosebrown">{formatInr(total)}</strong> (demo prices)
              </>
            ) : (
              <>Every piece in this look is already yours. Nothing to buy.</>
            )}
          </p>
          <Link to="/shopping" className="btn-soft">
            <ShoppingBag size={16} /> Smart shopping ideas
          </Link>
        </div>
      </section>
    </div>
  );
}
