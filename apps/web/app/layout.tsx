import type { Metadata } from 'next';
import { Inter, Instrument_Serif } from 'next/font/google';
import './globals.css';

const inter = Inter({ 
  subsets: ['latin'], 
  variable: '--font-inter',
  display: 'swap',
});

const instrumentSerif = Instrument_Serif({ 
  subsets: ['latin'], 
  weight: '400', 
  variable: '--font-instrument',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Affiliate Intelligence',
  description: 'Programmatic SEO content system',
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} ${instrumentSerif.variable} dark`}>
      <body className="bg-background text-text min-h-screen">
        <header className="border-b border-surface py-4">
          <div className="layout-container flex justify-between items-center">
            <a href="/" className="text-2xl font-display font-bold text-accent">
              Affiliate Intelligence
            </a>
          </div>
        </header>
        <main>
          {children}
        </main>
        <footer className="border-t border-surface py-8 mt-12">
          <div className="layout-container text-center text-sm text-gray-500">
            <p>&copy; 2026 Affiliate Intelligence. All rights reserved.</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
