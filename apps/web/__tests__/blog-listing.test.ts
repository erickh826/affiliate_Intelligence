import { describe, expect, it } from 'vitest';
import { resolveArticleImage } from '../lib/article-image';
import {
  categoryLabel,
  formatArticleDate,
  splitBlogListing,
  topicLinksFromArticles,
} from '../lib/blog-listing';
import type { MDXData } from '../lib/mdx';
import { formatBrandName, getPrimaryCta } from '../lib/site-nav';

function article(slug: string, category: string, publishedAt: string): MDXData {
  return {
    frontmatter: {
      title: slug,
      description: `${slug} description`,
      slug,
      category,
      intent: 'comparison',
      published_at: publishedAt,
      last_reviewed: publishedAt,
      author: 'Editor',
      affiliate_partner: null,
      schema_type: 'Article',
    },
    content: '',
    contentParts: [],
    headings: [],
    filePath: `${category}/${slug}.mdx`,
  };
}

describe('blog listing', () => {
  it('features the newest article and splits the rest into a grid and list', () => {
    const listing = splitBlogListing([
      article('oldest', 'guides', '2026-01-01'),
      article('newest', 'ai-writing', '2026-09-30'),
      article('second', 'guides', '2026-08-01'),
      article('third', 'research', '2026-07-01'),
      article('fourth', 'product', '2026-06-01'),
      article('fifth', 'product', '2026-05-01'),
    ]);

    expect(listing.featured?.frontmatter.slug).toBe('newest');
    expect(listing.grid.map((item) => item.frontmatter.slug)).toEqual([
      'second',
      'third',
      'fourth',
    ]);
    expect(listing.list.map((item) => item.frontmatter.slug)).toEqual([
      'fifth',
      'oldest',
    ]);
  });

  it('leaves popular slots empty when only one article exists', () => {
    const listing = splitBlogListing([
      article('only', 'ai-writing', '2026-09-30'),
    ]);

    expect(listing.featured?.frontmatter.slug).toBe('only');
    expect(listing.grid).toEqual([]);
    expect(listing.list).toEqual([]);
  });

  it('builds topic links from unique categories', () => {
    expect(
      topicLinksFromArticles([
        article('a', 'ai-writing', '2026-09-30'),
        article('b', 'ai-writing', '2026-08-01'),
        article('c', 'website-builders', '2026-07-01'),
      ]).map((topic) => topic.href),
    ).toEqual(['/ai-writing', '/website-builders']);
  });

  it('formats category labels and calendar dates in UTC', () => {
    expect(categoryLabel('ai-writing')).toBe('AI Writing');
    expect(formatArticleDate('2026-09-30')).toBe('September 30, 2026');
  });
});

describe('article images', () => {
  it('accepts a file that exists in public and rejects missing or unsafe paths', () => {
    expect(resolveArticleImage({ image: '/og-default.svg' })).toBe(
      '/og-default.svg',
    );
    expect(resolveArticleImage({ image: '/missing-article.png' })).toBeNull();
    expect(resolveArticleImage({ image: '../package.json' })).toBeNull();
    expect(
      resolveArticleImage({ image: 'https://example.com/a.jpg' }),
    ).toBeNull();
    expect(resolveArticleImage({})).toBeNull();
  });
});

describe('brand label', () => {
  it('capitalizes the public site name for the wordmark and pill', () => {
    expect(formatBrandName('shadona')).toBe('Shadona');
    expect(formatBrandName('ai tools hub')).toBe('AI Tools Hub');
    const cta: { label: string; href: string } = getPrimaryCta();
    expect(cta.href).toBe('/contact');
    expect(cta.label.startsWith('Try ')).toBe(true);
  });
});
