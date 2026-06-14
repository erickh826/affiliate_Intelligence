import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';

export interface Frontmatter {
  title: string;
  description: string;
  slug: string;
  category: string;
  intent: string;
  published_at: string;
  last_reviewed: string;
  author: string;
  affiliate_partner: string | null;
  schema_type: string;
}

export interface Heading {
  id: string;
  text: string;
  level: number;
}

export interface MDXData {
  frontmatter: Frontmatter;
  content: string;
  contentParts: string[];
  headings: Heading[];
  filePath: string;
}

export interface FAQItem {
  question: string;
  answer: string;
}

export interface FAQData {
  faqs: FAQItem[];
  slug: string;
}

const CONTENT_PATH = path.join(process.cwd(), 'content');
const SKIP_CONTENT_DIRS = new Set(['faq']);

export function getHeadings(content: string): Heading[] {
  const headings: Heading[] = [];
  for (const line of content.split('\n')) {
    const h2 = line.match(/^## (.+)/);
    const h3 = line.match(/^### (.+)/);
    if (h2) {
      const text = h2[1].trim();
      headings.push({
        id: text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''),
        text,
        level: 2,
      });
    } else if (h3) {
      const text = h3[1].trim();
      headings.push({
        id: text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''),
        text,
        level: 3,
      });
    }
  }
  return headings;
}

export function splitAtH2(content: string): string[] {
  const parts = content.split(/(?=^## )/m);
  return parts.length > 0 ? parts : [content];
}

export async function getFAQBySlug(slug: string): Promise<FAQData | null> {
  const filePath = path.join(CONTENT_PATH, 'faq', `${slug}.faq.json`);
  if (!fs.existsSync(filePath)) return null;
  const fileContent = fs.readFileSync(filePath, 'utf8');
  return JSON.parse(fileContent);
}

export async function getMDXDataBySlug(
  category: string,
  slug: string,
): Promise<MDXData | null> {
  const filePath = path.join(CONTENT_PATH, category, `${slug}.mdx`);
  if (!fs.existsSync(filePath)) return null;
  const fileContent = fs.readFileSync(filePath, 'utf8');
  const { data, content } = matter(fileContent);

  return {
    frontmatter: data as Frontmatter,
    content,
    contentParts: splitAtH2(content),
    headings: getHeadings(content),
    filePath,
  };
}

export async function getAllArticles(): Promise<MDXData[]> {
  const categories = fs.readdirSync(CONTENT_PATH);
  const articles: MDXData[] = [];

  for (const category of categories) {
    if (SKIP_CONTENT_DIRS.has(category)) continue;
    const categoryPath = path.join(CONTENT_PATH, category);
    if (fs.statSync(categoryPath).isDirectory()) {
      const files = fs
        .readdirSync(categoryPath)
        .filter((file) => file.endsWith('.mdx'));
      for (const file of files) {
        const slug = file.replace('.mdx', '');
        const data = await getMDXDataBySlug(category, slug);
        if (data) articles.push(data);
      }
    }
  }

  return articles;
}
