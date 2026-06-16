import type { Metadata } from 'next';
import { getSiteName } from '../../lib/site';

const updatedAt = '2026-06-14';

export const metadata: Metadata = {
  title: `Disclaimer | ${getSiteName()}`,
  description: 'Affiliate and editorial disclaimer for Affiliate Intelligence.',
  alternates: {
    canonical: '/disclaimer/',
  },
};

export default function DisclaimerPage() {
  return (
    <div className="layout-container py-16">
      <div className="max-w-3xl space-y-8">
        <header className="space-y-3">
          <h1 className="text-4xl font-bold font-display">Disclaimer</h1>
          <p className="text-sm text-gray-400">Last updated: {updatedAt}</p>
        </header>

        <section className="space-y-6 text-gray-300">
          <div className="space-y-2">
            <h2 className="text-2xl font-bold font-display text-text">
              Affiliate disclosure
            </h2>
            <p>
              Some links on this site are affiliate links marked with sponsored
              relationship attributes. If you sign up or purchase through these
              links, we may earn a commission at no extra cost to you.
            </p>
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold font-display text-text">
              Editorial independence
            </h2>
            <p>
              Reviews and comparisons are written independently. Affiliate
              relationships do not buy rankings, placements, or favorable
              coverage.
            </p>
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold font-display text-text">
              No guarantees
            </h2>
            <p>
              Software products change quickly. Pricing, features, and support
              quality can shift after publication, so verify current details
              with each vendor before making decisions.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
