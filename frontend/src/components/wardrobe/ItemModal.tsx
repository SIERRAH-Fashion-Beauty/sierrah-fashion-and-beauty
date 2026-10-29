import { useEffect, useRef, useState, type FormEvent } from 'react';
import { ImagePlus, Loader2, Trash2, Upload } from 'lucide-react';
import { CATEGORIES, OCCASIONS, STYLES } from '../../data/options';
import { useApp } from '../../context/AppContext';
import { fileToCompactDataUrl } from '../../lib/imageFile';
import type { WardrobeCategory, WardrobeItem } from '../../types';
import { CategoryIcon } from '../ui/icons';
import { Modal } from '../ui/Modal';
import { SmartImage } from '../ui/SmartImage';

interface Props {
  open: boolean;
  editing: WardrobeItem | null;
  initialImage?: string;
  onClose: () => void;
}

const OCCASION_TAGS = OCCASIONS.filter((o) => o.id !== 'custom').map((o) => ({ id: o.id as string, label: o.label }));
const STYLE_TAGS = STYLES.map((s) => ({ id: s.id as string, label: s.label }));
const KNOWN_TAGS = new Set([...OCCASION_TAGS, ...STYLE_TAGS].map((t) => t.id));
const COLOR_SUGGESTIONS = ['Black', 'White', 'Beige', 'Cream', 'Pink', 'Purple', 'Blue', 'Navy', 'Green', 'Red', 'Maroon', 'Yellow', 'Brown', 'Grey', 'Gold', 'Silver', 'Rose Gold', 'Multicolor'];

interface Form {
  name: string;
  category: WardrobeCategory;
  color: string;
  tags: string[];
  brand: string;
  notes: string;
  image: string;
}

const blank = (image = ''): Form => ({ name: '', category: 'tops', color: '', tags: [], brand: '', notes: '', image });

