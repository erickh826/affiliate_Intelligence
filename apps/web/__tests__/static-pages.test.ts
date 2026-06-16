import { describe, expect, it } from 'vitest';

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
});
