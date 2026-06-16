import type { FAQData, Frontmatter } from './mdx';

export function buildArticleSchema(
  frontmatter: Frontmatter,
  siteUrl: string,
): object {
  return {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: frontmatter.title,
    description: frontmatter.description,
    author: {
      '@type': 'Person',
      name: frontmatter.author,
    },
    datePublished: frontmatter.published_at,
    dateModified: frontmatter.last_reviewed || frontmatter.published_at,
    url: `${siteUrl}/${frontmatter.category}/${frontmatter.slug}/`,
  };
}

export function buildFaqSchema(faqData: FAQData, _siteUrl: string): object {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqData.faqs.map((faq) => ({
      '@type': 'Question',
      name: faq.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: faq.answer,
      },
    })),
  };
}

export function buildBreadcrumbSchema(
  category: string,
  slug: string,
  title: string,
  siteUrl: string,
): object {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'Home',
        item: `${siteUrl}/`,
      },
      {
        '@type': 'ListItem',
        position: 2,
        name: category.replace(/-/g, ' '),
        item: `${siteUrl}/${category}/`,
      },
      {
        '@type': 'ListItem',
        position: 3,
        name: title,
        item: `${siteUrl}/${category}/${slug}/`,
      },
    ],
  };
}
