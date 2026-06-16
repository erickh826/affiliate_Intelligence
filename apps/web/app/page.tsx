import type { Metadata } from 'next';
import { getAllArticles } from '../lib/mdx';
import ArticleCard from '../components/ArticleCard';
import Link from 'next/link';
import { getSiteName } from '../lib/site';

export const metadata: Metadata = {
  title: getSiteName(),
  description: 'In-depth comparisons and reviews of AI tools.',
  alternates: {
    canonical: '/',
  },
};

export default async function HomePage() {
  const allArticles = await getAllArticles();
  const sorted = [...allArticles].sort((a, b) =>
    b.frontmatter.published_at.localeCompare(a.frontmatter.published_at),
  );
  const latest = sorted.slice(0, 6);
  const categories = [
    ...new Set(allArticles.map((a) => a.frontmatter.category)),
  ];

  return (
    <div className="layout-container py-20">
      <h1 className="text-5xl md:text-6xl font-bold mb-4 font-display text-accent">
        AI Tools Intelligence
      </h1>
      <p className="text-xl text-gray-400 max-w-2xl mb-16">
        In-depth comparisons and reviews of AI tools — researched, tested, and
        updated regularly.
      </p>

      {categories.length > 0 && (
        <section className="mb-16">
          <h2 className="text-2xl font-bold mb-6 font-display">
            Browse by Category
          </h2>
          <div className="flex flex-wrap gap-3">
            {categories.map((cat) => (
              <Link
                key={cat}
                href={`/${cat}`}
                className="px-5 py-2.5 border border-gray-700 rounded-lg capitalize hover:border-accent hover:text-accent transition-colors text-sm font-medium"
              >
                {cat.replace(/-/g, ' ')}
              </Link>
            ))}
          </div>
        </section>
      )}

      {latest.length > 0 && (
        <section>
          <h2 className="text-2xl font-bold mb-6 font-display">
            Latest Articles
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {latest.map((article) => (
              <ArticleCard
                key={article.frontmatter.slug}
                frontmatter={article.frontmatter}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
