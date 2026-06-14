import fs from 'fs';
import path from 'path';
import { AFFILIATE_LINKS } from './affiliate-links';

export interface AffiliateMap {
  slug: string;
  primary_partner: string;
  cta_variant: 'A' | 'B';
  links: Record<string, string>;
}

export interface CTAConfig {
  href: string;
  text: string;
  partner: string;
}

export function getAffiliateMapPath(slug: string): string {
  return path.join(
    process.cwd(),
    '..',
    '..',
    'monetisation',
    'affiliate_map',
    `${slug}.json`,
  );
}

export function getAffiliateMap(slug: string): AffiliateMap | null {
  const mapPath = getAffiliateMapPath(slug);
  if (!fs.existsSync(mapPath)) return null;
  return JSON.parse(fs.readFileSync(mapPath, 'utf8')) as AffiliateMap;
}

export function resolveCTAUrl(map: AffiliateMap): string | null {
  const fromLinks = map.links[map.primary_partner];
  if (fromLinks && fromLinks.length > 0) return fromLinks;
  return AFFILIATE_LINKS[map.primary_partner] ?? null;
}

export function resolveCTAConfig(slug: string): CTAConfig | null {
  const map = getAffiliateMap(slug);
  if (!map) return null;
  const url = resolveCTAUrl(map);
  if (!url) return null;
  return {
    href: url,
    text: `Try ${map.primary_partner.replace(/_/g, ' ')} →`,
    partner: map.primary_partner,
  };
}
