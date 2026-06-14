import { describe, expect, it } from 'vitest';

import {
  getAllArticles,
  getFAQBySlug,
  getMDXDataBySlug,
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
    expect(articles.every((article) => article.frontmatter.category !== 'faq')).toBe(
      true,
    );
  });
});
