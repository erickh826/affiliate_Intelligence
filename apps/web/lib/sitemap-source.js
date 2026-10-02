const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');

const SKIP_CONTENT_DIRS = new Set(['faq']);

function resolveSiteUrl() {
  const configured = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  if (configured) {
    return configured.replace(/\/+$/, '');
  }

  const productionHost = process.env.VERCEL_PROJECT_PRODUCTION_URL?.trim();
  if (productionHost) {
    const host = productionHost.replace(/^https?:\/\//, '').replace(/\/+$/, '');
    return `https://${host}`;
  }

  return 'http://localhost:3000';
}

function segment(value, fallback) {
  const raw =
    typeof value === 'string' && value.trim() ? value.trim() : fallback;
  if (!raw || raw.includes('/') || raw.includes('\\') || raw.includes('..')) {
    return null;
  }
  return raw;
}

function toLastMod(value) {
  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    return value.toISOString();
  }
  if (typeof value !== 'string' || !value.trim()) return undefined;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return undefined;
  return date.toISOString();
}

function listPublishedRoutes(contentDir) {
  if (!fs.existsSync(contentDir)) return [];

  const byCategory = new Map();
  const categories = fs.readdirSync(contentDir);

  for (const directory of categories) {
    if (SKIP_CONTENT_DIRS.has(directory)) continue;
    const categoryPath = path.join(contentDir, directory);
    if (!fs.statSync(categoryPath).isDirectory()) continue;

    const files = fs
      .readdirSync(categoryPath)
      .filter((file) => file.endsWith('.mdx'));

    for (const file of files) {
      const raw = fs.readFileSync(path.join(categoryPath, file), 'utf8');
      const { data } = matter(raw);
      const category = segment(data.category, directory);
      const slug = segment(data.slug, file.replace(/\.mdx$/, ''));
      if (!category || !slug) continue;

      const lastmod =
        toLastMod(data.last_reviewed) ?? toLastMod(data.published_at);
      const articles = byCategory.get(category) ?? [];
      articles.push({
        loc: `/${category}/${slug}`,
        lastmod,
        changefreq: 'weekly',
        priority: 0.8,
      });
      byCategory.set(category, articles);
    }
  }

  const routes = [];
  for (const [category, articles] of byCategory) {
    const lastmod = articles.reduce((latest, article) => {
      if (!article.lastmod) return latest;
      if (!latest || article.lastmod > latest) return article.lastmod;
      return latest;
    }, undefined);
    routes.push({
      loc: `/${category}`,
      lastmod,
      changefreq: 'weekly',
      priority: 0.6,
    });
    routes.push(...articles);
  }

  return routes;
}

module.exports = {
  resolveSiteUrl,
  listPublishedRoutes,
};
