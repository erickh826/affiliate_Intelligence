import Link from 'next/link';
import { formatArticleDate, type ArticleSummary } from '../../lib/blog-listing';
import ArticleMedia from './ArticleMedia';

interface ArticleGridCardProps {
  article: ArticleSummary;
}

export default function ArticleGridCard({ article }: ArticleGridCardProps) {
  return (
    <article className="content-auto flex flex-col gap-3">
      <ArticleMedia
        image={article.image}
        sizes="(min-width: 1024px) 360px, (min-width: 640px) 50vw, 100vw"
        className="aspect-video rounded-lg"
      />
      <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-secondary">
        {article.categoryLabel}
      </p>
      <h3 className="text-xl font-semibold leading-[1.3] tracking-[-0.02em]">
        <Link href={article.href} className="hover:text-accent">
          {article.title}
        </Link>
      </h3>
      <time dateTime={article.publishedAt} className="text-sm text-secondary">
        {formatArticleDate(article.publishedAt)}
      </time>
      <Link
        href={article.href}
        className="inline-flex w-fit items-center gap-1.5 text-[15px] font-semibold text-accent hover:underline"
      >
        Read <span aria-hidden="true">→</span>
      </Link>
    </article>
  );
}
