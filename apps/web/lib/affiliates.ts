import fs from 'fs';
import path from 'path';

export type ProgramType = 'affiliate' | 'referral';

export interface AffiliateProgram {
  id: string;
  name: string;
  category: string;
  url: string;
  promo_code: string;
  anchor: string;
  enabled: boolean;
  type: ProgramType;
}

export interface AffiliateConfig {
  programs: AffiliateProgram[];
}

export type DisclosureKind = 'affiliate' | 'referral' | 'mixed';

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
    programs: programs.flatMap((entry) => {
      const program = parseAffiliateProgram(entry);
      return program ? [program] : [];
    }),
  };
}

function parseAffiliateProgram(value: unknown): AffiliateProgram | null {
  if (!value || typeof value !== 'object') return null;
  const program = value as Record<string, unknown>;
  const type = program.type === undefined ? 'affiliate' : program.type;
  if (type !== 'affiliate' && type !== 'referral') return null;
  if (
    typeof program.id !== 'string' ||
    typeof program.name !== 'string' ||
    typeof program.category !== 'string' ||
    typeof program.url !== 'string' ||
    typeof program.promo_code !== 'string' ||
    typeof program.anchor !== 'string' ||
    typeof program.enabled !== 'boolean'
  ) {
    return null;
  }
  return {
    id: program.id,
    name: program.name,
    category: program.category,
    url: program.url,
    promo_code: program.promo_code,
    anchor: program.anchor,
    enabled: program.enabled,
    type,
  };
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

export function linkDisclosure(type: ProgramType): string {
  if (type === 'referral') {
    return 'We may receive credits or rewards if you sign up through this link.';
  }
  return 'We may earn a commission if you click this link.';
}

export function activeProgramsForArticle(
  partnerId: string | null | undefined,
  content: string,
  programs: AffiliateProgram[] = loadAffiliateConfig().programs,
): AffiliateProgram[] {
  const ids = new Set<string>();
  const primary = (partnerId ?? '').trim();
  if (primary) ids.add(primary);
  for (const id of affiliatePartnerIdsInContent(content)) ids.add(id);
  const found: AffiliateProgram[] = [];
  for (const id of ids) {
    const program = getProgram(id, programs);
    if (isProgramActive(program)) found.push(program);
  }
  return found;
}

export function disclosureKind(
  programs: AffiliateProgram[],
): DisclosureKind | null {
  const active = programs.filter((program) => isProgramActive(program));
  if (active.length === 0) return null;
  const kinds = new Set(active.map((program) => program.type));
  if (kinds.has('referral') && kinds.has('affiliate')) return 'mixed';
  if (kinds.has('referral')) return 'referral';
  return 'affiliate';
}

export function articleDisclosureText(kind: DisclosureKind): string {
  if (kind === 'referral') {
    return 'This article contains a referral link. We may receive credits or rewards if you sign up through it.';
  }
  if (kind === 'mixed') {
    return 'This article contains affiliate and referral links. We may earn a commission or receive credits or rewards if you use them.';
  }
  return 'This article contains affiliate links. We may earn a commission if you buy through them.';
}

export function comparisonBannerText(kind: DisclosureKind | null): string {
  if (kind === 'referral') {
    return 'This page contains a referral link. We may receive credits or rewards if you sign up through it.';
  }
  if (kind === 'mixed') {
    return 'This page contains affiliate and referral links. We may earn a commission or receive credits or rewards if you use them.';
  }
  return 'This page contains affiliate links. We may earn a commission at no cost to you.';
}
