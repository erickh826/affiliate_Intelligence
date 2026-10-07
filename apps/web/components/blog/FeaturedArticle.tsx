import Link from 'next/link';
import { formatArticleDate, type ArticleSummary } from '../../lib/blog-listing';

interface FeaturedArticleProps {
  article: ArticleSummary | null;
}

export default function FeaturedArticle({ article }: FeaturedArticleProps) {
  const title = article?.title ?? 'Guides for choosing AI tools';

  return (
    <section className="pb-8 pt-12" aria-labelledby="featured-title">
      <div className="layout-container">
        <div className="relative mb-6 grid min-h-[220px] items-end justify-items-start overflow-hidden rounded-xl bg-[#0a0a0a] p-8">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_70%_40%,rgba(37,99,235,0.45),transparent_60%),radial-gradient(ellipse_50%_40%_at_20%_80%,rgba(147,197,253,0.25),transparent_50%)]"
          />
          <div className="relative">
            <span className="mb-3 inline-block rounded border border-white/35 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-white">
              Featured
            </span>
            <h1
              id="featured-title"
              className="max-w-[28ch] text-balance text-[clamp(28px,4vw,44px)] font-bold leading-[1.15] tracking-[-0.03em] text-white"
            >
              {title}
            </h1>
          </div>
        </div>

        {article ? (
          <article>
            <div className="mb-3 flex flex-wrap items-baseline gap-3">
              <Link
                href={`/${article.category}`}
                className="text-[12px] font-semibold uppercase tracking-[0.06em] text-accent"
              >
                {article.categoryLabel}
              </Link>
              <time
                dateTime={article.publishedAt}
                className="text-sm text-secondary"
              >
                {formatArticleDate(article.publishedAt)}
              </time>
            </div>
            <h2 className="mb-3 text-[clamp(28px,3.5vw,40px)] font-bold leading-[1.2] tracking-[-0.03em]">
              <Link href={article.href} className="hover:text-accent">
                {article.title}
              </Link>
            </h2>
            <p className="mb-4 max-w-[62ch] text-base leading-[1.6] text-secondary">
              {article.description}
            </p>
            <Link
              href={article.href}
              className="inline-flex items-center gap-1.5 text-[15px] font-semibold text-accent hover:underline"
            >
              Read article <span aria-hidden="true">→</span>
            </Link>
          </article>
        ) : (
          <p className="max-w-[62ch] text-base leading-[1.6] text-secondary">
            Comparisons and reviews will appear here as they are published.
          </p>
        )}
      </div>
    </section>
  );
}
