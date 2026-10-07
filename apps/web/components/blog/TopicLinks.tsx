import Link from 'next/link';
import { fallbackTopics, type TopicLink } from '../../lib/blog-listing';

interface TopicLinksProps {
  topics: TopicLink[];
}

export default function TopicLinks({ topics }: TopicLinksProps) {
  const links = topics.length > 0 ? topics : fallbackTopics;

  return (
    <section
      id="topics"
      className="scroll-mt-20 border-b border-border pb-8 pt-6"
      aria-labelledby="topics-heading"
    >
      <div className="layout-container">
        <h2
          id="topics-heading"
          className="mb-4 text-sm font-semibold tracking-[0.02em] text-secondary"
        >
          Browse by topic
        </h2>
        <div className="flex flex-wrap gap-3">
          {links.map((topic) => (
            <Link
              key={topic.href + topic.label}
              href={topic.href}
              className="inline-flex rounded-full border border-border bg-background px-[18px] py-2.5 text-sm font-semibold text-text transition-[border-color,background-color] duration-150 hover:border-accent hover:bg-surface motion-reduce:transition-none"
            >
              {topic.label}
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
