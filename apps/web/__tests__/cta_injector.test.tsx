import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import {
  ctaFromProgram,
  getAffiliateMap,
  resolveCTAConfig,
  shouldShowAffiliateDisclosure,
} from '../lib/cta_injector';
import {
  activeProgramsForArticle,
  articleDisclosureText,
  contentRendersAffiliateCta,
  disclosureKind,
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
  type: 'affiliate',
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
  it('keeps placeholder programs disabled and enables referral links', () => {
    const programs = loadAffiliateConfig().programs;
    const affiliates = programs.filter(
      (program) => program.type === 'affiliate',
    );
    expect(affiliates.length).toBeGreaterThanOrEqual(10);
    expect(affiliates.every((program) => program.enabled === false)).toBe(true);
    expect(getProgram('jasper')?.url).toContain('YOUR_REF');
    expect(getProgram('jasper')?.type).toBe('affiliate');

    const lovable = getProgram('lovable');
    const manus = getProgram('manus');
    expect(lovable).toMatchObject({
      type: 'referral',
      enabled: true,
      category: 'ai-code',
      url: 'https://lovable.dev/invite/U7087MO',
    });
    expect(manus).toMatchObject({
      type: 'referral',
      enabled: true,
      url: 'https://manus.im/invitation/4QB3RCLPTD1A',
    });
    expect(lovable?.anchor).toContain('bonus credits');
    expect(manus?.anchor).toContain('bonus credits');
    expect(ctaFromProgram(lovable)?.disclosure).toContain('credits or rewards');
    expect(ctaFromProgram(manus)?.linkType).toBe('referral');
  });

  it('uses operator CTA wording from the article map', () => {
    const config = resolveCTAConfig('unused-slug', 'jasper', [enabledJasper], {
      slug: 'unused-slug',
      primary_partner: 'jasper',
      cta_variant: 'A',
      links: {},
      cta_text: 'Sign up with this link to get bonus credits',
    });
    expect(config?.text).toBe('Sign up with this link to get bonus credits');
    expect(config?.href).toBe('https://jasper.ai/?via=real');
  });

  it('renders the CTA from the program record, not the article map', () => {
    const config = ctaFromProgram(enabledJasper);
    expect(config).toEqual({
      href: 'https://jasper.ai/?via=real',
      text: 'Try Jasper Free for 7 Days →',
      partner: 'Jasper AI',
      promoCode: 'SAVE10',
      linkType: 'affiliate',
      disclosure: 'We may earn a commission if you click this link.',
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

    const referral = renderToStaticMarkup(
      <AffiliateCTA
        href="https://lovable.dev/invite/U7087MO"
        text="Sign up with this link to get bonus credits"
        partner="Lovable"
        placement="inline"
        linkType="referral"
        disclosure="We may receive credits or rewards if you sign up through this link."
      />,
    );
    expect(referral).toContain('href="https://lovable.dev/invite/U7087MO"');
    expect(referral).toContain('rel="sponsored noopener noreferrer"');
    expect(referral).toContain('bonus credits');
    expect(referral).toContain('credits or rewards');
    expect(referral).not.toContain('affiliate partner');

    const referralNote = renderToStaticMarkup(
      <AffiliateDisclosureNote kind="referral" />,
    );
    expect(referralNote).toContain(articleDisclosureText('referral'));
    expect(referralNote).toContain('href="/affiliate-disclosure"');
  });
});

describe('referral placement', () => {
  it('marks lovable and manus articles and shows the referral disclosure', async () => {
    const { getMDXDataBySlug } = await import('../lib/mdx');
    const lovableSlugs = [
      'cursor-ai-review-2026',
      'github-copilot-vs-cursor',
      'best-ai-tools-for-developers-2026',
    ];
    for (const slug of lovableSlugs) {
      const article = await getMDXDataBySlug('ai-code', slug);
      expect(article?.content).toContain('<AffiliateCTA partner="lovable" />');
      expect(
        disclosureKind(activeProgramsForArticle(null, article?.content ?? '')),
      ).not.toBeNull();
    }

    const manusSlugs = [
      'how-to-use-cursor-ai',
      'cursor-vs-windsurf',
      'github-copilot-review-2026',
      'claude-code-review-2026',
      'best-ai-tools-for-developers-2026',
    ];
    for (const slug of manusSlugs) {
      const article = await getMDXDataBySlug('ai-code', slug);
      expect(article?.content).toContain('<AffiliateCTA partner="manus" />');
      expect(article?.content).toContain(
        'paused new subscriptions in some regions since August 2026',
      );
      expect(
        disclosureKind(activeProgramsForArticle(null, article?.content ?? '')),
      ).toBe('referral');
    }
  });
});
