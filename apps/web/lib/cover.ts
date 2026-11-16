export const COVER_WIDTH = 1200;
export const COVER_HEIGHT = 630;

const ACCENTS: Record<string, string> = {
  'ai-writing': '#2563eb',
  seo: '#0f766e',
  'ai-video': '#7c3aed',
  'ai-productivity': '#c2410c',
  'ai-code': '#15803d',
  'ai-image': '#be185d',
};

const SMALL_WORDS = new Set([
  'vs',
  'and',
  'for',
  'the',
  'with',
  'your',
  'from',
]);

export function categoryAccent(category: string): string {
  return ACCENTS[category] ?? '#2563eb';
}

export function articleKeyword(slug: string): string {
  return slug.replace(/-/g, ' ').replace(/\s+/g, ' ').trim();
}

export function articleCoverAlt(title: string, slug: string): string {
  const keyword = articleKeyword(slug);
  return `Cover image for ${title}. Article about ${keyword}.`;
}

export function coverImagePath(category: string, slug: string): string {
  return `/cover/${category}/${slug}`;
}

export function coverTitle(title: string): string {
  const trimmed = title.trim().replace(/\s+/g, ' ');
  if (trimmed.length <= 140) return trimmed;
  return `${trimmed.slice(0, 137).trimEnd()}...`;
}

export function coverTitleSize(title: string): number {
  if (title.length > 90) return 40;
  if (title.length > 64) return 48;
  if (title.length > 42) return 56;
  return 64;
}

function stripYear(value: string): string {
  return value.replace(/\s+\d{4}$/, '').trim();
}

export function coverToolLabel(title: string, categoryName: string): string {
  const head = title.split(':')[0]?.trim() || title.trim();
  const howTo = head.match(/^how to use\s+(.+)$/i);
  if (howTo?.[1]) return stripYear(howTo[1]);
  const versus = head.match(/^(.+?)\s+vs\.?\s+(.+)$/i);
  if (versus?.[1] && versus[2]) {
    return `${stripYear(versus[1])} vs ${stripYear(versus[2])}`;
  }
  const review = head.match(/^(.+?)\s+review\b/i);
  if (review?.[1]) return stripYear(review[1]);
  return categoryName;
}

export function coverMonogram(label: string): string {
  const words = label
    .split(/\s+/)
    .filter((word) => word.length > 1 && !SMALL_WORDS.has(word.toLowerCase()));
  const source = words.length > 0 ? words : label.split(/\s+/).filter(Boolean);
  const letters = source
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase() ?? '')
    .join('');
  return letters || 'AI';
}

export interface CoverModel {
  title: string;
  displayTitle: string;
  keyword: string;
  categoryLabel: string;
  toolLabel: string;
  monogram: string;
  accent: string;
  brand: string;
  alt: string;
}

export function buildCoverModel(input: {
  title: string;
  slug: string;
  category: string;
  categoryLabel: string;
  brand: string;
}): CoverModel {
  const toolLabel = coverToolLabel(input.title, input.categoryLabel);
  return {
    title: input.title,
    displayTitle: coverTitle(input.title),
    keyword: articleKeyword(input.slug),
    categoryLabel: input.categoryLabel,
    toolLabel,
    monogram: coverMonogram(toolLabel),
    accent: categoryAccent(input.category),
    brand: input.brand.trim() || 'Shadona',
    alt: articleCoverAlt(input.title, input.slug),
  };
}
