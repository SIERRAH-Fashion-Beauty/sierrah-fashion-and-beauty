import { Gem, Handbag, Shirt, Sparkles, type LucideProps } from 'lucide-react';
import type { WardrobeCategory } from '../../types';

/**
 * Fine-line fashion icons that match Lucide's 1.5px stroke style, for
 * categories Lucide does not cover (dress, trousers, heel, perfume).
 */
function Base({ children, size = 24, strokeWidth = 1.5, className }: LucideProps & { children: React.ReactNode }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

export const DressIcon = (p: LucideProps) => (
  <Base {...p}>
    <path d="M9 2.5 8 7l1.5 3L6 21.5h12L14.5 10 16 7l-1-4.5" />
    <path d="M9 2.5c.8 1.4 1.8 2 3 2s2.2-.6 3-2" />
    <path d="M9.5 10h5" />
  </Base>
);

export const TrousersIcon = (p: LucideProps) => (
  <Base {...p}>
    <path d="M7 3h10l1.2 18.5h-4.3L12 9.5l-1.9 12H5.8L7 3Z" />
    <path d="M7.2 6.5h9.6" />
  </Base>
);

export const HeelIcon = (p: LucideProps) => (
  <Base {...p}>
    <path d="M3 5v8c0 3 2 4.5 5.5 4.5 3.5 0 6-1.3 8-3l4 .8v3.2h-3.5" />
    <path d="M3 5h4c.3 3 1.5 5 4 6.5" />
    <path d="M5 21h2.5l-.5-4" />
  </Base>
);

export const PerfumeIcon = (p: LucideProps) => (
  <Base {...p}>
    <rect x="6" y="9" width="12" height="12" rx="3" />
    <path d="M10 9V6.5h4V9" />
    <path d="M9 3.5h6v3H9z" />
    <path d="M9.5 14.5c1 1 4 1 5 0" />
  </Base>
);

export const LipstickIcon = (p: LucideProps) => (
  <Base {...p}>
    <rect x="7" y="13" width="10" height="8" rx="1.5" />
    <path d="M8.5 13V9.5h7V13" />
    <path d="M9.5 9.5V5l3.5-2.5V9.5" />
  </Base>
);

export const CATEGORY_ICONS: Record<WardrobeCategory, (p: LucideProps) => React.ReactElement> = {
  tops: (p) => <Shirt {...p} strokeWidth={p.strokeWidth ?? 1.5} />,
  bottoms: TrousersIcon,
  dresses: DressIcon,
  footwear: HeelIcon,
  bags: (p) => <Handbag {...p} strokeWidth={p.strokeWidth ?? 1.5} />,
  jewellery: (p) => <Gem {...p} strokeWidth={p.strokeWidth ?? 1.5} />,
  kurtis: (p) => <Shirt {...p} strokeWidth={p.strokeWidth ?? 1.5} />,
  sarees: DressIcon,
  makeup: LipstickIcon,
  skincare: PerfumeIcon,
};

export function CategoryIcon({ category, ...props }: { category: WardrobeCategory } & LucideProps) {
  const Icon = CATEGORY_ICONS[category];
  return <Icon {...props} />;
}

export const SparkleIcon = (p: LucideProps) => <Sparkles {...p} strokeWidth={p.strokeWidth ?? 1.5} />;
