import fs from 'fs';
import path from 'path';
import {
  type AffiliateProgram,
  contentRendersAffiliateCta,
  getProgram,
  isProgramActive,
  loadAffiliateConfig,
} from './affiliates';

export interface AffiliateMap {
  slug: string;
  primary_partner: string;
  cta_variant: 'A' | 'B';
  links: Record<string, string>;
  cta_text?: string;
  disclosure?: string;
}

export interface CTAConfig {
  href: string;
  text: string;
  partner: string;
  promoCode?: string;
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

export function ctaFromProgram(
  program: AffiliateProgram | null,
): CTAConfig | null {
  if (!isProgramActive(program)) return null;
  const promoCode = program.promo_code.trim();
  return {
    href: program.url.trim(),
    text: program.anchor.trim() || `Try ${program.name} →`,
    partner: program.name.trim() || program.id,
    ...(promoCode ? { promoCode } : {}),
  };
}

export function resolveCTAConfig(
  slug: string,
  partnerId?: string | null,
  programs: AffiliateProgram[] = loadAffiliateConfig().programs,
  affiliateMap?: AffiliateMap | null,
): CTAConfig | null {
  const map = affiliateMap === undefined ? getAffiliateMap(slug) : affiliateMap;
  const id = (partnerId ?? '').trim() || map?.primary_partner || '';
  const config = ctaFromProgram(getProgram(id, programs));
  if (!config) return null;
  const ctaText = map?.cta_text?.trim();
  if (!ctaText) return config;
  return { ...config, text: ctaText };
}

export function shouldShowAffiliateDisclosure(
  cta: CTAConfig | null,
  content: string,
  programs?: AffiliateProgram[],
): boolean {
  if (cta) return true;
  return contentRendersAffiliateCta(content, programs);
}
