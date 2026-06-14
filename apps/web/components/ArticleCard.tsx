import Link from 'next/link';
import type { Frontmatter } from '../lib/mdx';

interface ArticleCardProps {
  frontmatter: Frontmatter;
}

export default function ArticleCard({ frontmatter }: ArticleCardProps) {
  const { title, description, published_at, category, slug } = frontmatter;
  return (
    <article className="bg-surface border border-gray-800 rounded-lg p-6 hover:border-accent transition-colors">
      <Link href={`/${category}/${slug}`} className="block">
        <div className="mb-3">
          <span className="text-xs font-medium text-accent uppercase tracking-wide border border-accent/30 rounded px-2 py-0.5">
            {category.replace(/-/g, ' ')}
          </span>
        </div>
        <h3 className="text-lg font-bold mb-2 font-display leading-snug hover:text-accent transition-colors">
          {title}
        </h3>
        <p className="text-gray-400 text-sm line-clamp-2 mb-3">{description}</p>
        <time className="text-xs text-gray-500" dateTime={published_at}>
          {new Date(published_at).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </time>
      </Link>
    </article>
  );
}
