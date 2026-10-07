import Link from 'next/link';
import { footerColumns, footerLegal, getBrandName } from '../../lib/site-nav';

export default function SiteFooter() {
  const year = new Date().getFullYear();
  const brand = getBrandName();

  return (
    <footer className="mt-8 bg-surface pb-6 pt-12">
      <div className="layout-container">
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-5">
          {footerColumns.map((column) => (
            <div key={column.heading}>
              <h2 className="mb-3 text-[13px] font-bold tracking-[0.02em]">
                {column.heading}
              </h2>
              <ul className="flex flex-col gap-2">
                {column.links.map((link) => (
                  <li key={`${column.heading}-${link.label}`}>
                    <Link
                      href={link.href}
                      className="text-sm text-secondary hover:text-text"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-8 flex flex-wrap items-center justify-between gap-4 border-t border-border pt-4 text-[13px] text-secondary">
          <nav aria-label="Legal" className="flex flex-wrap gap-4">
            {footerLegal.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="hover:text-text"
              >
                {link.label}
              </Link>
            ))}
          </nav>
          <p>
            {brand} © {year}
          </p>
        </div>
      </div>
    </footer>
  );
}
