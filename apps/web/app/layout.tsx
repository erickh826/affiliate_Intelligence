import type { Metadata } from 'next';
import Link from 'next/link';
import ThemeToggle from '../components/ThemeToggle';
import { getSiteName } from '../lib/site';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000',
  ),
  title: getSiteName(),
  description: 'Programmatic SEO content system',
  alternates: {
    canonical: '/',
  },
  openGraph: {
    title: getSiteName(),
    description: 'Programmatic SEO content system',
    images: [
      {
        url: '/og-default.svg',
        width: 1200,
        height: 630,
      },
    ],
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="bg-background text-text min-h-screen">
        <header className="border-b border-surface py-4">
          <div className="layout-container flex justify-between items-center">
            <Link
              href="/"
              className="text-2xl font-display font-bold text-accent"
            >
              {getSiteName()}
            </Link>
            <div className="flex items-center gap-5 text-sm">
              <nav className="hidden sm:flex items-center gap-4 text-gray-400">
                <Link
                  href="/about"
                  className="hover:text-accent transition-colors"
                >
                  About
                </Link>
                <Link
                  href="/contact"
                  className="hover:text-accent transition-colors"
                >
                  Contact
                </Link>
                <Link
                  href="/disclaimer"
                  className="hover:text-accent transition-colors"
                >
                  Disclaimer
                </Link>
              </nav>
              <ThemeToggle />
            </div>
          </div>
        </header>
        <main>{children}</main>
        <footer className="border-t border-surface py-8 mt-12">
          <div className="layout-container text-center text-sm text-gray-500 space-y-3">
            <p>&copy; 2026 Affiliate Intelligence. All rights reserved.</p>
            <div className="flex justify-center gap-4">
              <Link
                href="/privacy-policy"
                className="hover:text-accent transition-colors"
              >
                Privacy Policy
              </Link>
              <Link
                href="/contact"
                className="hover:text-accent transition-colors"
              >
                Contact
              </Link>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
