import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Cloud, CloudOff, Loader2, RefreshCw, RotateCcw } from 'lucide-react';
import { ConfirmDialog } from '../components/ui/Modal';
import { SmartImage } from '../components/ui/SmartImage';
import { useApp } from '../context/AppContext';
import { API_BASE_URL } from '../services/api';

export function ProfilePage() {
  const { wardrobe, saved, apiStatus, retryConnection, resetDemo } = useApp();
  const [confirming, setConfirming] = useState(false);

  const stats = [
    { label: 'Wardrobe items', value: wardrobe.length, to: '/wardrobe' },
    { label: 'Saved looks', value: saved.length, to: '/saved' },
    { label: 'Favorites', value: saved.filter((s) => s.favorite).length, to: '/saved' },
  ];

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="card flex flex-col items-center gap-4 px-6 py-10 text-center">
        <SmartImage src="/images/models/hero.jpg" alt="Profile" position="50% 12%" className="h-24 w-24 rounded-full border-4 border-white shadow-soft" imgClassName="scale-[2.2] origin-[48%_14%]" eager />
        <div>
          <h1 className="font-serif text-3xl text-cocoa">Guest Stylist</h1>
          <p className="text-sm text-cocoa/55">Your Style. Your Beauty. Your Way.</p>
        </div>
        <div className="mt-2 grid w-full grid-cols-3 gap-3">
          {stats.map((s) => (
            <Link key={s.label} to={s.to} className="rounded-2xl bg-blush/40 px-2 py-4 transition hover:bg-blush/70">
              <p className="font-serif text-3xl text-rosebrown">{s.value}</p>
              <p className="text-[11px] text-cocoa/60">{s.label}</p>
            </Link>
          ))}
        </div>
      </div>

      <section className="card space-y-3 p-6" aria-labelledby="conn-title">
        <h2 id="conn-title" className="font-serif text-xl text-cocoa">
          Connection
        </h2>
        <div className="flex flex-wrap items-center gap-3 text-sm">
          {apiStatus === 'checking' ? (
            <Loader2 size={18} className="animate-spin text-rosebrown" />
          ) : apiStatus === 'online' ? (
            <Cloud size={18} className="text-[#4B6B45]" />
          ) : (
            <CloudOff size={18} className="text-rosebrown" />
          )}
          <span>
            {apiStatus === 'online' && 'Connected. Wardrobe and saved looks sync with the server.'}
            {apiStatus === 'offline' && 'Server not reachable. Data is saved on this device only.'}
            {apiStatus === 'checking' && 'Checking server…'}
          </span>
          <button type="button" onClick={retryConnection} className="btn-soft ml-auto px-4 py-1.5 text-xs">
            <RefreshCw size={13} /> Recheck
          </button>
        </div>
        <p className="text-xs text-cocoa/45">
          API: <code className="rounded bg-blush/50 px-1.5 py-0.5">{API_BASE_URL}</code>
        </p>
      </section>

      <section className="card space-y-3 p-6" aria-labelledby="data-title">
        <h2 id="data-title" className="font-serif text-xl text-cocoa">
          Demo data
        </h2>
        <p className="text-sm text-cocoa/65">Restore the sample wardrobe and clear your saved looks and preferences.</p>
        <button type="button" className="btn-outline" onClick={() => setConfirming(true)}>
          <RotateCcw size={16} /> Reset demo data
        </button>
      </section>

      <ConfirmDialog
        open={confirming}
        title="Reset demo data?"
        message="This replaces your wardrobe with the sample items and deletes all saved looks."
        confirmLabel="Reset"
        onCancel={() => setConfirming(false)}
        onConfirm={() => {
          resetDemo();
          setConfirming(false);
        }}
      />
    </div>
  );
}
