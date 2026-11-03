import ArticleGridCard from './blog/ArticleGridCard';
import { articleSummaryFromFrontmatter } from '../lib/blog-listing';
import type { Frontmatter } from '../lib/mdx';

interface ArticleCardProps {
  frontmatter: Frontmatter;
}

export default function ArticleCard({ frontmatter }: ArticleCardProps) {
  return (
    <ArticleGridCard article={articleSummaryFromFrontmatter(frontmatter)} />
  );
}
