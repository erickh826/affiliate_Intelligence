import { headingId, type Heading } from './mdx';

export interface TocNode {
  id: string;
  text: string;
  level: number;
  children: TocNode[];
}

interface ParsedHeading extends Heading {
  line: number;
}

const HEADING_RE = /^(#{1,3})[ \t]+(.+?)[ \t]*$/;

function parseDocumentHeadings(content: string): ParsedHeading[] {
  const seen = new Map<string, number>();
  const headings: ParsedHeading[] = [];
  const lines = content.split('\n');

  lines.forEach((line, lineNo) => {
    const match = line.match(HEADING_RE);
    if (!match) return;
    const level = match[1].length;
    const text = match[2].trim();
    const id = level >= 2 ? headingId(text, seen) : '';
    headings.push({ id, text, level, line: lineNo });
  });

  return headings;
}

function isAdjacentDuplicate(
  lines: string[],
  current: ParsedHeading,
  next: ParsedHeading,
): boolean {
  if (current.text !== next.text) return false;
  for (let line = current.line + 1; line < next.line; line += 1) {
    if (lines[line].trim() !== '') return false;
  }
  return true;
}

function toNode(heading: ParsedHeading): TocNode {
  return {
    id: heading.id,
    text: heading.text,
    level: heading.level,
    children: [],
  };
}

function nestByLevel(headings: ParsedHeading[]): TocNode[] {
  const roots: TocNode[] = [];
  let currentH2: TocNode | null = null;

  for (const heading of headings) {
    if (!heading.id) continue;
    const node = toNode(heading);
    if (heading.level <= 2 || !currentH2) {
      roots.push(node);
      currentH2 = heading.level === 2 ? node : null;
      continue;
    }
    currentH2.children.push(node);
  }

  return roots;
}

function nestSections(
  headings: ParsedHeading[],
  openerIndexes: Set<number>,
  skipIndexes: Set<number>,
): TocNode[] {
  const roots: TocNode[] = [];
  let section: TocNode | null = null;
  let currentH2: TocNode | null = null;

  headings.forEach((heading, index) => {
    if (skipIndexes.has(index)) return;

    if (openerIndexes.has(index)) {
      const node = toNode(heading);
      const duplicate = headings[index + 1];
      if (!node.id && duplicate?.id) node.id = duplicate.id;
      if (!node.id) return;
      roots.push(node);
      section = node;
      currentH2 = null;
      return;
    }

    if (heading.level < 2 || !heading.id) return;

    const node = toNode(heading);
    if (!section) {
      roots.push(node);
      currentH2 = heading.level === 2 ? node : null;
      return;
    }

    if (heading.level >= 3 && currentH2) {
      currentH2.children.push(node);
      return;
    }

    section.children.push(node);
    currentH2 = heading.level === 2 ? node : null;
  });

  return roots;
}

export function buildTableOfContents(content: string): TocNode[] {
  const lines = content.split('\n');
  const headings = parseDocumentHeadings(content);
  const openerIndexes = new Set<number>();
  const skipIndexes = new Set<number>();

  for (let index = 0; index < headings.length - 1; index += 1) {
    if (headings[index].level > 2) continue;
    if (!isAdjacentDuplicate(lines, headings[index], headings[index + 1])) {
      continue;
    }
    openerIndexes.add(index);
    skipIndexes.add(index + 1);
  }

  if (openerIndexes.size === 0) {
    return nestByLevel(headings.filter((heading) => heading.level >= 2));
  }

  return nestSections(headings, openerIndexes, skipIndexes);
}

export function flattenToc(nodes: TocNode[]): TocNode[] {
  const flat: TocNode[] = [];
  const walk = (items: TocNode[]) => {
    for (const item of items) {
      flat.push(item);
      walk(item.children);
    }
  };
  walk(nodes);
  return flat;
}
