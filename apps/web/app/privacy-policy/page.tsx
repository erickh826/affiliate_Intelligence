import type { Metadata } from 'next';
import { getSiteName } from '../../lib/site';

const updatedAt = '2026-06-14';

export const metadata: Metadata = {
  title: `Privacy Policy | ${getSiteName()}`,
  description:
    'Privacy policy for Affiliate Intelligence, including analytics and advertising disclosures.',
  alternates: {
    canonical: '/privacy-policy/',
  },
};

export default function PrivacyPolicyPage() {
  return (
    <div className="layout-container py-16">
      <div className="max-w-3xl space-y-8">
        <header className="space-y-3">
          <h1 className="text-4xl font-bold font-display">Privacy Policy</h1>
          <p className="text-sm text-gray-400">Last updated: {updatedAt}</p>
        </header>

        <section className="space-y-6 text-gray-300">
          <p>
            Affiliate Intelligence collects limited usage data to understand how
            readers use the site and to improve editorial quality. We do not
            sell personal information.
          </p>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold font-display text-text">
              Analytics
            </h2>
            <p>
              We use Google Analytics 4 to measure visits, page performance, and
              engagement patterns. This may involve cookies or similar
              browser-side identifiers.
            </p>
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold font-display text-text">
              Advertising
            </h2>
            <p>
              Google AdSense may show ads based on your visits to this and other
              websites. For more information, review Google&apos;s advertising
              and privacy policies.
            </p>
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold font-display text-text">
              Cookies
            </h2>
            <p>
              You can disable cookies in your browser settings. Doing so may
              affect site functionality or analytics accuracy.
            </p>
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold font-display text-text">
              Contact
            </h2>
            <p>
              Questions about this policy can be sent through the contact page.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
