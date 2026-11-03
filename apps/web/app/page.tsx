import type { Metadata } from 'next';
import FeaturedArticle from '../components/blog/FeaturedArticle';
import PopularArticles from '../components/blog/PopularArticles';
import TopicLinks from '../components/blog/TopicLinks';
import {
  splitBlogListing,
  toArticleSummary,
  topicLinksFromArticles,
} from '../lib/blog-listing';
import { getAllArticles } from '../lib/mdx';
import { getSiteName } from '../lib/site';

export const metadata: Metadata = {
  title: getSiteName(),
  description: 'In-depth comparisons and reviews of AI tools.',
  alternates: {
    canonical: '/',
  },
};

export default async function HomePage() {
  const articles = await getAllArticles();
  const listing = splitBlogListing(articles);
  const topics = topicLinksFromArticles(articles);
  const featured = listing.featured ? toArticleSummary(listing.featured) : null;
  const grid = listing.grid.map((article) => toArticleSummary(article));
  const list = listing.list.map((article) => toArticleSummary(article));

  return (
    <>
      <FeaturedArticle article={featured} />
      <TopicLinks topics={topics} />
      <PopularArticles grid={grid} list={list} />
    </>
  );
}
