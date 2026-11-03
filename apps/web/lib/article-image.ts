import fs from 'fs';
import path from 'path';
import { articleCoverAlt, coverImagePath } from './cover';
import type { Frontmatter } from './mdx';

const PUBLIC_DIR = path.resolve(process.cwd(), 'public');

export function resolveArticleImage(
  frontmatter: Pick<Frontmatter, 'image'>,
): string | null {
  const raw = frontmatter.image?.trim();
  if (
    !raw ||
    !raw.startsWith('/') ||
    raw.includes('..') ||
    raw.includes('\\')
  ) {
    return null;
  }

  const resolved = path.resolve(PUBLIC_DIR, `.${raw}`);
  if (!resolved.startsWith(`${PUBLIC_DIR}${path.sep}`)) return null;
  if (!fs.existsSync(resolved)) return null;

  try {
    if (!fs.statSync(resolved).isFile()) return null;
  } catch {
    return null;
  }

  return raw;
}

export function articleDisplayImage(
  frontmatter: Pick<Frontmatter, 'image' | 'title' | 'slug' | 'category'>,
): { src: string; alt: string } {
  return {
    src:
      resolveArticleImage(frontmatter) ??
      coverImagePath(frontmatter.category, frontmatter.slug),
    alt: articleCoverAlt(frontmatter.title, frontmatter.slug),
  };
}
