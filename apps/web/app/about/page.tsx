import type { Metadata } from 'next';
import { getSiteName } from '../../lib/site';

const authorName = process.env.NEXT_PUBLIC_AUTHOR_NAME ?? 'The Editor';
const linkedInUrl = process.env.NEXT_PUBLIC_LINKEDIN_URL ?? '#';

export const metadata: Metadata = {
  title: `About | ${getSiteName()}`,
  description:
    'Learn about the author and editorial approach behind Affiliate Intelligence.',
  alternates: {
    canonical: '/about/',
  },
};

export default function AboutPage() {
  return (
    <div className="layout-container py-16">
      <div className="max-w-3xl space-y-8">
        <header className="space-y-3">
          <h1 className="text-4xl font-bold font-display">About</h1>
          <p className="text-lg text-gray-400">
            Affiliate Intelligence publishes researched comparisons, reviews,
            and practical guidance for AI tools.
          </p>
        </header>

        <section className="grid gap-6 rounded-xl border border-gray-800 bg-surface p-6 md:grid-cols-[160px_1fr]">
          <div className="aspect-square rounded-lg border border-dashed border-gray-700 bg-background/60 flex items-center justify-center text-sm text-gray-500">
            Photo placeholder
          </div>
          <div className="space-y-4">
            <h2 className="text-2xl font-bold font-display">{authorName}</h2>
            <p className="text-gray-300">
              {authorName} is an LLM developer and AI tools researcher focused
              on evaluating real-world workflows, pricing tradeoffs, and
              integration constraints across fast-moving software products.
            </p>
            <p className="text-gray-300">
              Editorial reviews prioritize hands-on evaluation, source
              validation, and practical buying guidance over vendor marketing
              claims.
            </p>
            <a
              href={linkedInUrl}
              className="inline-flex text-accent hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              LinkedIn profile
            </a>
          </div>
        </section>
      </div>
    </div>
  );
}
