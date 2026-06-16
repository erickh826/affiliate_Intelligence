import { describe, expect, it } from 'vitest';
import {
  buildArticleSchema,
  buildBreadcrumbSchema,
  buildFaqSchema,
} from '../lib/schema_builder';
import type { FAQData, Frontmatter } from '../lib/mdx';

const SITE_URL = 'https://example.com';

const frontmatter: Frontmatter = {
  title: 'Best AI Writing Tools 2026',
  description: 'Top writing tools compared.',
  slug: 'best-ai-writing-tools-2026',
  category: 'ai-writing',
  intent: 'comparison',
  published_at: '2026-05-31',
  last_reviewed: '2026-06-01',
  author: 'Test Author',
  affiliate_partner: 'jasper',
  schema_type: 'Article',
};

const faqData: FAQData = {
  slug: 'best-ai-writing-tools-2026',
  faqs: [
    { question: 'Is Jasper good?', answer: 'Yes.' },
    { question: 'Is it free?', answer: 'No.' },
  ],
};

describe('buildArticleSchema', () => {
  it('returns @type Article', () => {
    const schema = buildArticleSchema(frontmatter, SITE_URL) as Record<
      string,
      unknown
    >;
    expect(schema['@type']).toBe('Article');
  });

  it('sets headline and description from frontmatter', () => {
    const schema = buildArticleSchema(frontmatter, SITE_URL) as Record<
      string,
      unknown
    >;
    expect(schema.headline).toBe(frontmatter.title);
    expect(schema.description).toBe(frontmatter.description);
  });

  it('URL includes trailing slash', () => {
    const schema = buildArticleSchema(frontmatter, SITE_URL) as Record<
      string,
      unknown
    >;
    expect(schema.url as string).toMatch(/\/$/);
  });

  it('URL is correctly composed', () => {
    const schema = buildArticleSchema(frontmatter, SITE_URL) as Record<
      string,
      unknown
    >;
    expect(schema.url).toBe(
      `${SITE_URL}/ai-writing/best-ai-writing-tools-2026/`,
    );
  });
});

describe('buildBreadcrumbSchema', () => {
  it('returns @type BreadcrumbList', () => {
    const schema = buildBreadcrumbSchema(
      'ai-writing',
      'best-ai-writing-tools-2026',
      'Title',
      SITE_URL,
    ) as Record<string, unknown>;
    expect(schema['@type']).toBe('BreadcrumbList');
  });

  it('has three list items', () => {
    const schema = buildBreadcrumbSchema(
      'ai-writing',
      'best-ai-writing-tools-2026',
      'Title',
      SITE_URL,
    ) as Record<string, unknown>;
    const items = schema.itemListElement as unknown[];
    expect(items).toHaveLength(3);
  });

  it('all item URLs end with trailing slash', () => {
    const schema = buildBreadcrumbSchema(
      'ai-writing',
      'best-ai-writing-tools-2026',
      'Title',
      SITE_URL,
    ) as Record<string, unknown>;
    const items = schema.itemListElement as Record<string, string>[];
    for (const item of items) {
      expect(item.item).toMatch(/\/$/);
    }
  });

  it('article item URL is correctly composed', () => {
    const schema = buildBreadcrumbSchema(
      'ai-writing',
      'best-ai-writing-tools-2026',
      'Title',
      SITE_URL,
    ) as Record<string, unknown>;
    const items = schema.itemListElement as Record<string, string>[];
    expect(items[2].item).toBe(
      `${SITE_URL}/ai-writing/best-ai-writing-tools-2026/`,
    );
  });
});

describe('buildFaqSchema', () => {
  it('returns @type FAQPage', () => {
    const schema = buildFaqSchema(faqData, SITE_URL) as Record<string, unknown>;
    expect(schema['@type']).toBe('FAQPage');
  });

  it('maps FAQs to mainEntity Questions', () => {
    const schema = buildFaqSchema(faqData, SITE_URL) as Record<string, unknown>;
    const entities = schema.mainEntity as Record<string, unknown>[];
    expect(entities).toHaveLength(2);
    expect(entities[0]['@type']).toBe('Question');
    expect(entities[0].name).toBe('Is Jasper good?');
  });
});
