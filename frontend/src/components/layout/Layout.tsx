import { useEffect } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import { Bookmark, Home, Plus, Shirt, Sparkles } from 'lucide-react';
import { Blossom } from '../ui/Floral';
import { OfflineBanner, ToastHost } from '../ui/Feedback';
import { SmartImage } from '../ui/SmartImage';
import { ItemModal } from '../wardrobe/ItemModal';
import { useApp } from '../../context/AppContext';

const STYLE_FLOW = ['/style', '/personalize', '/look', '/preview', '/shopping'];

const NAV = [
  { to: '/', label: 'Home', end: true },
  { to: '/wardrobe', label: 'My Wardrobe' },
  { to: '/style', label: 'Style', match: STYLE_FLOW },
  { to: '/saved', label: 'Saved Looks' },
];

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <Link to="/" className="group flex items-center gap-3" aria-label="SIERRAH Fashion & Beauty home">
      <span className="relative block h-10 w-10 shrink-0 overflow-hidden rounded-full border border-dusty/70 shadow-card sm:h-11 sm:w-11">
        <img src="/brand/logo.png" alt="" className="h-full w-full scale-[1.15] object-cover" />
      </span>
      <span className="leading-none">
        <span className="block font-serif text-2xl font-medium tracking-[0.22em] text-rosebrown sm:text-[1.65rem]">SIERRAH</span>
        {!compact && (
          <span className="mt-1 flex items-center gap-1.5 font-serif text-[11px] italic tracking-wider text-rosegold">
            <Blossom className="h-2.5 w-2.5" /> Fashion &amp; Beauty
          </span>
        )}
      </span>
    </Link>
  );
}

function Header() {
  const { pathname } = useLocation();
  return (
    <header className="sticky top-0 z-40 border-b border-blush/70 bg-cream/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-6 px-4 sm:h-[72px] sm:px-6 lg:px-8">
        <Logo />
        <nav className="hidden items-center gap-1 md:flex" aria-label="Primary">
          {NAV.map((n) => {
            const active = n.match ? n.match.includes(pathname) : n.end ? pathname === n.to : pathname.startsWith(n.to);
            return (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                aria-current={active ? 'page' : undefined}
                className={`relative rounded-full px-4 py-2 text-sm transition ${
                  active ? 'bg-blush/80 font-medium text-rosebrown' : 'text-cocoa/75 hover:bg-blush/40 hover:text-rosebrown'
                }`}
              >
                {n.label}
              </NavLink>
            );
          })}
        </nav>
        <Link
          to="/profile"
          aria-label="Open profile"
          className="h-10 w-10 shrink-0 overflow-hidden rounded-full border-2 border-white shadow-card ring-1 ring-dusty/60 transition hover:ring-rosebrown"
        >
          <SmartImage src="/images/models/hero.jpg" alt="Your profile" position="50% 12%" className="h-full w-full" imgClassName="scale-[2.2] origin-[48%_14%]" eager />
        </Link>
      </div>
    </header>
  );
}

function MobileNav() {
  const { pathname } = useLocation();
  const { openItemModal } = useApp();
  const item = (to: string, label: string, Icon: typeof Home, active: boolean) => (
    <Link
      to={to}
      aria-current={active ? 'page' : undefined}
      className={`flex flex-1 flex-col items-center gap-0.5 py-1.5 text-[11px] ${active ? 'text-rosebrown' : 'text-cocoa/55'}`}
    >
      <Icon size={22} strokeWidth={active ? 1.9 : 1.5} />
      {label}
    </Link>
  );
  return (
    <nav
      aria-label="Mobile"
      className="pb-safe fixed inset-x-0 bottom-0 z-40 border-t border-blush bg-cream/95 backdrop-blur-md md:hidden"
    >
      <div className="mx-auto flex max-w-md items-end px-2">
        {item('/', 'Home', Home, pathname === '/')}
        {item('/wardrobe', 'Wardrobe', Shirt, pathname === '/wardrobe')}
        <div className="flex flex-1 justify-center">
          <button
            type="button"
            onClick={() => openItemModal()}
            aria-label="Add wardrobe item"
            className="-mt-5 flex h-14 w-14 items-center justify-center rounded-full bg-rosebrown text-cream shadow-lift ring-4 ring-cream transition active:scale-95"
          >
            <Plus size={26} strokeWidth={1.8} />
          </button>
        </div>
        {item('/style', 'Style', Sparkles, STYLE_FLOW.includes(pathname))}
        {item('/saved', 'Saved', Bookmark, pathname === '/saved')}
      </div>
    </nav>
  );
}

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'auto' });
  }, [pathname]);
  return null;
}

export function Layout() {
  const { itemModal, closeItemModal } = useApp();
  return (
    <div className="flex min-h-screen flex-col">
      <ScrollToTop />
      <Header />
      <OfflineBanner />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 pb-28 pt-6 sm:px-6 md:pb-14 lg:px-8">
        <Outlet />
      </main>
      <footer className="hidden border-t border-blush/70 py-6 text-center text-xs text-cocoa/50 md:block">
        <span className="font-serif text-sm tracking-[0.2em] text-rosebrown">SIERRAH</span> · Your Style. Your Beauty. Your Way.
      </footer>
      <MobileNav />
      <ItemModal
        open={itemModal.open}
        editing={itemModal.editing}
        initialImage={itemModal.initialImage}
        onClose={closeItemModal}
      />
      <ToastHost />
    </div>
  );
}
