import { Info, Loader2, RefreshCw, Sparkles, TriangleAlert } from 'lucide-react';
import { SmartImage } from '../ui/SmartImage';
import { useApp } from '../../context/AppContext';
import { samplePhotoFor } from '../../lib/looks';
import { resolveImageUrl } from '../../services/api';
import type { Look } from '../../types';

const DISCLAIMER =
  'AI-generated visual interpretation of this outfit. It is not an exact try-on, so colours, cut and details can differ from the real items.';

interface Props {
  look: Look;
  /** Preview uses a larger shadow and no long caption. */
  variant?: 'look' | 'preview';
}

/**
 * The model picture for a look. It is honest about where the picture comes from:
 * a real AI-generated image from the backend, or a curated sample photo that is
 * clearly labelled as not AI-generated.
 */
export function ModelImage({ look, variant = 'look' }: Props) {
  const { imageJobs, imageStatus, apiStatus, generateImage } = useApp();
  const job = imageJobs[look.id];
  const generated = look.image;
  const loading = job?.status === 'loading';
  const canGenerate = !look.isDemo;
  const src = generated ? resolveImageUrl(generated.url) : samplePhotoFor(look);

  return (
    <div>
      <figure
        className={`relative overflow-hidden rounded-3xl border border-blush bg-white ${
          variant === 'preview' ? 'shadow-lift' : 'shadow-soft'
        }`}
      >
        <SmartImage
          src={src}
          alt={generated ? `AI-generated model wearing the ${look.title}` : `Sample photo for the ${look.occasionLabel} look`}
          className="aspect-[3/4]"
          position="50% 20%"
          eager
        />
        <span
          className={`absolute left-3 top-3 inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider shadow-card ${
            generated ? 'bg-rosebrown text-cream' : 'bg-white/90 text-rosebrown'
          }`}
        >
          {generated ? (
            <>
              <Sparkles size={11} /> AI-generated
            </>
          ) : (
            'Sample photo · not AI-generated'
          )}
        </span>
        {loading && (
          <div
            role="status"
            aria-live="polite"
            className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-cream/85 px-6 text-center backdrop-blur-sm"
          >
            <Loader2 size={30} className="animate-spin text-rosebrown" />
            <p className="font-serif text-xl text-rosebrown">Creating your model preview…</p>
            <p className="text-xs text-cocoa/60">This can take up to a minute. You can keep browsing your look.</p>
          </div>
        )}
        {variant === 'look' && (
          <figcaption className="px-4 py-2.5 text-center text-[11px] text-cocoa/55">
            {generated ? DISCLAIMER : look.isDemo ? 'Sample photo for the sample look.' : 'Curated sample photo, shown until an AI preview is created.'}
          </figcaption>
        )}
      </figure>

      <div className="mt-3 space-y-2 text-sm">
        {job?.status === 'error' && (
          <div role="alert" className="flex items-start gap-2.5 rounded-2xl border border-rosebrown/30 bg-blush/50 px-4 py-3 text-rosebrown">
            <TriangleAlert size={16} className="mt-0.5 shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="text-xs leading-relaxed">{job.message}</p>
              <button type="button" className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold underline underline-offset-2" onClick={() => void generateImage(look.id, { regenerate: !!generated })}>
                <RefreshCw size={12} /> Try again
              </button>
            </div>
          </div>
        )}

        {!loading && !generated && canGenerate && job?.status !== 'error' && (
          <>
            {job?.status === 'not_configured' || imageStatus?.configured === false ? (
              <div className="flex items-start gap-2.5 rounded-2xl border border-dusty/50 bg-blush/40 px-4 py-3 text-xs leading-relaxed text-rosebrown" role="note">
                <Info size={16} className="mt-0.5 shrink-0" />
                <p>{job?.status === 'not_configured' ? job.message : imageStatus?.message}</p>
              </div>
            ) : apiStatus === 'offline' ? (
              <p className="text-center text-xs text-cocoa/55">Start the backend to create an AI model preview.</p>
            ) : (
              <button type="button" className="btn-soft w-full" onClick={() => void generateImage(look.id)}>
                <Sparkles size={16} /> Create AI model preview
              </button>
            )}
          </>
        )}

        {generated && !loading && canGenerate && (
          <div className="flex items-center justify-between gap-3 text-[11px] text-cocoa/50">
            <span>Created with {generated.provider}</span>
            <button
              type="button"
              className="inline-flex items-center gap-1 font-medium text-rosebrown underline underline-offset-2"
              onClick={() => void generateImage(look.id, { regenerate: true })}
            >
              <RefreshCw size={11} /> Regenerate
            </button>
          </div>
        )}
        {variant === 'preview' && generated && <p className="text-center text-[11px] text-cocoa/50">{DISCLAIMER}</p>}
      </div>
    </div>
  );
}
