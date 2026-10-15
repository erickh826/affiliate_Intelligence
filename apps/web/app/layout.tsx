import type { Metadata } from 'next';
import localFont from 'next/font/local';
import GoogleAnalytics from '../components/GoogleAnalytics';
import SiteFooter from '../components/blog/SiteFooter';
import SiteHeader from '../components/blog/SiteHeader';
import { getSiteName, getSiteUrl } from '../lib/site';
import './globals.css';

const inter = localFont({
  src: [
    {
      path: './fonts/inter-latin-400-normal.woff2',
      weight: '400',
      style: 'normal',
    },
    {
      path: './fonts/inter-latin-600-normal.woff2',
      weight: '600',
      style: 'normal',
    },
    {
      path: './fonts/inter-latin-700-normal.woff2',
      weight: '700',
      style: 'normal',
    },
  ],
  variable: '--font-inter',
  display: 'swap',
});

export const metadata: Metadata = {
  metadataBase: new URL(getSiteUrl()),
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
    <html
      lang="en"
      className={`${inter.variable} scroll-smooth motion-reduce:scroll-auto`}
    >
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin=""
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-background font-body text-text">
        <SiteHeader />
        <main>{children}</main>
        <SiteFooter />
        <GoogleAnalytics />
      </body>
    </html>
  );
}
