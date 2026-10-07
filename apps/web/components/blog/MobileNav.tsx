'use client';

import Link from 'next/link';
import { useState } from 'react';
import { primaryNav } from '../../lib/site-nav';

export default function MobileNav() {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative md:hidden">
      <button
        type="button"
        className="rounded-full border border-border px-3 py-2 text-sm font-semibold text-text"
        aria-expanded={open}
        aria-controls="mobile-nav"
        onClick={() => setOpen((value) => !value)}
      >
        Menu
      </button>
      {open ? (
        <nav
          id="mobile-nav"
          aria-label="Primary"
          className="absolute right-0 z-30 mt-2 flex min-w-40 flex-col gap-3 rounded-lg border border-border bg-background p-4"
        >
          {primaryNav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-sm text-secondary hover:text-text"
              onClick={() => setOpen(false)}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      ) : null}
    </div>
  );
}
