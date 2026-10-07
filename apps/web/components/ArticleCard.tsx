import ArticleGridCard from './blog/ArticleGridCard';
import { resolveArticleImage } from '../lib/article-image';
import { categoryLabel, type ArticleSummary } from '../lib/blog-listing';
import type { Frontmatter } from '../lib/mdx';

interface ArticleCardProps {
  frontmatter: Frontmatter;
}

export default function ArticleCard({ frontmatter }: ArticleCardProps) {
  const article: ArticleSummary = {
    title: frontmatter.title,
    description: frontmatter.description,
    slug: frontmatter.slug,
    category: frontmatter.category,
    categoryLabel: categoryLabel(frontmatter.category),
    publishedAt: frontmatter.published_at,
    href: `/${frontmatter.category}/${frontmatter.slug}`,
    image: resolveArticleImage(frontmatter),
  };

  return <ArticleGridCard article={article} />;
}
