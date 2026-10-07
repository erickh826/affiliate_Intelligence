import Link from 'next/link';
import { formatArticleDate, type ArticleSummary } from '../../lib/blog-listing';
import ArticleMedia from './ArticleMedia';

interface ArticleListCardProps {
  article: ArticleSummary;
}

export default function ArticleListCard({ article }: ArticleListCardProps) {
  return (
    <article className="grid grid-cols-[120px_1fr] items-start gap-4 border-b border-border py-6 sm:grid-cols-[180px_1fr] sm:gap-6">
      <ArticleMedia
        image={article.image}
        sizes="180px"
        className="aspect-[4/3] rounded-lg"
      />
      <div>
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-secondary">
          {article.categoryLabel}
        </p>
        <h3 className="mb-2 text-[clamp(18px,2.5vw,22px)] font-semibold leading-[1.3] tracking-[-0.02em]">
          <Link href={article.href} className="hover:text-accent">
            {article.title}
          </Link>
        </h3>
        <p className="mb-2 hidden text-[15px] leading-[1.55] text-secondary sm:block">
          {article.description}
        </p>
        <time dateTime={article.publishedAt} className="text-sm text-secondary">
          {formatArticleDate(article.publishedAt)}
        </time>
      </div>
    </article>
  );
}
