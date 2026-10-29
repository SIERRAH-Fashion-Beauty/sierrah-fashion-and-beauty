interface Props {
  className?: string;
  /** Mirror horizontally. */
  flip?: boolean;
}

/** Delicate fine-line floral branch used as an editorial accent. */
export function FloralBranch({ className = '', flip = false }: Props) {
  return (
    <svg
      viewBox="0 0 160 260"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.1"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      style={flip ? { transform: 'scaleX(-1)' } : undefined}
      aria-hidden="true"
    >
      {/* stem */}
      <path d="M40 250C48 200 52 150 78 105c14-24 30-44 40-78" />
      {/* leaves */}
      <path d="M52 205c-16-4-28-14-32-30 16 0 28 10 32 30Z" />
      <path d="M58 170c18-2 30-12 36-28-18-2-31 8-36 28Z" />
      <path d="M68 136c-16-6-24-18-26-34 16 4 25 16 26 34Z" />
      <path d="M82 108c16-4 28-14 32-30-17 0-28 10-32 30Z" />
      <path d="M100 66c-12-6-18-16-18-30 12 4 18 14 18 30Z" />
      {/* bloom */}
      <g transform="translate(118 28)">
        <path d="M0 -4c-6-12-2-22 0-22s6 10 0 22Z" />
        <path d="M0 -4c-6-12-2-22 0-22s6 10 0 22Z" transform="rotate(72)" />
        <path d="M0 -4c-6-12-2-22 0-22s6 10 0 22Z" transform="rotate(144)" />
        <path d="M0 -4c-6-12-2-22 0-22s6 10 0 22Z" transform="rotate(216)" />
        <path d="M0 -4c-6-12-2-22 0-22s6 10 0 22Z" transform="rotate(288)" />
        <circle r="2.2" />
      </g>
      {/* buds */}
      <circle cx="28" cy="150" r="2.5" />
      <circle cx="104" cy="132" r="2" />
      <circle cx="132" cy="92" r="2.5" />
    </svg>
  );
}

/** Tiny three-petal ornament for dividers and logo accents. */
export function Blossom({ className = '' }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" className={className} aria-hidden="true">
      <path d="M12 12c-3-2-3-7 0-9 3 2 3 7 0 9Z" />
      <path d="M12 12c-1-3-6-4-9-2 1 3 6 4 9 2Z" />
      <path d="M12 12c1-3 6-4 9-2-1 3-6 4-9 2Z" />
      <path d="M12 12v9" />
    </svg>
  );
}

export function Divider({ className = '' }: { className?: string }) {
  return (
    <div className={`flex items-center gap-3 text-rosegold ${className}`} aria-hidden="true">
      <span className="h-px w-10 bg-current opacity-60" />
      <Blossom className="h-4 w-4" />
      <span className="h-px w-10 bg-current opacity-60" />
    </div>
  );
}
