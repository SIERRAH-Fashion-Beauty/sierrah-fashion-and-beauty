import type { ReactNode } from 'react';
import { AlertCircle, CheckCircle2, Info, WifiOff, RefreshCw } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { FloralBranch } from './Floral';

export function EmptyState({
  title,
  message,
  action,
  icon,
}: {
  title: string;
  message: string;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="card relative flex flex-col items-center overflow-hidden px-6 py-14 text-center">
      <FloralBranch className="pointer-events-none absolute -left-4 bottom-0 h-44 text-dusty/50" />
      <FloralBranch flip className="pointer-events-none absolute -right-4 bottom-0 h-44 text-dusty/50" />
      {icon && <div className="relative mb-4 rounded-full bg-blush/70 p-4 text-rosebrown">{icon}</div>}
      <h3 className="relative font-serif text-2xl text-cocoa">{title}</h3>
      <p className="relative mt-2 max-w-sm text-sm leading-relaxed text-cocoa/65">{message}</p>
      {action && <div className="relative mt-6 flex flex-wrap justify-center gap-3">{action}</div>}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="card flex flex-col items-center px-6 py-12 text-center">
      <div className="mb-3 rounded-full bg-blush/70 p-3 text-rosebrown">
        <AlertCircle size={26} strokeWidth={1.5} />
      </div>
      <h3 className="font-serif text-2xl">Something went wrong</h3>
      <p className="mt-1 max-w-sm text-sm text-cocoa/65">{message}</p>
      {onRetry && (
        <button type="button" className="btn-primary mt-5" onClick={onRetry}>
          <RefreshCw size={16} /> Try again
        </button>
      )}
    </div>
  );
}

export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`shimmer rounded-2xl ${className}`} aria-hidden="true" />;
}

export function GridSkeleton({ count = 10, aspect = 'aspect-square' }: { count?: number; aspect?: string }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5" role="status" aria-label="Loading">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className={aspect} />
          <Skeleton className="h-4 w-2/3" />
        </div>
      ))}
    </div>
  );
}

export function ToastHost() {
  const { toast } = useApp();
  if (!toast) return null;
  const Icon = toast.tone === 'success' ? CheckCircle2 : toast.tone === 'error' ? AlertCircle : Info;
  const tone =
    toast.tone === 'error'
      ? 'border-rosebrown/50 bg-white text-rosebrown'
      : 'border-dusty/60 bg-white text-cocoa';
  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-24 z-[120] flex justify-center px-4 md:bottom-8" aria-live="polite">
      <div
        key={toast.id}
        role="status"
        className={`pointer-events-auto flex max-w-md animate-fade-up items-center gap-3 rounded-full border px-5 py-3 text-sm shadow-lift ${tone}`}
      >
        <Icon size={18} strokeWidth={1.7} className="shrink-0 text-rosebrown" />
        <span>{toast.message}</span>
      </div>
    </div>
  );
}

/** Slim banner shown when the FastAPI backend can't be reached. */
export function OfflineBanner() {
  const { apiStatus, retryConnection } = useApp();
  if (apiStatus !== 'offline') return null;
  return (
    <div className="border-b border-dusty/40 bg-blush/60 text-xs text-rosebrown">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-x-3 gap-y-1 px-4 py-2 text-center">
        <WifiOff size={14} />
        <span>Backend not connected. SIERRAH is running in local demo mode and saving to this device.</span>
        <button type="button" onClick={retryConnection} className="font-semibold underline underline-offset-2 hover:text-cocoa">
          Retry
        </button>
      </div>
    </div>
  );
}
