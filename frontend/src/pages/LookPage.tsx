import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Bookmark, BookmarkCheck, Info, Sparkles } from 'lucide-react';
import { FlowSteps } from '../components/layout/FlowSteps';
import { LookChips, SLOT_META, SLOT_ORDER, SourceBadge, bySlot, itemDetail } from '../components/look/LookParts';
import { Skeleton } from '../components/ui/Feedback';
import { SmartImage } from '../components/ui/SmartImage';
import { useApp } from '../context/AppContext';

export function LookPage() {
  const { displayLook: look, generating, saveLook, isSaved, showToast } = useApp();
  const navigate = useNavigate();
  const saved = isSaved(look.id);

  const onSave = () => {
    saveLook(look);
    showToast('Look saved to My Saved Looks.');
  };

  return (
    <div>
      <FlowSteps />
      <div className="mb-5">
        <h1 className="section-title">Your Personalized Look</h1>
        <p className="mt-1 text-sm text-cocoa/65">Here&apos;s a complete look styled with your own wardrobe items.</p>
      </div>

      {look.isDemo && (
        <div className="mb-5 flex flex-wrap items-center gap-3 rounded-2xl border border-dusty/50 bg-blush/40 px-4 py-3 text-sm text-rosebrown">
          <Info size={16} className="shrink-0" />
          <span>This is a sample look. Choose an occasion to get one styled from your wardrobe.</span>
          <Link to="/style" className="font-semibold underline underline-offset-2">
            Create my look
          </Link>
        </div>
      )}

      <div className="mb-6">{generating ? <Skeleton className="h-8 w-80 max-w-full" /> : <LookChips look={look} />}</div>

      <div className="grid gap-6 md:grid-cols-[minmax(260px,400px)_1fr] lg:gap-10">
        {/* Model */}
        <div>
          {generating ? (
            <Skeleton className="aspect-[3/4] w-full" />
          ) : (
            <figure className="overflow-hidden rounded-3xl border border-blush bg-white shadow-soft">
              <SmartImage src={look.modelImage} alt={`Model wearing the ${look.title}`} className="aspect-[3/4]" position="50% 20%" eager />
              <figcaption className="px-4 py-2.5 text-center text-[11px] text-cocoa/50">
                Illustrative model preview. AI try-on generation arrives in a later phase.
              </figcaption>
            </figure>
          )}
        </div>

        {/* Items */}
        <div className="flex flex-col">
          <h2 className="mb-1 font-serif text-2xl text-cocoa">{look.title}</h2>
          <ul className="card divide-y divide-blush/70 overflow-hidden">
            {SLOT_ORDER.map((slot) => {
              const item = bySlot(look, slot);
              if (!item) return null;
              const detail = itemDetail(item);
              return (
                <li key={slot} className="flex items-center gap-4 p-3.5 sm:p-4">
                  <SmartImage src={item.image} alt={item.title} className="h-16 w-16 shrink-0 rounded-xl sm:h-[72px] sm:w-[72px]" />
                  <div className="min-w-0 flex-1">
                    <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-rosebrown">
                      {SLOT_META[slot].icon(14)} {SLOT_META[slot].label}
                    </p>
                    <p className="truncate font-medium text-cocoa">{item.title}</p>
                    {detail && <p className="line-clamp-2 text-xs text-cocoa/60">{detail}</p>}
                  </div>
                  <SourceBadge source={item.source} short />
                </li>
              );
            })}
          </ul>

          <div className="mt-6 flex flex-wrap gap-3">
            <button type="button" className="btn-primary px-7" onClick={() => navigate('/preview')}>
              View Full Look <ArrowRight size={16} />
            </button>
            {saved ? (
              <Link to="/saved" className="btn-soft">
                <BookmarkCheck size={16} /> Saved · View all
              </Link>
            ) : (
              <button type="button" className="btn-outline" onClick={onSave}>
                <Bookmark size={16} /> Save Look
              </button>
            )}
            <Link to="/personalize" className="btn-ghost">
              <Sparkles size={16} /> Tweak preferences
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
