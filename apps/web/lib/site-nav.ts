import { getSiteName } from './site';

export interface NavLink {
  label: string;
  href: string;
}

const ACRONYMS: Record<string, string> = {
  ai: 'AI',
};

export function formatBrandName(name: string): string {
  return name
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => {
      const acronym = ACRONYMS[part.toLowerCase()];
      if (acronym) return acronym;
      return part.charAt(0).toUpperCase() + part.slice(1);
    })
    .join(' ');
}

export function getBrandName(): string {
  return formatBrandName(getSiteName()) || 'Shadona';
}

export function getPrimaryCta(): NavLink {
  const brand = getBrandName().split(' ')[0] || 'Shadona';
  return {
    label: `Try ${brand}`,
    href: '/contact',
  };
}

export const primaryNav: NavLink[] = [
  { label: 'Articles', href: '/#popular' },
  { label: 'Topics', href: '/#topics' },
  { label: 'About', href: '/about' },
  { label: 'Contact', href: '/contact' },
];

export const footerColumns: { heading: string; links: NavLink[] }[] = [
  {
    heading: 'Product',
    links: [
      { label: 'Overview', href: '/' },
      { label: 'Articles', href: '/#popular' },
    ],
  },
  {
    heading: 'Pricing',
    links: [{ label: 'Free to read', href: '/#popular' }],
  },
  {
    heading: 'Company',
    links: [
      { label: 'About', href: '/about' },
      { label: 'Contact', href: '/contact' },
    ],
  },
  {
    heading: 'Support',
    links: [
      { label: 'Contact', href: '/contact' },
      { label: 'Disclaimer', href: '/disclaimer' },
    ],
  },
  {
    heading: 'Editorial',
    links: [
      { label: 'All articles', href: '/#popular' },
      { label: 'Topics', href: '/#topics' },
    ],
  },
];

export const footerLegal: NavLink[] = [
  { label: 'Privacy', href: '/privacy-policy' },
  { label: 'Disclaimer', href: '/disclaimer' },
  { label: 'Cookies', href: '/privacy-policy#cookies' },
];
