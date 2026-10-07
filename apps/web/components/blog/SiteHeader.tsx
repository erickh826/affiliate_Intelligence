import Link from 'next/link';
import { getBrandName, getPrimaryCta, primaryNav } from '../../lib/site-nav';
import MobileNav from './MobileNav';

function NavLinks({ className }: { className: string }) {
  return (
    <>
      {primaryNav.map((item) => (
        <Link key={item.href} href={item.href} className={className}>
          {item.label}
        </Link>
      ))}
    </>
  );
}

export default function SiteHeader() {
  const brand = getBrandName();
  const cta = getPrimaryCta();

  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background">
      <div className="layout-container flex items-center justify-between gap-4 py-4">
        <Link
          href="/"
          className="truncate text-[18px] font-bold tracking-[-0.02em] text-text hover:text-accent"
        >
          {brand}
          <span className="text-accent">.</span>
        </Link>
        <nav
          className="hidden items-center gap-6 text-sm text-secondary md:flex"
          aria-label="Primary"
        >
          <NavLinks className="hover:text-text" />
        </nav>
        <div className="flex shrink-0 items-center gap-3">
          <MobileNav />
          <Link
            href={cta.href}
            className="inline-flex items-center justify-center rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white hover:text-white hover:brightness-105 motion-reduce:transition-none"
          >
            {cta.label}
          </Link>
        </div>
      </div>
    </header>
  );
}
