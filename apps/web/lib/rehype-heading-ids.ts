import type { Node } from 'unist';
import type { Plugin } from 'unified';

interface ElementNode extends Node {
  tagName?: string;
  properties?: Record<string, unknown>;
  children?: ElementNode[];
}

function isElement(node: Node): node is ElementNode {
  return node.type === 'element';
}

export function rehypeHeadingIds(ids: string[]): Plugin {
  return () => (tree: Node) => {
    let index = 0;
    const walk = (node: Node) => {
      if (!isElement(node)) {
        const children = (node as ElementNode).children;
        children?.forEach(walk);
        return;
      }
      if (node.tagName === 'h2' || node.tagName === 'h3') {
        const id = ids[index];
        index += 1;
        if (id) {
          node.properties = { ...node.properties, id };
        }
      }
      node.children?.forEach(walk);
    };
    walk(tree);
  };
}
