import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { evaluate } from '@mdx-js/mdx';
import matter from 'gray-matter';
import * as runtime from 'react/jsx-runtime';
import { renderToStaticMarkup } from 'react-dom/server';
import remarkGfm from 'remark-gfm';

const UNRESOLVED_LINK_RE = /\[([^\]]+)\]\(\{\{LINK_[A-Z0-9_]+\}\}\)/g;

function AffiliateCTA() {
  return null;
}

function Image() {
  return null;
}

const components = {
  AffiliateCTA,
  Image,
};

function neutralizeUnresolvedLinks(content) {
  return content.replace(UNRESOLVED_LINK_RE, '$1');
}

function splitAtH2(content) {
  const parts = content.split(/(?=^## )/m);
  return parts.length > 0 ? parts : [content];
}

function formatError(error) {
  const message = error instanceof Error ? error.message : String(error);
  return message.split('\n').slice(0, 12).join('\n');
}

async function renderMdx(source) {
  const evaluated = await evaluate(source, {
    ...runtime,
    remarkPlugins: [remarkGfm],
    useMDXComponents: () => components,
  });
  renderToStaticMarkup(evaluated.default({ components }));
}

function contentFiles(dir) {
  const files = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...contentFiles(full));
    } else if (entry.name.endsWith('.mdx')) {
      files.push(full);
    }
  }
  return files;
}

async function renderDocument(source) {
  const { content } = matter(source);
  const parts = splitAtH2(neutralizeUnresolvedLinks(content));
  for (const part of parts) {
    if (!part.trim()) continue;
    await renderMdx(part);
  }
}

async function renderStdin() {
  const source = readFileSync(0, 'utf8');
  await renderMdx(source);
}

async function renderContent() {
  const root = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    '../content',
  );
  const files = contentFiles(root).sort();
  if (files.length === 0) {
    console.error('no MDX files found');
    process.exit(1);
  }
  let failed = 0;
  for (const file of files) {
    const source = readFileSync(file, 'utf8');
    try {
      await renderDocument(source);
    } catch (error) {
      failed += 1;
      console.error(`FAIL ${path.relative(root, file)}`);
      console.error(formatError(error));
    }
  }
  if (failed > 0) {
    console.error(`${failed} MDX file(s) failed to render`);
    process.exit(1);
  }
  console.log(`rendered ${files.length} MDX files`);
}

if (process.argv.includes('--stdin')) {
  renderStdin().catch((error) => {
    console.error(formatError(error));
    process.exit(1);
  });
} else {
  renderContent().catch((error) => {
    console.error(formatError(error));
    process.exit(1);
  });
}
