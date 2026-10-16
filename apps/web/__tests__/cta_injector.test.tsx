import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import {
  ctaFromProgram,
  getAffiliateMap,
  resolveCTAConfig,
  shouldShowAffiliateDisclosure,
} from '../lib/cta_injector';
import {
  contentRendersAffiliateCta,
  getProgram,
  loadAffiliateConfig,
} from '../lib/affiliates';
import type { AffiliateProgram } from '../lib/affiliates';
import AffiliateCTA from '../components/AffiliateCTA';
import AffiliateDisclosureNote from '../components/AffiliateDisclosureNote';

const enabledJasper: AffiliateProgram = {
  id: 'jasper',
  name: 'Jasper AI',
  category: 'ai-writing',
  url: 'https://jasper.ai/?via=real',
  promo_code: 'SAVE10',
  anchor: 'Try Jasper Free for 7 Days →',
  enabled: true,
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

describe('central affiliate config', () => {
  it('keeps placeholder programs disabled', () => {
    const programs = loadAffiliateConfig().programs;
    expect(programs.length).toBeGreaterThanOrEqual(10);
    expect(programs.every((program) => program.enabled === false)).toBe(true);
    expect(getProgram('jasper')?.url).toContain('YOUR_REF');
  });

  it('renders the CTA from the program record, not the article map', () => {
    const config = ctaFromProgram(enabledJasper);
    expect(config).toEqual({
      href: 'https://jasper.ai/?via=real',
      text: 'Try Jasper Free for 7 Days →',
      partner: 'Jasper AI',
      promoCode: 'SAVE10',
    });
    expect(resolveCTAConfig('best-ai-writing-tools-2026', 'jasper')).toBeNull();
  });

  it('hides a disabled program even when the map stores a link', () => {
    expect(
      contentRendersAffiliateCta('<AffiliateCTA partner="jasper" />'),
    ).toBe(false);
    expect(
      shouldShowAffiliateDisclosure(null, '<AffiliateCTA partner="jasper" />'),
    ).toBe(false);
    expect(
      shouldShowAffiliateDisclosure(ctaFromProgram(enabledJasper), ''),
    ).toBe(true);
  });
});

describe('resolveCTAConfig', () => {
  it('returns null for missing slug', () => {
    const config = resolveCTAConfig('this-slug-does-not-exist-xyz');
    expect(config).toBeNull();
  });
});

describe('affiliate markup', () => {
  it('marks the outbound link sponsored and links the disclosure', () => {
    const html = renderToStaticMarkup(
      <AffiliateCTA
        href="https://jasper.ai/?via=real"
        text="Try Jasper"
        partner="Jasper AI"
        placement="top"
        promoCode="SAVE10"
      />,
    );
    expect(html).toContain('rel="sponsored noopener noreferrer"');
    expect(html).toContain('href="https://jasper.ai/?via=real"');
    expect(html).toContain('Promo code: SAVE10');

    const note = renderToStaticMarkup(<AffiliateDisclosureNote />);
    expect(note).toContain('href="/affiliate-disclosure"');
    expect(note).toContain('affiliate links');
  });
});
