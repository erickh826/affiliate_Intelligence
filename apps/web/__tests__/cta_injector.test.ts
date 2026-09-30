import { describe, expect, it } from 'vitest';
import path from 'path';
import {
  getAffiliateMap,
  resolveCTAUrl,
  resolveCTAConfig,
} from '../lib/cta_injector';
import type { AffiliateMap } from '../lib/cta_injector';
import { AFFILIATE_LINKS } from '../lib/affiliate-links';

const FIXTURES = path.join(__dirname, 'fixtures');

const mapWithLinks: AffiliateMap = JSON.parse(
  require('fs').readFileSync(
    path.join(FIXTURES, 'affiliate-map-with-links.json'),
    'utf8',
  ),
);

const mapEmptyLinks: AffiliateMap = JSON.parse(
  require('fs').readFileSync(
    path.join(FIXTURES, 'affiliate-map-empty-links.json'),
    'utf8',
  ),
);

const mapUnknownPartner: AffiliateMap = {
  slug: 'test',
  primary_partner: 'unknown_partner_xyz',
  cta_variant: 'A',
  links: {},
};

describe('getAffiliateMap', () => {
  it('loads the published affiliate map for the live article', () => {
    const map = getAffiliateMap('best-ai-writing-tools-2026');
    expect(map).toEqual({
      slug: 'best-ai-writing-tools-2026',
      primary_partner: 'jasper',
      cta_variant: 'A',
      links: {},
    });
  });

  it('returns null for missing slug', () => {
    const map = getAffiliateMap('this-slug-does-not-exist-xyz');
    expect(map).toBeNull();
  });
});

describe('resolveCTAUrl', () => {
  it('uses links[primary_partner] when populated', () => {
    const url = resolveCTAUrl(mapWithLinks);
    expect(url).toBe('https://www.jasper.ai?via=test');
  });

  it('falls back to AFFILIATE_LINKS when links is empty', () => {
    const url = resolveCTAUrl(mapEmptyLinks);
    expect(url).toBe(AFFILIATE_LINKS['jasper']);
  });

  it('returns null for unknown partner with empty links', () => {
    const url = resolveCTAUrl(mapUnknownPartner);
    expect(url).toBeNull();
  });
});

describe('resolveCTAConfig', () => {
  it('resolves the live article CTA from the partner fallback', () => {
    const config = resolveCTAConfig('best-ai-writing-tools-2026');
    expect(config).toEqual({
      href: AFFILIATE_LINKS.jasper,
      text: 'Try jasper →',
      partner: 'jasper',
    });
  });

  it('returns null for missing slug', () => {
    const config = resolveCTAConfig('this-slug-does-not-exist-xyz');
    expect(config).toBeNull();
  });
});
