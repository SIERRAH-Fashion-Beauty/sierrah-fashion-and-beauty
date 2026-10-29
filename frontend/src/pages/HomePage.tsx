import { Link } from 'react-router-dom';
import { ArrowRight, Lightbulb, Shirt, Handbag } from 'lucide-react';
import { Blossom, Divider, FloralBranch } from '../components/ui/Floral';
import { PerfumeIcon } from '../components/ui/icons';
import { SmartImage } from '../components/ui/SmartImage';

const QUICK_LINKS = [
  { label: 'Fashion', to: '/style', Icon: Shirt },
  { label: 'Beauty', to: '/wardrobe?category=beauty', Icon: PerfumeIcon },
  { label: 'Accessories', to: '/wardrobe?category=bags', Icon: Handbag },
  { label: 'Styling Tips', to: '/preview', Icon: Lightbulb },
];

const STEPS = [
  { n: '01', title: 'Add what you own', text: 'Upload photos of your clothes, shoes, bags, jewellery and beauty staples.' },
  { n: '02', title: 'Pick an occasion', text: 'College, office, wedding, travel or something entirely your own.' },
  { n: '03', title: 'Get your look', text: 'A complete, coordinated outfit, makeup and hairstyle from your own wardrobe.' },
];

export function HomePage() {
  return (
    <div className="space-y-12">
      {/* Hero */}
      <section
        aria-labelledby="hero-title"
        className="relative isolate flex flex-col overflow-hidden rounded-3xl bg-gradient-to-br from-blush via-[#F9E6E0] to-cream shadow-soft lg:block lg:min-h-[620px]"
      >
        {/* Model portrait: right half on desktop, full-bleed backdrop on mobile */}
        <div className="relative h-[400px] sm:h-[500px] lg:absolute lg:inset-0 lg:left-auto lg:h-auto lg:w-[62%]">
          <SmartImage
            src="/images/models/hero.jpg"
            alt="Elegant woman in a flowing blush-pink saree"
            eager
            position="50% 18%"
            className="hero-mask h-full w-full"
          />
        </div>

        <FloralBranch className="pointer-events-none absolute -left-14 bottom-0 hidden h-72 text-rosegold/30 lg:block" />

        <div className="relative z-10 -mt-16 flex flex-col px-6 pb-10 sm:px-12 lg:mt-0 lg:min-h-[620px] lg:max-w-[52%] lg:justify-center lg:py-14">
          <Blossom className="mb-3 h-7 w-7 text-rosegold" />
          <h1 id="hero-title" className="font-serif text-6xl font-normal tracking-[0.16em] text-rosebrown sm:text-7xl lg:text-[5.5rem] lg:leading-none">
            SIERRAH
          </h1>
          <p className="mt-2 flex items-center gap-3 font-serif text-lg italic tracking-wide text-rosegold sm:text-xl">
            <span className="h-px w-8 bg-rosegold/60" /> Fashion &amp; Beauty <span className="h-px w-8 bg-rosegold/60" />
          </p>

          <p className="mt-7 font-serif text-2xl font-medium text-cocoa sm:text-3xl">Your Style. Your Beauty. Your Way.</p>
          <p className="mt-3 max-w-sm text-sm leading-relaxed text-cocoa/75 sm:text-base">
            Use what you have. Style it your way.
            <br />
            Get personalized looks for every occasion.
          </p>

          <div className="mt-7">
            <Link to="/style" className="btn-primary px-8 py-3.5 text-base">
              Start Styling <ArrowRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      {/* Circular quick links */}
      <section aria-label="Explore" className="-mt-2">
        <ul className="mx-auto grid max-w-xl grid-cols-4 gap-3 sm:gap-6">
          {QUICK_LINKS.map(({ label, to, Icon }) => (
            <li key={label}>
              <Link to={to} className="group flex flex-col items-center gap-2.5 text-center">
                <span className="flex h-16 w-16 items-center justify-center rounded-full border border-dusty/50 bg-white/80 text-rosebrown shadow-card transition duration-300 group-hover:-translate-y-1 group-hover:bg-blush group-hover:shadow-soft sm:h-[72px] sm:w-[72px]">
                  <Icon size={28} strokeWidth={1.3} />
                </span>
                <span className="text-xs font-medium text-cocoa/80 sm:text-sm">{label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      {/* How it works */}
      <section aria-labelledby="how-title" className="space-y-8">
        <div className="text-center">
          <Divider className="justify-center" />
          <h2 id="how-title" className="mt-3 font-serif text-3xl text-cocoa sm:text-4xl">
            Style it better, not buy more
          </h2>
          <p className="mx-auto mt-2 max-w-lg text-sm text-cocoa/65">
            Most of us already own enough. SIERRAH helps you see it differently, and only suggests something new when a look truly needs it.
          </p>
        </div>
        <ol className="grid gap-4 md:grid-cols-3">
          {STEPS.map((s) => (
            <li key={s.n} className="card relative overflow-hidden p-6">
              <span className="font-serif text-5xl text-blush">{s.n}</span>
              <h3 className="mt-1 font-serif text-2xl text-rosebrown">{s.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-cocoa/70">{s.text}</p>
            </li>
          ))}
        </ol>
        <div className="flex justify-center">
          <Link to="/wardrobe" className="btn-outline">
            Open My Wardrobe
          </Link>
        </div>
      </section>
    </div>
  );
}
