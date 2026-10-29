import { Pencil, X } from 'lucide-react';
import type { WardrobeItem } from '../../types';
import { SmartImage } from '../ui/SmartImage';

interface Props {
  item: WardrobeItem;
  onEdit: (item: WardrobeItem) => void;
  onRemove: (item: WardrobeItem) => void;
}

export function ItemCard({ item, onEdit, onRemove }: Props) {
  return (
    <article className="group relative animate-fade-up">
      <div className="card overflow-hidden transition duration-300 group-hover:-translate-y-0.5 group-hover:shadow-soft">
        <button
          type="button"
          onClick={() => onEdit(item)}
          className="block w-full text-left"
          aria-label={`Edit ${item.name}`}
        >
          <SmartImage src={item.image} alt={item.name} category={item.category} className="aspect-square" imgClassName="transition duration-500 group-hover:scale-105" />
        </button>
        <div className="flex items-center justify-between gap-2 px-3 py-2.5">
          <div className="min-w-0">
            <h3 className="truncate font-sans text-sm font-medium text-cocoa">{item.name}</h3>
            <p className="truncate text-[11px] text-cocoa/50">{item.color}</p>
          </div>
          <button
            type="button"
            onClick={() => onEdit(item)}
            aria-label={`Edit ${item.name}`}
            className="rounded-full p-1.5 text-rosebrown/70 transition hover:bg-blush/60 hover:text-rosebrown md:opacity-0 md:group-hover:opacity-100 md:focus-visible:opacity-100"
          >
            <Pencil size={14} />
          </button>
        </div>
      </div>
      <button
        type="button"
        onClick={() => onRemove(item)}
        aria-label={`Remove ${item.name}`}
        className="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full bg-white/90 text-rosebrown shadow-card transition hover:bg-rosebrown hover:text-cream"
      >
        <X size={13} strokeWidth={2} />
      </button>
    </article>
  );
}
