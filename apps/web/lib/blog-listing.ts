import type { MDXData } from './mdx';

export interface ArticleSummary {
  title: string;
  description: string;
  slug: string;
  category: string;
  categoryLabel: string;
  publishedAt: string;
  href: string;
  image: string | null;
}

export interface TopicLink {
  label: string;
  href: string;
}

export interface BlogListing {
  featured: MDXData | null;
  grid: MDXData[];
  list: MDXData[];
}

const ACRONYMS: Record<string, string> = {
  ai: 'AI',
};

export function categoryLabel(category: string): string {
  return category
    .split('-')
    .filter(Boolean)
    .map((word) => {
      const acronym = ACRONYMS[word.toLowerCase()];
      if (acronym) return acronym;
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(' ');
}

export function formatArticleDate(isoDate: string): string {
  const date = new Date(`${isoDate.slice(0, 10)}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return isoDate;
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    timeZone: 'UTC',
  }).format(date);
}

export function sortByPublishedDesc(articles: MDXData[]): MDXData[] {
  return [...articles].sort((a, b) =>
    b.frontmatter.published_at.localeCompare(a.frontmatter.published_at),
  );
}

export function splitBlogListing(articles: MDXData[]): BlogListing {
  const sorted = sortByPublishedDesc(articles);
  const [featured, ...rest] = sorted;
  return {
    featured: featured ?? null,
    grid: rest.slice(0, 3),
    list: rest.slice(3),
  };
}

export function topicLinksFromArticles(articles: MDXData[]): TopicLink[] {
  const seen = new Set<string>();
  const topics: TopicLink[] = [];
  for (const article of sortByPublishedDesc(articles)) {
    const category = article.frontmatter.category;
    if (!category || seen.has(category)) continue;
    seen.add(category);
    topics.push({
      label: categoryLabel(category),
      href: `/${category}`,
    });
  }
  return topics;
}

export const fallbackTopics: TopicLink[] = [
  { label: 'AI writing tools', href: '/' },
  { label: 'Affiliate marketing', href: '/' },
  { label: 'Website builders', href: '/' },
];

export function toArticleSummary(
  article: MDXData,
  image: string | null,
): ArticleSummary {
  const { title, description, slug, category, published_at } =
    article.frontmatter;
  return {
    title,
    description,
    slug,
    category,
    categoryLabel: categoryLabel(category),
    publishedAt: published_at,
    href: `/${category}/${slug}`,
    image,
  };
}
