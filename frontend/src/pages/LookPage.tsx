import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Bookmark, BookmarkCheck, Info, ShoppingBag, Sparkles } from 'lucide-react';
import { FlowSteps } from '../components/layout/FlowSteps';
import { LookChips, ScoreBadge, SLOT_META, SLOT_ORDER, SourceBadge, bySlot, itemDetail } from '../components/look/LookParts';
import { ModelImage } from '../components/look/ModelImage';
import { Skeleton } from '../components/ui/Feedback';
import { SmartImage } from '../components/ui/SmartImage';
import { useApp } from '../context/AppContext';
import { formatInr } from '../data/shopCatalog';

export function LookPage() {
  const { displayLook: look, options, limitations, selectLook, generating, saveLook, isSaved, showToast } = useApp();
  const navigate = useNavigate();
  const saved = isSaved(look.id);
  const choices = options.length > 1 ? options : [];

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

      {!look.isDemo && limitations.length > 0 && (
        <ul className="mb-5 space-y-1.5 rounded-2xl border border-dusty/50 bg-blush/40 px-4 py-3 text-sm text-rosebrown" aria-label="Notes about this recommendation">
          {limitations.map((text) => (
            <li key={text} className="flex gap-2.5">
              <Info size={16} className="mt-0.5 shrink-0" />
              <span>{text}</span>
            </li>
          ))}
        </ul>
      )}

      <div className="mb-6">{generating ? <Skeleton className="h-8 w-80 max-w-full" /> : <LookChips look={look} />}</div>

      {choices.length > 0 && (
        <div className="mb-6" role="tablist" aria-label="Outfit options">
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-rosebrown">{choices.length} different looks for you</p>
          <div className="flex flex-wrap gap-2">
            {choices.map((option, index) => {
              const active = option.id === look.id;
              return (
                <button
                  key={option.id}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  onClick={() => selectLook(option.id)}
                  className={`pill gap-2 px-4 ${active ? 'pill-active' : ''}`}
                >
                  Option {index + 1}
                  <span className={`text-[11px] ${active ? 'text-cream/80' : 'text-cocoa/50'}`}>{Math.round(option.score)}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-[minmax(260px,400px)_1fr] lg:gap-10">
        {/* Model */}
        <div>{generating ? <Skeleton className="aspect-[3/4] w-full" /> : <ModelImage look={look} />}</div>

        {/* Items */}
        <div className="flex flex-col">
          <div className="mb-1 flex flex-wrap items-center gap-x-3 gap-y-1">
            <h2 className="font-serif text-2xl text-cocoa">{look.title}</h2>
            {!look.isDemo || look.score ? <ScoreBadge look={look} /> : null}
          </div>
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

          {look.whyItWorks.length > 0 && (
            <section aria-labelledby="why-title" className="mt-5 rounded-2xl border border-blush bg-white/70 p-4">
              <h3 id="why-title" className="font-serif text-lg text-cocoa">
                Why this works
              </h3>
              <ul className="mt-2 space-y-1.5 text-sm text-cocoa/75">
                {look.whyItWorks.map((reason) => (
                  <li key={reason} className="flex gap-2">
                    <span aria-hidden className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-rosegold" />
                    {reason}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {look.missingItems.length > 0 && (
            <section aria-labelledby="missing-title" className="mt-4 rounded-2xl border border-dusty/50 bg-blush/30 p-4">
              <h3 id="missing-title" className="flex items-center gap-2 font-serif text-lg text-cocoa">
                <ShoppingBag size={16} className="text-rosegold" /> To complete this look
              </h3>
              <ul className="mt-2 space-y-1.5 text-sm text-cocoa/75">
                {look.missingItems.map((m) => (
                  <li key={`${m.slot}-${m.label}`}>
                    <strong className="font-medium text-cocoa">{m.label}</strong>
                    {m.suggestion ? (
                      <>
                        {' '}
                        · {formatInr(m.suggestion.price)} <span className="text-[10px] uppercase tracking-wider text-cocoa/45">demo price</span>
                        {!m.withinBudget && <span className="text-rosebrown"> · above your budget</span>}
                      </>
                    ) : null}
                    <span className="block text-xs text-cocoa/55">{m.reason}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

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
