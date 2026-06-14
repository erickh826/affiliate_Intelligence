import type { Heading } from '../lib/mdx';

interface TableOfContentsProps {
  headings: Heading[];
}

export default function TableOfContents({ headings }: TableOfContentsProps) {
  if (headings.length === 0) return null;

  return (
    <nav className="text-sm" aria-label="Table of contents">
      <p className="font-semibold text-gray-300 mb-3 uppercase tracking-wide text-xs">
        Contents
      </p>
      <ol className="space-y-2">
        {headings.map((h) => (
          <li key={h.id} style={{ paddingLeft: h.level === 3 ? '0.75rem' : '0' }}>
            <a
              href={`#${h.id}`}
              className="text-gray-400 hover:text-accent transition-colors leading-snug"
            >
              {h.text}
            </a>
          </li>
        ))}
      </ol>
    </nav>
  );
}
