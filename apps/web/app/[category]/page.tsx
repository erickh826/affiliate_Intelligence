import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getAllArticles } from '../../lib/mdx';
import { getSiteName } from '../../lib/site';
import ArticleCard from '../../components/ArticleCard';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';

const PAGE_SIZE = 12;

export async function generateStaticParams() {
  const articles = await getAllArticles();
  const categories = [...new Set(articles.map((a) => a.frontmatter.category))];
  return categories.map((category) => ({ category }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ category: string }>;
}): Promise<Metadata> {
  const { category } = await params;
  const siteName = getSiteName();
  const label = category.replace(/-/g, ' ');
  return {
    title: `${label} | ${siteName}`,
    description: `Browse all ${label} articles.`,
    alternates: {
      canonical: `${SITE_URL}/${category}/`,
    },
  };
}

export default async function CategoryPage({
  params,
}: {
  params: Promise<{ category: string }>;
}) {
  const { category } = await params;
  const page = 1;

  const allArticles = await getAllArticles();
  const sorted = allArticles
    .filter((a) => a.frontmatter.category === category)
    .sort((a, b) =>
      b.frontmatter.published_at.localeCompare(a.frontmatter.published_at),
    );

  if (sorted.length === 0) notFound();

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);
  const articles = sorted.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const label = category.replace(/-/g, ' ');

  return (
    <div className="layout-container py-12">
      <header className="mb-10">
        <nav className="text-sm text-gray-500 mb-4">
          <Link href="/" className="hover:text-accent transition-colors">
            Home
          </Link>
          <span className="mx-2">/</span>
          <span className="text-gray-300 capitalize">{label}</span>
        </nav>
        <h1 className="text-4xl font-bold font-display capitalize">{label}</h1>
        <p className="text-gray-400 mt-2">{sorted.length} articles</p>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {articles.map((article) => (
          <ArticleCard
            key={article.frontmatter.slug}
            frontmatter={article.frontmatter}
          />
        ))}
      </div>

      {totalPages > 1 && (
        <nav
          className="mt-12 flex justify-center gap-4"
          aria-label="Pagination"
        >
          {page > 1 && (
            <Link
              href={`/${category}?page=${page - 1}`}
              rel="prev"
              className="px-4 py-2 border border-gray-700 rounded hover:border-accent transition-colors text-sm"
            >
              Previous
            </Link>
          )}
          <span className="px-4 py-2 text-sm text-gray-400">
            Page {page} of {totalPages}
          </span>
          {page < totalPages && (
            <Link
              href={`/${category}?page=${page + 1}`}
              rel="next"
              className="px-4 py-2 border border-gray-700 rounded hover:border-accent transition-colors text-sm"
            >
              Next
            </Link>
          )}
        </nav>
      )}
    </div>
  );
}
