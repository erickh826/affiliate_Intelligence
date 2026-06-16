import type { Metadata } from 'next';
import Link from 'next/link';
import { Fragment } from 'react';
import { notFound } from 'next/navigation';
import { MDXRemote } from 'next-mdx-remote/rsc';
import { mdxComponents } from '../../../lib/mdx-components';
import {
  getAllArticles,
  getFAQBySlug,
  getMDXDataBySlug,
} from '../../../lib/mdx';
import { getSiteName } from '../../../lib/site';
import { resolveCTAConfig } from '../../../lib/cta_injector';
import {
  buildArticleSchema,
  buildBreadcrumbSchema,
  buildFaqSchema,
} from '../../../lib/schema_builder';
import Breadcrumb from '../../../components/Breadcrumb';
import AffiliateCTA from '../../../components/AffiliateCTA';
import NewsletterCTA from '../../../components/NewsletterCTA';
import TableOfContents from '../../../components/TableOfContents';
import YouTubeEmbed from '../../../components/YouTubeEmbed';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';

export async function generateStaticParams() {
  const articles = await getAllArticles();
  return articles.map((article) => ({
    category: article.frontmatter.category,
    slug: article.frontmatter.slug,
  }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ category: string; slug: string }>;
}): Promise<Metadata> {
  const { category, slug } = await params;
  const article = await getMDXDataBySlug(category, slug);
  const siteName = getSiteName();

  if (!article) return { title: siteName };

  const { title, description } = article.frontmatter;
  const canonical = `${SITE_URL}/${category}/${slug}/`;

  return {
    title: `${title} | ${siteName}`,
    description,
    alternates: { canonical },
    openGraph: {
      title,
      description,
      type: 'article',
      url: canonical,
    },
  };
}

export default async function ArticlePage({
  params,
}: {
  params: Promise<{ category: string; slug: string }>;
}) {
  const { category, slug } = await params;
  const article = await getMDXDataBySlug(category, slug);

  if (!article) notFound();

  const faqData = await getFAQBySlug(slug);
  const ctaConfig = resolveCTAConfig(slug);
  const { contentParts, headings } = article;
  const articleSchema = buildArticleSchema(article.frontmatter, SITE_URL);
  const breadcrumbSchema = buildBreadcrumbSchema(
    category,
    slug,
    article.frontmatter.title,
    SITE_URL,
  );
  const faqSchema = faqData ? buildFaqSchema(faqData, SITE_URL) : null;

  return (
    <div className="layout-container py-12">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
      />
      {faqSchema && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
        />
      )}

      <Breadcrumb
        category={category}
        slug={slug}
        title={article.frontmatter.title}
      />

      <div className="lg:grid lg:grid-cols-[720px_1fr] lg:gap-12 lg:items-start">
        <div className="min-w-0">
          <header className="mb-8">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 leading-tight">
              {article.frontmatter.title}
            </h1>
            <div className="flex flex-wrap items-center text-sm text-gray-400 gap-y-2 gap-x-4">
              <Link
                href="/about"
                className="hover:text-accent transition-colors"
              >
                {article.frontmatter.author}
              </Link>
              <span className="hidden sm:inline">•</span>
              <time dateTime={article.frontmatter.published_at}>
                {new Date(article.frontmatter.published_at).toLocaleDateString(
                  'en-US',
                  {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  },
                )}
              </time>
              {article.frontmatter.last_reviewed && (
                <>
                  <span className="hidden sm:inline">•</span>
                  <span>
                    Last reviewed: {article.frontmatter.last_reviewed}
                  </span>
                </>
              )}
            </div>
          </header>

          {ctaConfig ? (
            <AffiliateCTA placement="top" {...ctaConfig} />
          ) : (
            <NewsletterCTA />
          )}

          <div className="prose prose-invert prose-teal max-w-none">
            <MDXRemote source={contentParts[0]} components={mdxComponents} />

            {contentParts[1] && (
              <MDXRemote source={contentParts[1]} components={mdxComponents} />
            )}

            <YouTubeEmbed />

            {contentParts.slice(2).map((part, i, arr) => (
              <Fragment key={i + 2}>
                <MDXRemote source={part} components={mdxComponents} />
                {i === 0 && arr.length > 1 && ctaConfig && (
                  <AffiliateCTA placement="inline" {...ctaConfig} />
                )}
              </Fragment>
            ))}
          </div>

          {ctaConfig ? (
            <AffiliateCTA placement="bottom" {...ctaConfig} />
          ) : (
            <NewsletterCTA />
          )}

          {faqData && faqData.faqs.length > 0 && (
            <section className="mt-16 border-t border-surface pt-12">
              <h2 className="text-3xl font-bold mb-8 font-display">
                Frequently Asked Questions
              </h2>
              <div className="space-y-8">
                {faqData.faqs.map((faq, index) => (
                  <div
                    key={index}
                    className="bg-surface p-6 rounded-lg border border-gray-800"
                  >
                    <h3 className="text-xl font-bold mb-2 font-display">
                      {faq.question}
                    </h3>
                    <p className="text-gray-300">
                      {faq.answer || 'Answer coming soon.'}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {article.frontmatter.intent === 'comparison' && (
            <div className="fixed bottom-0 left-0 right-0 bg-surface/95 backdrop-blur border-t border-gray-700 py-3 px-4 text-xs text-gray-400 text-center z-50">
              This page contains affiliate links. We may earn a commission at no
              cost to you.{' '}
              <Link href="/disclaimer" className="text-accent hover:underline">
                Learn more
              </Link>
            </div>
          )}
        </div>

        <aside className="hidden lg:block mt-0">
          <div className="sticky top-8 space-y-6">
            <TableOfContents headings={headings} />
          </div>
        </aside>
      </div>
    </div>
  );
}
