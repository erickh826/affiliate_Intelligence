import { describe, expect, it } from 'vitest';
import { footerLegal } from '../lib/site-nav';

describe('static pages export defaults', () => {
  it('about page', async () => {
    const mod = await import('../app/about/page');
    expect(typeof mod.default).toBe('function');
  });

  it('contact page', async () => {
    const mod = await import('../app/contact/page');
    expect(typeof mod.default).toBe('function');
  });

  it('privacy-policy page', async () => {
    const mod = await import('../app/privacy-policy/page');
    expect(typeof mod.default).toBe('function');
  });

  it('disclaimer page', async () => {
    const mod = await import('../app/disclaimer/page');
    expect(typeof mod.default).toBe('function');
  });

  it('affiliate disclosure page', async () => {
    const mod = await import('../app/affiliate-disclosure/page');
    expect(typeof mod.default).toBe('function');
  });
});

describe('footer legal links', () => {
  it('links the privacy policy and the affiliate disclosure', () => {
    const hrefs = footerLegal.map((link) => link.href);
    expect(hrefs).toContain('/privacy-policy');
    expect(hrefs).toContain('/affiliate-disclosure');
  });
});
