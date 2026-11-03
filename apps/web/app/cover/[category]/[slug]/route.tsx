import { readFileSync } from 'fs';
import path from 'path';
import { ImageResponse } from 'next/og';
import CoverCard from '../../../../components/cover/CoverCard';
import { categoryLabel } from '../../../../lib/blog-listing';
import {
  COVER_HEIGHT,
  COVER_WIDTH,
  buildCoverModel,
} from '../../../../lib/cover';
import { getAllArticles, getMDXDataBySlug } from '../../../../lib/mdx';
import { getBrandName } from '../../../../lib/site-nav';

export const dynamicParams = false;

const SLUG = /^[a-z0-9-]+$/;

function coverFont(): ArrayBuffer {
  const file = readFileSync(
    path.join(process.cwd(), 'app/fonts/inter-latin-700-normal.woff'),
  );
  return file.buffer.slice(file.byteOffset, file.byteOffset + file.byteLength);
}

const fontData = coverFont();

export async function generateStaticParams() {
  const articles = await getAllArticles({ includeDrafts: true });
  return articles.map((article) => ({
    category: article.frontmatter.category,
    slug: article.frontmatter.slug,
  }));
}

export async function GET(
  _request: Request,
  context: { params: Promise<{ category: string; slug: string }> },
) {
  const { category, slug } = await context.params;
  if (!SLUG.test(category) || !SLUG.test(slug)) {
    return new Response('Not found', { status: 404 });
  }

  const article = await getMDXDataBySlug(category, slug);
  if (!article) return new Response('Not found', { status: 404 });

  const model = buildCoverModel({
    title: article.frontmatter.title,
    slug: article.frontmatter.slug,
    category: article.frontmatter.category,
    categoryLabel: categoryLabel(article.frontmatter.category),
    brand: getBrandName(),
  });

  return new ImageResponse(<CoverCard model={model} />, {
    width: COVER_WIDTH,
    height: COVER_HEIGHT,
    fonts: [
      {
        name: 'Inter',
        data: fontData,
        weight: 700,
        style: 'normal',
      },
    ],
  });
}
