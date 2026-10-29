import { useNavigate } from 'react-router-dom';
import { ArrowRight, CalendarHeart, Check } from 'lucide-react';
import { FlowSteps } from '../components/layout/FlowSteps';
import { SmartImage } from '../components/ui/SmartImage';
import { useApp } from '../context/AppContext';
import { OCCASIONS } from '../data/options';

export function OccasionPage() {
  const { preferences, patchPreferences } = useApp();
  const navigate = useNavigate();
  const selected = preferences.occasion;
  const customReady = selected !== 'custom' || !!preferences.customOccasion?.trim();

  return (
    <div>
      <FlowSteps />
      <div className="mb-7">
        <h1 className="section-title">Choose Your Occasion</h1>
        <p className="mt-1 text-sm text-cocoa/65">Tell us where you&apos;re going, and we&apos;ll create the perfect look for you.</p>
      </div>

      <div role="radiogroup" aria-label="Occasion" className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 lg:gap-5">
        {OCCASIONS.map((o) => {
          const active = selected === o.id;
          return (
            <button
              key={o.id}
              type="button"
              role="radio"
              aria-checked={active}
              onClick={() => patchPreferences({ occasion: o.id })}
              className={`group relative overflow-hidden rounded-2xl border bg-white/80 text-left transition duration-300 ${
                active ? 'border-rosebrown shadow-lift ring-2 ring-rosebrown' : 'border-blush/80 shadow-card hover:-translate-y-1 hover:shadow-soft'
              }`}
            >
              {o.image ? (
                <SmartImage
                  src={o.image}
                  alt={`${o.label} outfit inspiration`}
                  position="50% 22%"
                  className="aspect-[4/3.4]"
                  imgClassName="transition duration-700 group-hover:scale-105"
                />
              ) : (
                <div className="flex aspect-[4/3.4] flex-col items-center justify-center gap-2 bg-gradient-to-br from-blush/60 to-cream text-rosebrown">
                  <CalendarHeart size={42} strokeWidth={1.2} />
                  <span className="px-4 text-center text-xs text-cocoa/60">{o.blurb}</span>
                </div>
              )}
              {active && (
                <span className="absolute right-3 top-3 flex h-7 w-7 animate-pop-in items-center justify-center rounded-full bg-rosebrown text-cream shadow-card">
                  <Check size={16} strokeWidth={2.5} />
                </span>
              )}
              <div className={`px-3 py-3 text-center text-sm font-medium transition ${active ? 'bg-rosebrown text-cream' : 'text-cocoa'}`}>
                {o.label}
                {o.id === 'custom' && <span className="mt-0.5 block text-[11px] font-normal opacity-80">Describe your event</span>}
              </div>
            </button>
          );
        })}
      </div>

      {selected === 'custom' && (
        <div className="card mt-6 max-w-xl animate-fade-up p-5">
          <label htmlFor="custom-occasion" className="label">
            Describe your event
          </label>
          <input
            id="custom-occasion"
            className="input"
            maxLength={60}
            autoFocus
            placeholder="e.g. Cousin's engagement, job interview, beach brunch"
            value={preferences.customOccasion ?? ''}
            onChange={(e) => patchPreferences({ customOccasion: e.target.value })}
          />
          <p className="mt-2 text-xs text-cocoa/55">We&apos;ll match it to the closest styling profile, like wedding, office or travel.</p>
        </div>
      )}

      <div className="mt-8 flex flex-wrap items-center justify-between gap-4">
        <p className="text-sm text-cocoa/60">
          Selected:{' '}
          <span className="font-medium text-rosebrown">
            {selected === 'custom' ? preferences.customOccasion?.trim() || 'Custom Occasion' : OCCASIONS.find((o) => o.id === selected)?.label}
          </span>
        </p>
        <button type="button" className="btn-primary px-8" disabled={!customReady} onClick={() => navigate('/personalize')}>
          Continue <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}
