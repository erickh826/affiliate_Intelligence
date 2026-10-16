import fs from 'fs';
import path from 'path';

export interface AffiliateProgram {
  id: string;
  name: string;
  category: string;
  url: string;
  promo_code: string;
  anchor: string;
  enabled: boolean;
}

export interface AffiliateConfig {
  programs: AffiliateProgram[];
}

const AFFILIATE_TAG =
  /<AffiliateCTA\b[^>]*\bpartner=["']([^"']+)["'][^>]*\/?>/g;

export function affiliatesConfigPath(): string {
  return path.join(
    process.cwd(),
    '..',
    '..',
    'monetisation',
    'affiliates.json',
  );
}

export function loadAffiliateConfig(
  configPath: string = affiliatesConfigPath(),
): AffiliateConfig {
  if (!fs.existsSync(configPath)) return { programs: [] };
  const raw: unknown = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  if (!raw || typeof raw !== 'object' || !('programs' in raw)) {
    return { programs: [] };
  }
  const programs = (raw as { programs: unknown }).programs;
  if (!Array.isArray(programs)) return { programs: [] };
  return {
    programs: programs.filter(isAffiliateProgram),
  };
}

function isAffiliateProgram(value: unknown): value is AffiliateProgram {
  if (!value || typeof value !== 'object') return false;
  const program = value as Record<string, unknown>;
  return (
    typeof program.id === 'string' &&
    typeof program.name === 'string' &&
    typeof program.category === 'string' &&
    typeof program.url === 'string' &&
    typeof program.promo_code === 'string' &&
    typeof program.anchor === 'string' &&
    typeof program.enabled === 'boolean'
  );
}

export function getProgram(
  id: string | null | undefined,
  programs: AffiliateProgram[] = loadAffiliateConfig().programs,
): AffiliateProgram | null {
  const key = (id ?? '').trim();
  if (!key) return null;
  return programs.find((program) => program.id === key) ?? null;
}

export function isProgramActive(
  program: AffiliateProgram | null,
): program is AffiliateProgram {
  if (!program || !program.enabled) return false;
  return (
    program.url.startsWith('https://') || program.url.startsWith('http://')
  );
}

export function affiliatePartnerIdsInContent(content: string): string[] {
  return [...content.matchAll(AFFILIATE_TAG)].map((match) => match[1]);
}

export function contentRendersAffiliateCta(
  content: string,
  programs?: AffiliateProgram[],
): boolean {
  const list = programs ?? loadAffiliateConfig().programs;
  return affiliatePartnerIdsInContent(content).some((id) =>
    isProgramActive(getProgram(id, list)),
  );
}
