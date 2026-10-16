import type { Metadata } from 'next';
import Link from 'next/link';
import { getSiteName } from '../../lib/site';

const updatedAt = '2026-10-12';

export const metadata: Metadata = {
  title: `Affiliate Disclosure | ${getSiteName()}`,
  description:
    'How affiliate links work on this site, including commissions and editorial independence.',
  alternates: {
    canonical: '/affiliate-disclosure/',
  },
};

export default function AffiliateDisclosurePage() {
  const siteName = getSiteName();

  return (
    <div className="layout-container py-16">
      <div className="max-w-3xl space-y-8">
        <header className="space-y-3">
          <h1 className="text-4xl font-bold font-display">
            Affiliate Disclosure
          </h1>
          <p className="text-sm text-secondary">Last updated: {updatedAt}</p>
        </header>

        <section className="space-y-6 text-secondary">
          <p>
            {siteName} is reader-supported. Some links on articles are affiliate
            links. If you sign up or buy through one of those links, we may earn
            a commission at no extra cost to you.
          </p>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold font-display text-text">
              How to recognise an affiliate link
            </h2>
            <p>
              Affiliate links use{' '}
              <span className="text-text">rel=&quot;sponsored&quot;</span>.
              Articles that include one also show a short disclosure at the top
              of the page, linking back here.
            </p>
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold font-display text-text">
              Editorial independence
            </h2>
            <p>
              Rankings, recommendations, and criticism are written
              independently. An affiliate relationship does not buy placement, a
              higher rating, or favorable coverage. We only link to a program
              after it is approved and the referral URL is added to the site
              configuration.
            </p>
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold font-display text-text">
              Programs we may recommend
            </h2>
            <p>
              Current categories include AI writing tools (Jasper, Writesonic,
              Copy.ai), SEO tools (Surfer SEO, Semrush, Ahrefs), AI voice and
              video (ElevenLabs, Descript), and productivity and automation
              (Notion, Zapier). A program appears in an article only when that
              program is enabled.
            </p>
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold font-display text-text">
              Privacy
            </h2>
            <p>
              Affiliate networks may set a cookie so they can attribute a
              signup. See the{' '}
              <Link
                href="/privacy-policy"
                className="text-accent hover:underline"
              >
                privacy policy
              </Link>{' '}
              for how this site handles analytics, advertising, and cookies.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