export function ItemModal({ open, editing, initialImage, onClose }: Props) {
  const { addItem, updateItem, showToast } = useApp();
  const [form, setForm] = useState<Form>(blank());
  const [errors, setErrors] = useState<{ name?: string; image?: string }>({});
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;
    setErrors({});
    setForm(
      editing
        ? {
            name: editing.name,
            category: editing.category,
            color: editing.color,
            tags: editing.tags,
            brand: editing.brand ?? '',
            notes: editing.notes ?? '',
            image: editing.image,
          }
        : blank(initialImage),
    );
  }, [open, editing, initialImage]);

  const set = <K extends keyof Form>(key: K, value: Form[K]) => setForm((f) => ({ ...f, [key]: value }));
  const toggleTag = (id: string) =>
    set('tags', form.tags.includes(id) ? form.tags.filter((t) => t !== id) : [...form.tags, id]);

  async function handleFile(file?: File | null) {
    if (!file) return;
    setUploading(true);
    setErrors((e) => ({ ...e, image: undefined }));
    try {
      set('image', await fileToCompactDataUrl(file));
    } catch (err) {
      setErrors((e) => ({ ...e, image: err instanceof Error ? err.message : 'Upload failed.' }));
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    const name = form.name.trim();
    if (!name) {
      setErrors({ name: 'Please give this item a name.' });
      return;
    }
    const payload = {
      name,
      category: form.category,
      color: form.color.trim() || 'Multicolor',
      tags: Array.from(new Set(form.tags.map((t) => t.toLowerCase()))),
      brand: form.brand.trim() || undefined,
      notes: form.notes.trim() || undefined,
      image: form.image,
    };
    if (editing) {
      updateItem({ ...editing, ...payload });
      showToast(`${name} updated.`);
    } else {
      addItem(payload);
      showToast(`${name} added to your wardrobe.`);
    }
    onClose();
  }

  const extraTags = form.tags.filter((t) => !KNOWN_TAGS.has(t));

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={editing ? 'Edit Item' : 'Add Item'}
      description="Add a photo and a few details so SIERRAH can style it."
      size="lg"
      footer={
        <>
          <button type="button" className="btn-outline" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" form="item-form" className="btn-primary" disabled={uploading}>
            {editing ? 'Save changes' : 'Add to wardrobe'}
          </button>
        </>
      }
    >
      <form id="item-form" onSubmit={submit} className="grid gap-6 md:grid-cols-[220px_1fr]" noValidate>
        {/* Photo */}
        <div>
          <span className="label">Photo</span>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              void handleFile(e.dataTransfer.files?.[0]);
            }}
            className={`relative overflow-hidden rounded-2xl border-2 border-dashed transition ${
              dragging ? 'border-rosebrown bg-blush/60' : 'border-dusty/70 bg-white/60'
            }`}
          >
            {form.image ? (
              <SmartImage src={form.image} alt="Item preview" className="aspect-square" category={form.category} />
            ) : (
              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                className="flex aspect-square w-full flex-col items-center justify-center gap-2 text-rosebrown"
              >
                <ImagePlus size={32} strokeWidth={1.3} />
                <span className="text-sm font-medium">Upload photo</span>
                <span className="px-4 text-center text-xs text-cocoa/50">Drag &amp; drop or click. JPG, PNG or WebP.</span>
              </button>
            )}
            {uploading && (
              <div className="absolute inset-0 flex items-center justify-center bg-cream/80" role="status">
                <Loader2 className="animate-spin text-rosebrown" />
              </div>
            )}
          </div>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="sr-only"
            aria-label="Upload clothing photo"
            onChange={(e) => void handleFile(e.target.files?.[0])}
          />
          <div className="mt-2 flex gap-2">
            <button type="button" className="btn-soft flex-1 px-3 py-2 text-xs" onClick={() => fileRef.current?.click()}>
              <Upload size={14} /> {form.image ? 'Replace' : 'Choose file'}
            </button>
            {form.image && (
              <button
                type="button"
                className="btn-ghost px-3 py-2 text-xs"
                onClick={() => set('image', '')}
                aria-label="Remove photo"
              >
                <Trash2 size={14} />
              </button>
            )}
          </div>
          {errors.image && (
            <p role="alert" className="mt-2 text-xs text-rosebrown">
              {errors.image}
            </p>
          )}
        </div>

        {/* Details */}
        <div className="space-y-5">
          <div>
            <label htmlFor="item-name" className="label">
              Name
            </label>
            <input
              id="item-name"
              data-autofocus
              className="input"
              value={form.name}
              maxLength={60}
              placeholder="e.g. Cotton Kurti"
              onChange={(e) => set('name', e.target.value)}
              aria-invalid={!!errors.name}
            />
            {errors.name && (
              <p role="alert" className="mt-1 text-xs text-rosebrown">
                {errors.name}
              </p>
            )}
          </div>

          <div>
            <span className="label">Category</span>
            <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Category">
              {CATEGORIES.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  role="radio"
                  aria-checked={form.category === c.id}
                  onClick={() => set('category', c.id)}
                  className={`pill ${form.category === c.id ? 'pill-active' : ''}`}
                >
                  <CategoryIcon category={c.id} size={16} /> {c.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="item-color" className="label">
                Colour
              </label>
              <input
                id="item-color"
                className="input"
                list="color-suggestions"
                value={form.color}
                placeholder="e.g. Lavender"
                onChange={(e) => set('color', e.target.value)}
              />
              <datalist id="color-suggestions">
                {COLOR_SUGGESTIONS.map((c) => (
                  <option key={c} value={c} />
                ))}
              </datalist>
            </div>
            <div>
              <label htmlFor="item-brand" className="label">
                Brand <span className="font-normal normal-case tracking-normal text-cocoa/40">(optional)</span>
              </label>
              <input id="item-brand" className="input" value={form.brand} maxLength={40} onChange={(e) => set('brand', e.target.value)} />
            </div>
          </div>

          <div>
            <span className="label">Best for</span>
            <div className="flex flex-wrap gap-2">
              {OCCASION_TAGS.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  aria-pressed={form.tags.includes(t.id)}
                  onClick={() => toggleTag(t.id)}
                  className={`pill px-3 py-1.5 text-xs ${form.tags.includes(t.id) ? 'pill-active' : ''}`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <span className="label">Style</span>
            <div className="flex flex-wrap gap-2">
              {STYLE_TAGS.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  aria-pressed={form.tags.includes(t.id)}
                  onClick={() => toggleTag(t.id)}
                  className={`pill px-3 py-1.5 text-xs ${form.tags.includes(t.id) ? 'pill-active' : ''}`}
                >
                  {t.label}
                </button>
              ))}
            </div>
            {extraTags.length > 0 && (
              <p className="mt-2 text-xs text-cocoa/50">Also tagged: {extraTags.join(', ')}</p>
            )}
          </div>

          <div>
            <label htmlFor="item-notes" className="label">
              Notes <span className="font-normal normal-case tracking-normal text-cocoa/40">(optional)</span>
            </label>
            <textarea
              id="item-notes"
              rows={2}
              maxLength={200}
              className="input resize-none"
              value={form.notes}
              placeholder="Fabric, fit or anything you want to remember"
              onChange={(e) => set('notes', e.target.value)}
            />
          </div>
        </div>
      </form>
    </Modal>
  );
}
