'use client';

import { useId, useState } from 'react';
import type { TocNode } from '../lib/toc';

interface TableOfContentsProps {
  nodes: TocNode[];
}

interface TocListProps {
  nodes: TocNode[];
  depth: number;
}

function TocList({ nodes, depth }: TocListProps) {
  return (
    <ol className={depth === 0 ? 'space-y-1' : 'mt-1 space-y-1'}>
      {nodes.map((node) => (
        <TocEntry key={node.id} node={node} depth={depth} />
      ))}
    </ol>
  );
}

function TocEntry({ node, depth }: { node: TocNode; depth: number }) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const hasChildren = node.children.length > 0;

  return (
    <li>
      <div className="flex items-start gap-1">
        <a
          href={`#${node.id}`}
          className={
            depth === 0
              ? 'min-w-0 flex-1 py-1 text-[15px] font-medium leading-snug text-text hover:text-accent'
              : 'min-w-0 flex-1 py-1 text-sm leading-snug text-secondary hover:text-accent'
          }
        >
          {node.text}
        </a>
        {hasChildren ? (
          <button
            type="button"
            className="mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-secondary hover:bg-background hover:text-text"
            aria-expanded={open}
            aria-controls={panelId}
            aria-label={`${open ? 'Collapse' : 'Expand'} subsections for ${node.text}`}
            onClick={() => setOpen((value) => !value)}
          >
            <svg
              viewBox="0 0 16 16"
              aria-hidden="true"
              className={`h-3.5 w-3.5 motion-safe:transition-transform ${open ? 'rotate-90' : ''}`}
            >
              <path
                d="M6 3.5 10.5 8 6 12.5"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        ) : null}
      </div>
      {hasChildren ? (
        <div
          id={panelId}
          hidden={!open}
          className="ml-2 border-l border-border pl-3"
        >
          <TocList nodes={node.children} depth={depth + 1} />
        </div>
      ) : null}
    </li>
  );
}

export default function TableOfContents({ nodes }: TableOfContentsProps) {
  if (nodes.length === 0) return null;

  return (
    <nav
      aria-label="Table of contents"
      className="max-h-[70vh] overflow-y-auto rounded-xl border border-border bg-surface p-4 lg:max-h-[calc(100vh-9rem)]"
    >
      <p className="mb-3 text-xs font-semibold uppercase tracking-[0.08em] text-text">
        Contents
      </p>
      <TocList nodes={nodes} depth={0} />
    </nav>
  );
}
