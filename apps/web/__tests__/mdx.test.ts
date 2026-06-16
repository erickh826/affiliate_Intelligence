import { describe, expect, it } from 'vitest';

import {
  getAllArticles,
  getFAQBySlug,
  getMDXDataBySlug,
  getHeadings,
  splitAtH2,
} from '../lib/mdx';

describe('mdx loader', () => {
  it('finds sample article in getAllArticles', async () => {
    const articles = await getAllArticles();
    expect(
      articles.some(
        (article) => article.frontmatter.slug === 'best-ai-writing-tools-2026',
      ),
    ).toBe(true);
  });

  it('parses frontmatter for sample article', async () => {
    const article = await getMDXDataBySlug(
      'ai-writing',
      'best-ai-writing-tools-2026',
    );
    expect(article).not.toBeNull();
    expect(article?.frontmatter.title).toContain('Best');
    expect(article?.frontmatter.category).toBe('ai-writing');
    expect(article?.frontmatter.schema_type).toBe('Article');
    expect(article?.content).toContain('#');
  });

  it('loads FAQ json for sample slug', async () => {
    const faq = await getFAQBySlug('best-ai-writing-tools-2026');
    expect(faq).not.toBeNull();
    expect(faq?.faqs.length).toBeGreaterThan(0);
  });

  it('excludes faq directory from article scan', async () => {
    const articles = await getAllArticles();
    expect(
      articles.every((article) => article.frontmatter.category !== 'faq'),
    ).toBe(true);
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

  it('sample article has 3+ H2s, confirming inline CTA renders', async () => {
    const article = await getMDXDataBySlug(
      'ai-writing',
      'best-ai-writing-tools-2026',
    );
    expect(article).not.toBeNull();
    expect(article!.contentParts.slice(2).length).toBeGreaterThan(1);
    expect(
      article!.headings.filter((h) => h.level === 2).length,
    ).toBeGreaterThanOrEqual(3);
  });
});
