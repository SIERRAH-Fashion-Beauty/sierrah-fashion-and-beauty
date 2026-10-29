import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Check, ChevronDown, Loader2, Plus, Sparkles, TriangleAlert } from 'lucide-react';
import { FlowSteps } from '../components/layout/FlowSteps';
import { FloralBranch } from '../components/ui/Floral';
import { useApp } from '../context/AppContext';
import { APPEARANCE_OPTIONS, BUDGETS, COLOR_OPTIONS, PREFERENCES, STYLES, occasionLabel } from '../data/options';
import type { PreferenceId } from '../types';

const hexFor = (name: string) => COLOR_OPTIONS.find((c) => c.name.toLowerCase() === name.toLowerCase())?.hex ?? name.toLowerCase();

export function PersonalizePage() {
  const { preferences, patchPreferences, modelOptions, patchModelOptions, generate, generating, generateError, imageStatus, showToast } = useApp();
  const navigate = useNavigate();
  const [adding, setAdding] = useState(false);
  const [customColor, setCustomColor] = useState('');

  const toggleColor = (name: string) =>
    patchPreferences({
      colors: preferences.colors.includes(name) ? preferences.colors.filter((c) => c !== name) : [...preferences.colors, name],
    });

  const toggleTrait = (id: PreferenceId) =>
    patchPreferences({
      traits: preferences.traits.includes(id) ? preferences.traits.filter((t) => t !== id) : [...preferences.traits, id],
    });

  const customList = preferences.colors.filter((c) => !COLOR_OPTIONS.some((o) => o.name === c));

  function addCustomColor() {
    const raw = customColor.trim();
    if (!raw) return;
    const name = raw.charAt(0).toUpperCase() + raw.slice(1).toLowerCase();
    if (!CSS.supports('color', raw)) {
      showToast(`“${raw}” isn't a colour name we recognise. Try something like Maroon or Teal.`, 'error');
      return;
    }
    if (!preferences.colors.includes(name)) patchPreferences({ colors: [...preferences.colors, name] });
    setCustomColor('');
    setAdding(false);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (generating) return;
    try {
      await generate();
      navigate('/look');
    } catch {
      /* the reason is shown under the button; the form keeps every choice so the user can retry */
    }
  }

  return (
    <div>
      <FlowSteps />
      <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
        {/* Decorative sidebar */}
        <aside className="relative hidden overflow-hidden rounded-3xl bg-gradient-to-b from-blush/80 to-petal lg:block">
          <FloralBranch className="absolute -left-4 top-6 h-56 text-rosegold/60" />
          <div className="relative flex h-full min-h-[560px] flex-col justify-center px-7 py-10">
            <p className="font-script text-4xl leading-snug text-rosebrown">
              Style isn&apos;t about fitting in, it&apos;s about standing out.
            </p>
          </div>
          <FloralBranch flip className="absolute -right-4 bottom-6 h-56 rotate-180 text-rosegold/60" />
        </aside>

        <form onSubmit={submit} className="card space-y-8 p-6 sm:p-8">
          <div>
            <h1 className="section-title">Personalize Your Look</h1>
            <p className="mt-1 text-sm text-cocoa/65">Choose your style, colors, budget and preferences.</p>
            <p className="mt-3 text-sm">
              <span className="text-cocoa/55">Occasion:</span>{' '}
              <span className="rounded-full bg-blush/70 px-3 py-1 text-xs font-medium text-rosebrown">
                {occasionLabel(preferences.occasion, preferences.customOccasion ?? undefined)}
              </span>{' '}
              <Link to="/style" className="ml-1 text-xs text-rosebrown underline underline-offset-2">
                Change
              </Link>
            </p>
          </div>

          <fieldset>
            <legend className="mb-3 font-serif text-xl text-cocoa">Style Preference</legend>
            <div className="flex flex-wrap gap-2.5" role="radiogroup" aria-label="Style preference">
              {STYLES.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  role="radio"
                  aria-checked={preferences.style === s.id}
                  onClick={() => patchPreferences({ style: preferences.style === s.id ? null : s.id })}
                  className={`pill px-5 ${preferences.style === s.id ? 'pill-active' : ''}`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend className="mb-3 font-serif text-xl text-cocoa">Favorite Colors</legend>
            <div className="flex flex-wrap items-center gap-3">
              {[...COLOR_OPTIONS.map((c) => c.name), ...customList].map((name) => {
                const active = preferences.colors.includes(name);
                const hex = hexFor(name);
                return (
                  <button
                    key={name}
                    type="button"
                    aria-pressed={active}
                    aria-label={name}
                    title={name}
                    onClick={() => toggleColor(name)}
                    className={`relative flex h-10 w-10 items-center justify-center rounded-full border border-black/10 shadow-card transition hover:scale-110 ${
                      active ? 'ring-2 ring-rosebrown ring-offset-2 ring-offset-cream' : ''
                    }`}
                    style={{ backgroundColor: hex }}
                  >
                    {active && <Check size={16} strokeWidth={3} className={['White', 'Beige', 'Yellow'].includes(name) ? 'text-rosebrown' : 'text-white'} />}
                  </button>
                );
              })}
              <button
                type="button"
                aria-label="Add a custom colour"
                aria-expanded={adding}
                onClick={() => setAdding((a) => !a)}
                className="flex h-10 w-10 items-center justify-center rounded-full border border-dashed border-rosebrown/60 text-rosebrown transition hover:bg-blush/60"
              >
                <Plus size={18} />
              </button>
            </div>
            {adding && (
              <div className="mt-3 flex max-w-xs animate-fade-up gap-2">
                <input
                  className="input"
                  placeholder="Colour name, e.g. Maroon"
                  value={customColor}
                  maxLength={20}
                  autoFocus
                  onChange={(e) => setCustomColor(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addCustomColor();
                    }
                  }}
                />
                <button type="button" className="btn-soft" onClick={addCustomColor}>
                  Add
                </button>
              </div>
            )}
            {preferences.colors.length > 0 && <p className="mt-3 text-xs text-cocoa/55">Selected: {preferences.colors.join(', ')}</p>}
          </fieldset>

          <fieldset>
            <legend className="mb-3 font-serif text-xl text-cocoa">Budget Range</legend>
            <div className="grid gap-2.5 sm:grid-cols-2" role="radiogroup" aria-label="Budget range">
              {BUDGETS.map((b) => {
                const active = preferences.budget === b.id;
                return (
                  <label
                    key={b.id}
                    className={`flex cursor-pointer items-center gap-3 rounded-xl border px-4 py-3 text-sm transition ${
                      active ? 'border-rosebrown bg-blush/60 font-medium text-rosebrown' : 'border-dusty/50 bg-white/70 hover:bg-blush/30'
                    } focus-within:ring-2 focus-within:ring-rosebrown/50`}
                  >
                    <input
                      type="radio"
                      name="budget"
                      className="sr-only"
                      checked={active}
                      onChange={() => patchPreferences({ budget: b.id })}
                    />
                    <span className={`flex h-4 w-4 items-center justify-center rounded-full border ${active ? 'border-rosebrown' : 'border-dusty'}`}>
                      {active && <span className="h-2 w-2 rounded-full bg-rosebrown" />}
                    </span>
                    {b.label}
                  </label>
                );
              })}
            </div>
            <p className="mt-2 text-xs text-cocoa/50">Applies only to optional purchase suggestions. Your own wardrobe is always free.</p>
          </fieldset>

          <fieldset>
            <legend className="mb-3 font-serif text-xl text-cocoa">Other Preferences (optional)</legend>
            <div className="flex flex-wrap gap-x-6 gap-y-3">
              {PREFERENCES.map((p) => {
                const active = preferences.traits.includes(p.id);
                return (
                  <label key={p.id} className="flex cursor-pointer items-center gap-2.5 text-sm focus-within:[&>span]:ring-2 focus-within:[&>span]:ring-rosebrown/50">
                    <input type="checkbox" className="sr-only" checked={active} onChange={() => toggleTrait(p.id)} />
                    <span
                      className={`flex h-5 w-5 items-center justify-center rounded-md border transition ${
                        active ? 'border-rosebrown bg-rosebrown text-cream' : 'border-dusty bg-white'
                      }`}
                    >
                      {active && <Check size={13} strokeWidth={3} />}
                    </span>
                    {p.label}
                  </label>
                );
              })}
            </div>
          </fieldset>

          <div>
            <label htmlFor="notes" className="mb-3 block font-serif text-xl text-cocoa">
              Special Requirements
            </label>
            <textarea
              id="notes"
              rows={3}
              maxLength={240}
              className="input resize-none"
              placeholder="e.g. Modest neckline, outdoor event, avoid heels, match with a green dupatta"
              value={preferences.notes}
              onChange={(e) => patchPreferences({ notes: e.target.value })}
            />
            <p className="mt-1 text-right text-[11px] text-cocoa/40">{preferences.notes.length}/240</p>
          </div>

          <details className="group rounded-2xl border border-dusty/50 bg-white/60">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 font-serif text-xl text-cocoa [&::-webkit-details-marker]:hidden">
              <span>
                Model Appearance <span className="font-sans text-xs font-normal text-cocoa/45">(optional)</span>
              </span>
              <ChevronDown size={18} className="text-rosebrown transition group-open:rotate-180" />
            </summary>
            <div className="space-y-4 px-4 pb-4">
              <p className="text-xs leading-relaxed text-cocoa/60">
                Used only to describe the AI model in your preview. Leave everything empty for a default adult model. Nothing here is about you
                personally, and no photo of you is ever needed.
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                {APPEARANCE_OPTIONS.map((opt) => (
                  <label key={opt.key} className="block text-xs font-medium text-cocoa/70">
                    {opt.label}
                    <select
                      className="input mt-1 capitalize"
                      value={modelOptions.appearance[opt.key] ?? ''}
                      onChange={(e) =>
                        patchModelOptions({ appearance: { ...modelOptions.appearance, [opt.key]: e.target.value || null } })
                      }
                    >
                      <option value="">No preference</option>
                      {opt.values.map((v) => (
                        <option key={v} value={v}>
                          {v}
                        </option>
                      ))}
                    </select>
                  </label>
                ))}
              </div>
              <label className="flex cursor-pointer items-start gap-2.5 text-sm focus-within:[&>span]:ring-2 focus-within:[&>span]:ring-rosebrown/50">
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={modelOptions.useReferenceImages}
                  onChange={(e) => patchModelOptions({ useReferenceImages: e.target.checked })}
                />
                <span
                  className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border transition ${
                    modelOptions.useReferenceImages ? 'border-rosebrown bg-rosebrown text-cream' : 'border-dusty bg-white'
                  }`}
                >
                  {modelOptions.useReferenceImages && <Check size={13} strokeWidth={3} />}
                </span>
                <span>
                  Use my clothing photos as a visual guide
                  <span className="mt-0.5 block text-xs text-cocoa/50">
                    Sends up to 4 photos of the garments in the look to the image provider. The result is still an interpretation, not an exact try-on.
                  </span>
                </span>
              </label>
              {imageStatus && !imageStatus.configured && (
                <p className="rounded-xl bg-blush/50 p-3 text-xs leading-relaxed text-rosebrown">{imageStatus.message}</p>
              )}
            </div>
          </details>

          {generateError && (
            <div role="alert" className="flex items-start gap-3 rounded-2xl border border-rosebrown/30 bg-blush/50 px-4 py-3 text-sm text-rosebrown">
              <TriangleAlert size={18} className="mt-0.5 shrink-0" />
              <div>
                <p className="font-medium">We couldn&apos;t create your look.</p>
                <p className="mt-0.5 text-xs leading-relaxed">{generateError}</p>
                <p className="mt-1 text-xs text-rosebrown/80">Your choices are kept. Press Get My Look to try again.</p>
              </div>
            </div>
          )}

          <button type="submit" disabled={generating} className="btn-primary w-full py-3.5 text-base">
            {generating ? (
              <>
                <Loader2 size={18} className="animate-spin" /> Styling your look…
              </>
            ) : (
              <>
                Get My Look <Sparkles size={18} />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
