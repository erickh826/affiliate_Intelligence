import { createRequire } from 'node:module';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { getGaMeasurementId, getSiteUrl } from '../lib/site';

const require = createRequire(import.meta.url);
const { listPublishedRoutes, resolveSiteUrl } =
  require('../lib/sitemap-source') as {
    listPublishedRoutes: (contentDir: string) => Array<{
      loc: string;
      lastmod?: string;
      changefreq: string;
      priority: number;
    }>;
    resolveSiteUrl: () => string;
  };

afterEach(() => {
  vi.unstubAllEnvs();
});

describe('site url', () => {
  it('prefers NEXT_PUBLIC_SITE_URL and strips a trailing slash', () => {
    vi.stubEnv(
      'NEXT_PUBLIC_SITE_URL',
      'https://affiliate-intelligence-teal.vercel.app/',
    );
    vi.stubEnv('VERCEL_PROJECT_PRODUCTION_URL', 'www.shadona.co');

    expect(getSiteUrl()).toBe('https://affiliate-intelligence-teal.vercel.app');
    expect(resolveSiteUrl()).toBe(getSiteUrl());
  });

  it('falls back to the Vercel production host', () => {
    vi.stubEnv('NEXT_PUBLIC_SITE_URL', '');
    vi.stubEnv(
      'VERCEL_PROJECT_PRODUCTION_URL',
      'affiliate-intelligence-teal.vercel.app',
    );

    expect(getSiteUrl()).toBe('https://affiliate-intelligence-teal.vercel.app');
    expect(resolveSiteUrl()).toBe(getSiteUrl());
  });

  it('falls back to localhost outside a production deploy', () => {
    vi.stubEnv('NEXT_PUBLIC_SITE_URL', '   ');
    vi.stubEnv('VERCEL_PROJECT_PRODUCTION_URL', '');

    expect(getSiteUrl()).toBe('http://localhost:3000');
    expect(resolveSiteUrl()).toBe(getSiteUrl());
  });
});

describe('GA4 measurement id', () => {
  it('returns a trimmed measurement id', () => {
    vi.stubEnv('NEXT_PUBLIC_GA_MEASUREMENT_ID', '  G-ABC123xyz  ');
    expect(getGaMeasurementId()).toBe('G-ABC123xyz');
  });

  it('ignores an empty or invalid measurement id', () => {
    vi.stubEnv('NEXT_PUBLIC_GA_MEASUREMENT_ID', '');
    expect(getGaMeasurementId()).toBeNull();

    vi.stubEnv('NEXT_PUBLIC_GA_MEASUREMENT_ID', 'UA-12345');
    expect(getGaMeasurementId()).toBeNull();

    vi.stubEnv('NEXT_PUBLIC_GA_MEASUREMENT_ID', "G-ABC');alert(1);//");
    expect(getGaMeasurementId()).toBeNull();
  });
});

describe('published sitemap routes', () => {
  it('lists category and article urls from MDX frontmatter', () => {
    const contentDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sitemap-'));
    const categoryDir = path.join(contentDir, 'ai-writing');
    fs.mkdirSync(path.join(contentDir, 'faq'), { recursive: true });
    fs.mkdirSync(categoryDir, { recursive: true });
    fs.writeFileSync(path.join(contentDir, 'faq', 'ignored.faq.json'), '{}');
    fs.writeFileSync(path.join(categoryDir, 'notes.txt'), 'not an article');
    fs.writeFileSync(
      path.join(categoryDir, 'best-ai-writing-tools-2026.mdx'),
      `---
title: Best
slug: best-ai-writing-tools-2026
category: ai-writing
published_at: 2026-09-30
last_reviewed: 2026-10-01
---
Body
`,
    );
    fs.writeFileSync(
      path.join(categoryDir, 'older-tool.mdx'),
      `---
title: Older
slug: older-tool
category: ai-writing
published_at: 2026-01-02
---
Body
`,
    );

    const routes = listPublishedRoutes(contentDir);
    const article = routes.find(
      (route) => route.loc === '/ai-writing/best-ai-writing-tools-2026',
    );
    const category = routes.find((route) => route.loc === '/ai-writing');

    expect(article).toMatchObject({
      changefreq: 'weekly',
      priority: 0.8,
      lastmod: '2026-10-01T00:00:00.000Z',
    });
    expect(category).toMatchObject({
      changefreq: 'weekly',
      priority: 0.6,
      lastmod: '2026-10-01T00:00:00.000Z',
    });
    expect(routes.map((route) => route.loc)).toContain(
      '/ai-writing/older-tool',
    );
    expect(routes.some((route) => route.loc.includes('faq'))).toBe(false);
    expect(routes.some((route) => route.loc.includes('notes'))).toBe(false);
  });

  it('includes the published article in this repo', () => {
    const routes = listPublishedRoutes(
      path.join(path.dirname(fileURLToPath(import.meta.url)), '../content'),
    );
    const locs = routes.map((route) => route.loc);

    expect(locs).toContain('/ai-writing');
    expect(locs).toContain('/ai-writing/best-ai-writing-tools-2026');
    expect(
      routes.find(
        (route) => route.loc === '/ai-writing/best-ai-writing-tools-2026',
      )?.lastmod,
    ).toBe('2026-09-30T00:00:00.000Z');
  });
});
