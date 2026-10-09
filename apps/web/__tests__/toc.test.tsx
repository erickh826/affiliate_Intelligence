import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import TableOfContents from '../components/TableOfContents';
import { getHeadings, getMDXDataBySlug, headingIdsForParts } from '../lib/mdx';
import { rehypeHeadingIds } from '../lib/rehype-heading-ids';
import { buildTableOfContents, flattenToc } from '../lib/toc';

const LIVE_SECTIONS = [
  'Introduction to AI Writing Tools',
  'Overview of the Top AI Writing Tools',
  'Comparison of Features',
  'Use Cases for Each Tool',
  'Common Complaints and Limitations',
  'Future of AI Writing Tools',
  'Conclusion: Choosing the Right Tool',
];

describe('buildTableOfContents', () => {
  it('uses H2 as the top level and nests H3 when sections are not repeated', () => {
    const content = '## One\n\n### Nested\n\n## Two\n\ntext';
    const toc = buildTableOfContents(content);

    expect(toc.map((node) => node.text)).toEqual(['One', 'Two']);
    expect(toc[0].children.map((node) => node.text)).toEqual(['Nested']);
    expect(toc[1].children).toEqual([]);
    expect(toc[0].id).toBe('one');
    expect(toc[0].children[0].id).toBe('nested');
  });

  it('ignores the document title and keeps distinct H2s', () => {
    const content = '# Article Title\n\n## First\n\n## Second\n';
    expect(buildTableOfContents(content).map((node) => node.text)).toEqual([
      'First',
      'Second',
    ]);
  });

  it('collapses a repeated section title and nests the headings that follow', () => {
    const content = [
      '# Article Title',
      '## Intro',
      '',
      '# Intro',
      '## Child',
      '### Detail',
      '## Next Section',
      '',
      '# Next Section',
      '## Later',
    ].join('\n');
    const toc = buildTableOfContents(content);

    expect(toc.map((node) => node.text)).toEqual(['Intro', 'Next Section']);
    expect(toc[0].children.map((node) => node.text)).toEqual(['Child']);
    expect(toc[0].children[0].children.map((node) => node.text)).toEqual([
      'Detail',
    ]);
    expect(toc[1].children.map((node) => node.text)).toEqual(['Later']);
  });

  it('treats a duplicated H2 with only a blank line between as one section', () => {
    const content = '## Conclusion\n\n## Conclusion\n\n### Factor\n';
    const toc = buildTableOfContents(content);

    expect(toc).toHaveLength(1);
    expect(toc[0].text).toBe('Conclusion');
    expect(toc[0].id).toBe('conclusion');
    expect(toc[0].children.map((node) => node.text)).toEqual(['Factor']);
  });

  it('does not merge headings that have body text between them', () => {
    const content = '## Same\n\nA paragraph.\n\n## Same\n';
    const toc = buildTableOfContents(content);

    expect(toc.map((node) => node.id)).toEqual(['same', 'same-2']);
  });

  it('keeps ids aligned with getHeadings for the published article', async () => {
    const article = await getMDXDataBySlug(
      'ai-writing',
      'best-ai-writing-tools-2026',
    );
    expect(article).not.toBeNull();
    if (!article) return;

    const toc = buildTableOfContents(article.content);
    const headings = getHeadings(article.content);
    const flat = flattenToc(toc);

    expect(toc.map((node) => node.text)).toEqual(LIVE_SECTIONS);
    expect(flat.length).toBeLessThan(headings.length);
    expect(
      toc.some((node) => node.text === 'Jasper: Best for Businesses'),
    ).toBe(false);
    expect(
      toc
        .find((node) => node.text === 'Use Cases for Each Tool')
        ?.children.find(
          (node) => node.text === 'Content Marketing with Writesonic',
        )
        ?.children.map((node) => node.text),
    ).toEqual(['Pricing Comparison Table']);

    for (const node of flat) {
      expect(headings).toContainEqual({
        id: node.id,
        text: node.text,
        level: node.level,
      });
    }

    const partIds = headingIdsForParts(article.contentParts).flat();
    expect(partIds).toEqual(headings.map((heading) => heading.id));
  });
});

describe('rehypeHeadingIds', () => {
  it('assigns the next id to each h2 and h3 in document order', () => {
    const tree = {
      type: 'root',
      children: [
        { type: 'element', tagName: 'h2', properties: {}, children: [] },
        { type: 'element', tagName: 'p', properties: {}, children: [] },
        { type: 'element', tagName: 'h3', properties: {}, children: [] },
      ],
    };

    const transform = rehypeHeadingIds(['one', 'nested'])() as
      | ((tree: typeof tree) => void)
      | undefined;
    transform?.(tree);

    expect(tree.children[0].properties).toEqual({ id: 'one' });
    expect(tree.children[2].properties).toEqual({ id: 'nested' });
  });
});

describe('TableOfContents', () => {
  it('renders top-level links and keeps nested sections collapsed', () => {
    const html = renderToStaticMarkup(
      <TableOfContents
        nodes={[
          {
            id: 'intro',
            text: 'Introduction',
            level: 2,
            children: [
              {
                id: 'what',
                text: 'What are AI writing tools?',
                level: 2,
                children: [],
              },
            ],
          },
          {
            id: 'overview',
            text: 'Overview',
            level: 2,
            children: [],
          },
        ]}
      />,
    );

    expect(html).toContain('aria-label="Table of contents"');
    expect(html).toContain('href="#intro"');
    expect(html).toContain('href="#what"');
    expect(html).toContain('aria-expanded="false"');
    expect(html).toContain('Expand subsections for Introduction');
    expect(html).toContain('hidden=""');
  });
});
