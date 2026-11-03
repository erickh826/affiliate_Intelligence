import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import CoverCard from '../components/cover/CoverCard';
import { articleDisplayImage } from '../lib/article-image';
import {
  articleCoverAlt,
  articleKeyword,
  buildCoverModel,
  coverImagePath,
  coverMonogram,
  coverToolLabel,
} from '../lib/cover';
import { getAllArticles } from '../lib/mdx';

describe('cover model', () => {
  it('uses the tool name on reviews and comparisons', () => {
    expect(
      coverToolLabel('Cursor AI Review 2026: An Analysis', 'AI Code'),
    ).toBe('Cursor AI');
    expect(
      coverToolLabel('GitHub Copilot vs Cursor: A Comparison', 'AI Code'),
    ).toBe('GitHub Copilot vs Cursor');
    expect(
      coverToolLabel('How to Use Jasper AI: A Tutorial', 'AI Writing'),
    ).toBe('Jasper AI');
    expect(coverToolLabel('Best AI Tools for Developers 2026', 'AI Code')).toBe(
      'AI Code',
    );
    expect(coverMonogram('GitHub Copilot vs Cursor')).toBe('GC');
  });

  it('puts the keyword in the alt text and the image url', () => {
    const alt = articleCoverAlt(
      'Best AI Writing Tools 2026',
      'best-ai-writing-tools-2026',
    );
    expect(alt.toLowerCase()).toContain(
      articleKeyword('best-ai-writing-tools-2026'),
    );
    expect(coverImagePath('ai-writing', 'best-ai-writing-tools-2026')).toBe(
      '/cover/ai-writing/best-ai-writing-tools-2026',
    );
  });

  it('renders the title, tool, and keyword on the card', () => {
    const model = buildCoverModel({
      title: 'Cursor AI Review 2026: An In-Depth Analysis',
      slug: 'cursor-ai-review-2026',
      category: 'ai-code',
      categoryLabel: 'AI Code',
      brand: 'Shadona',
    });
    const html = renderToStaticMarkup(<CoverCard model={model} />);
    expect(html).toContain('Cursor AI Review 2026');
    expect(html).toContain('Cursor AI');
    expect(html).toContain('cursor ai review 2026');
    expect(html).toContain('Shadona');
    expect(html).toContain('AI Code');
  });
});

describe('article covers', () => {
  it('gives every article file a cover whose alt includes its keyword', async () => {
    const articles = await getAllArticles({ includeDrafts: true });
    expect(articles.length).toBe(107);
    for (const article of articles) {
      const image = articleDisplayImage(article.frontmatter);
      expect(image.src).toBe(
        coverImagePath(article.frontmatter.category, article.frontmatter.slug),
      );
      expect(image.alt.toLowerCase()).toContain(
        articleKeyword(article.frontmatter.slug),
      );
    }
  });
});
