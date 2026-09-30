import { describe, expect, it } from 'vitest';

import {
  getAllArticles,
  getFAQBySlug,
  getMDXDataBySlug,
  getHeadings,
  neutralizeUnresolvedLinks,
  splitAtH2,
} from '../lib/mdx';

describe('mdx loader', () => {
  it('loads the published live article', async () => {
    const articles = await getAllArticles();
    const article = articles.find(
      (item) => item.frontmatter.slug === 'best-ai-writing-tools-2026',
    );
    expect(article?.frontmatter.category).toBe('ai-writing');
    expect(article?.frontmatter.published_at).toBe('2026-09-30');
    expect(article?.frontmatter.affiliate_partner).toBe('jasper');
    expect((article?.content.length ?? 0) > 1000).toBe(true);
    expect(article?.content).not.toContain('{{LINK_');
  });

  it('loads the live article by category and slug', async () => {
    const article = await getMDXDataBySlug(
      'ai-writing',
      'best-ai-writing-tools-2026',
    );
    expect(article?.frontmatter.title).toContain('Best AI Writing Tools 2026');
    expect(article?.frontmatter.slug).toBe('best-ai-writing-tools-2026');
  });

  it('loads the published FAQ file', async () => {
    const faq = await getFAQBySlug('best-ai-writing-tools-2026');
    expect(faq?.slug).toBe('best-ai-writing-tools-2026');
    expect((faq?.faqs.length ?? 0) >= 4).toBe(true);
  });

  it('returns null for a slug with no published article', async () => {
    const article = await getMDXDataBySlug(
      'ai-writing',
      'this-slug-does-not-exist-xyz',
    );
    expect(article).toBeNull();
  });

  it('excludes faq directory from article scan', async () => {
    const articles = await getAllArticles();
    expect(
      articles.every((article) => article.frontmatter.category !== 'faq'),
    ).toBe(true);
  });
});

describe('neutralizeUnresolvedLinks', () => {
  it('replaces unresolved link placeholders with their anchor text', () => {
    const content =
      'See [AI writing tools]({{LINK_AI_WRITING}}) and [Jasper]({{LINK_JASPER}}).';
    expect(neutralizeUnresolvedLinks(content)).toBe(
      'See AI writing tools and Jasper.',
    );
  });
});

describe('getHeadings', () => {
  it('returns empty array for content with no headings', () => {
    expect(getHeadings('Some plain text without headings')).toEqual([]);
  });

  it('extracts H2 headings with correct id, text, and level', () => {
    const content = '## Section One\n\ntext\n\n## Section Two\n\nmore text';
    const result = getHeadings(content);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({
      id: 'section-one',
      text: 'Section One',
      level: 2,
    });
    expect(result[1]).toEqual({
      id: 'section-two',
      text: 'Section Two',
      level: 2,
    });
  });

  it('extracts H3 headings with level 3', () => {
    const content = '## H2 Title\n\n### H3 Title\n\ntext';
    const result = getHeadings(content);
    expect(result).toHaveLength(2);
    expect(result[1]).toEqual({ id: 'h3-title', text: 'H3 Title', level: 3 });
  });

  it('generates slug-safe ids (lowercased, non-alphanumeric collapsed to hyphens)', () => {
    const content = '## What Is AI? A Guide';
    const result = getHeadings(content);
    expect(result[0].id).toBe('what-is-ai-a-guide');
  });

  it('gives duplicate headings distinct ids', () => {
    const content =
      '## Pricing Comparison Table\n\n## Pricing Comparison Table';
    const result = getHeadings(content);
    expect(result.map((heading) => heading.id)).toEqual([
      'pricing-comparison-table',
      'pricing-comparison-table-2',
    ]);
  });

  it('strips leading and trailing hyphens from id', () => {
    const content = '## (Test Heading!)';
    const result = getHeadings(content);
    expect(result[0].id).not.toMatch(/^-|-$/);
  });
});

describe('splitAtH2', () => {
  it('returns single-element array when no H2 headings exist', () => {
    const parts = splitAtH2('Just some text without headings');
    expect(parts).toHaveLength(1);
  });

  it('splits at H2 boundaries, keeping ## in each part', () => {
    const content = 'intro\n\n## Section One\n\ntext\n\n## Section Two\n\nmore';
    const parts = splitAtH2(content);
    expect(parts).toHaveLength(3);
    expect(parts[1]).toMatch(/^## Section One/);
    expect(parts[2]).toMatch(/^## Section Two/);
  });

  it('inline CTA condition — 2 H2s: slice(2) has length 1, CTA does NOT render', () => {
    const content = 'intro\n\n## H2 One\n\ntext\n\n## H2 Two\n\ntext';
    const parts = splitAtH2(content);
    expect(parts.slice(2).length).toBe(1);
    expect(parts.slice(2).length > 1).toBe(false);
  });

  it('inline CTA condition — 3 H2s: slice(2) has length > 1, CTA DOES render', () => {
    const content =
      'intro\n\n## H2 One\n\ntext\n\n## H2 Two\n\ntext\n\n## H2 Three\n\ntext';
    const parts = splitAtH2(content);
    expect(parts.slice(2).length).toBeGreaterThan(1);
  });

  it('three H2s leave a trailing part so the inline CTA can render', () => {
    const content =
      'intro\n\n## H2 One\n\ntext\n\n## H2 Two\n\ntext\n\n## H2 Three\n\ntext';
    const parts = splitAtH2(content);
    const headings = getHeadings(content);
    expect(parts.slice(2).length).toBeGreaterThan(1);
    expect(headings.filter((heading) => heading.level === 2).length).toBe(3);
  });
});
