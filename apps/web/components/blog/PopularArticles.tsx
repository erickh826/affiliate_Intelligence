import ArticleGridCard from './ArticleGridCard';
import ArticleListCard from './ArticleListCard';
import type { ArticleSummary } from '../../lib/blog-listing';

interface PopularArticlesProps {
  grid: ArticleSummary[];
  list: ArticleSummary[];
}

export default function PopularArticles({ grid, list }: PopularArticlesProps) {
  const isEmpty = grid.length === 0 && list.length === 0;

  return (
    <section
      id="popular"
      className="scroll-mt-20 py-12"
      aria-labelledby="popular-heading"
    >
      <div className="layout-container">
        <div className="mb-6 flex items-baseline justify-between gap-4">
          <h2
            id="popular-heading"
            className="text-[clamp(24px,3vw,32px)] font-bold tracking-[-0.02em]"
          >
            Popular articles
          </h2>
        </div>

        {isEmpty ? (
          <p className="text-base text-secondary">
            More articles will appear here.
          </p>
        ) : (
          <>
            {grid.length > 0 && (
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {grid.map((article) => (
                  <ArticleGridCard key={article.slug} article={article} />
                ))}
              </div>
            )}
            {list.length > 0 && (
              <div
                className="mt-8 flex flex-col border-t border-border"
                aria-label="More articles"
              >
                {list.map((article) => (
                  <ArticleListCard key={article.slug} article={article} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
