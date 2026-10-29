import { useState } from 'react';
import { ImageOff } from 'lucide-react';
import type { WardrobeCategory } from '../../types';
import { CategoryIcon } from './icons';

interface Props {
  src?: string;
  alt: string;
  className?: string;
  imgClassName?: string;
  /** CSS object-position, e.g. "center 20%". */
  position?: string;
  eager?: boolean;
  /** Shows a category icon in the fallback instead of a generic one. */
  category?: WardrobeCategory;
}

/**
 * Image with a soft skeleton while loading and an elegant fallback panel if the
 * file is missing or fails, so the UI never shows a broken-image icon.
 */
export function SmartImage({ src, alt, className = '', imgClassName = '', position, eager, category }: Props) {
  // Status is tied to the src it was reported for, so a new src automatically
  // reads as "loading" without an effect (which could clobber an early onLoad).
  const [result, setResult] = useState<{ src?: string; status: 'ready' | 'error' } | null>(null);
  const status: 'loading' | 'ready' | 'error' = !src ? 'error' : result?.src === src ? result.status : 'loading';
  const setStatus = (s: 'ready' | 'error') => setResult({ src, status: s });

  return (
    <div className={`relative overflow-hidden bg-blush/40 ${className}`}>
      {status !== 'ready' && status !== 'error' && <div className="shimmer absolute inset-0" />}
      {status === 'error' ? (
        <div
          role="img"
          aria-label={alt}
          className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-gradient-to-br from-blush/70 via-petal to-cream text-rosegold"
        >
          {category ? <CategoryIcon category={category} size={34} /> : <ImageOff size={30} strokeWidth={1.4} />}
          <span className="px-2 text-center text-[11px] uppercase tracking-widest text-rosebrown/70">
            {src ? 'Image unavailable' : 'No photo yet'}
          </span>
        </div>
      ) : (
        <img
          src={src}
          alt={alt}
          loading={eager ? 'eager' : 'lazy'}
          decoding="async"
          draggable={false}
          ref={(el) => {
            // Image may already be cached/complete before React attached onLoad.
            if (el?.complete && el.naturalWidth > 0 && status === 'loading') setStatus('ready');
          }}
          onLoad={() => setStatus('ready')}
          onError={() => setStatus('error')}
          style={position ? { objectPosition: position } : undefined}
          className={`h-full w-full object-cover transition-opacity duration-500 ${
            status === 'ready' ? 'opacity-100' : 'opacity-0'
          } ${imgClassName}`}
        />
      )}
    </div>
  );
}
