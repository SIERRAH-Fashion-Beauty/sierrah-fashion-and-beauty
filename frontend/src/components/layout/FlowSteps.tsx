import { Link, useLocation } from 'react-router-dom';
import { Check } from 'lucide-react';

const STEPS = [
  { to: '/style', label: 'Occasion' },
  { to: '/personalize', label: 'Personalize' },
  { to: '/look', label: 'Your Look' },
  { to: '/preview', label: 'Preview' },
  { to: '/shopping', label: 'Shop Smart' },
];

/** Small breadcrumb that keeps the multi-screen styling flow navigable. */
export function FlowSteps() {
  const { pathname } = useLocation();
  const current = STEPS.findIndex((s) => s.to === pathname);
  return (
    <nav aria-label="Styling steps" className="scrollbar-none -mx-1 mb-5 flex gap-1 overflow-x-auto px-1 text-xs">
      {STEPS.map((s, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <Link
            key={s.to}
            to={s.to}
            aria-current={active ? 'step' : undefined}
            className={`flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1.5 transition ${
              active
                ? 'bg-rosebrown text-cream'
                : done
                  ? 'bg-blush/70 text-rosebrown hover:bg-blush'
                  : 'text-cocoa/55 hover:bg-blush/40 hover:text-rosebrown'
            }`}
          >
            <span
              className={`flex h-4 w-4 items-center justify-center rounded-full text-[10px] ${
                active ? 'bg-cream/25' : done ? 'bg-rosebrown text-cream' : 'border border-dusty'
              }`}
            >
              {done ? <Check size={10} strokeWidth={3} /> : i + 1}
            </span>
            {s.label}
          </Link>
        );
      })}
    </nav>
  );
}
