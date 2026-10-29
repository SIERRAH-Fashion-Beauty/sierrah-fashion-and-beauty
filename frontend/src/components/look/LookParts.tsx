import type { ReactNode } from 'react';
import { Gem, Handbag, Scissors, Shirt } from 'lucide-react';
import { HeelIcon, LipstickIcon } from '../ui/icons';
import { budgetLabel, styleLabel } from '../../data/options';
import type { Look, LookItem, LookSlot } from '../../types';

export const SLOT_META: Record<LookSlot, { label: string; icon: (size: number) => ReactNode }> = {
  outfit: { label: 'Outfit', icon: (s) => <Shirt size={s} strokeWidth={1.4} /> },
  footwear: { label: 'Footwear', icon: (s) => <HeelIcon size={s} strokeWidth={1.4} /> },
  bag: { label: 'Bag', icon: (s) => <Handbag size={s} strokeWidth={1.4} /> },
  jewellery: { label: 'Jewellery', icon: (s) => <Gem size={s} strokeWidth={1.4} /> },
  makeup: { label: 'Makeup', icon: (s) => <LipstickIcon size={s} strokeWidth={1.4} /> },
  hairstyle: { label: 'Hairstyle', icon: (s) => <Scissors size={s} strokeWidth={1.4} /> },
};

export const SLOT_ORDER: LookSlot[] = ['outfit', 'footwear', 'bag', 'jewellery', 'makeup', 'hairstyle'];

export const bySlot = (look: Look, slot: LookSlot): LookItem | undefined => look.items.find((i) => i.slot === slot);

const SOURCE_STYLES: Record<LookItem['source'], { label: string; cls: string }> = {
  wardrobe: { label: 'From your wardrobe', cls: 'bg-[#EDF3EA] text-[#4B6B45]' },
  suggested: { label: 'Suggested purchase', cls: 'bg-[#FBE9D9] text-[#9A5B2E]' },
  tip: { label: 'Styling tip', cls: 'bg-blush/70 text-rosebrown' },
};

export function SourceBadge({ source, short = false }: { source: LookItem['source']; short?: boolean }) {
  const s = SOURCE_STYLES[source];
  return (
    <span className={`inline-flex shrink-0 items-center rounded-full px-2.5 py-0.5 text-[11px] font-medium ${s.cls}`}>
      {short && source === 'wardrobe' ? 'Yours' : short && source === 'suggested' ? 'Suggested' : s.label}
    </span>
  );
}

/** Subtitle without the "From your wardrobe" boilerplate, since the badge already says it. */
export const itemDetail = (item: LookItem): string =>
  item.subtitle === 'From your wardrobe' ? '' : item.subtitle.replace(/^Suggested · /, '');

export function LookChips({ look }: { look: Look }) {
  const p = look.preferences;
  const chips = [
    look.occasionLabel,
    styleLabel(p.style),
    budgetLabel(p.budget),
    ...p.colors,
    ...p.traits.map((t) => t.charAt(0).toUpperCase() + t.slice(1)),
  ].filter(Boolean);
  return (
    <ul className="flex flex-wrap gap-2" aria-label="Look preferences">
      {chips.map((c, i) => (
        <li
          key={`${c}-${i}`}
          className={`rounded-full border px-3.5 py-1 text-xs font-medium ${
            i === 0 ? 'border-rosebrown bg-rosebrown text-cream' : 'border-dusty/60 bg-white/70 text-rosebrown'
          }`}
        >
          {c}
        </li>
      ))}
    </ul>
  );
}
