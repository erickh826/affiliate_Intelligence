import type { Metadata } from 'next';
import { getSiteName } from '../../lib/site';

const formId = process.env.NEXT_PUBLIC_FORMSPREE_ID;
const formAction = formId ? `https://formspree.io/f/${formId}` : '#';

export const metadata: Metadata = {
  title: `Contact | ${getSiteName()}`,
  description: 'Contact the Affiliate Intelligence editorial team.',
  alternates: {
    canonical: '/contact/',
  },
};

export default function ContactPage() {
  return (
    <div className="layout-container py-16">
      <div className="max-w-3xl space-y-8">
        <header className="space-y-3">
          <h1 className="text-4xl font-bold font-display">Contact</h1>
          <p className="text-lg text-gray-400">
            Send editorial questions, corrections, or partnership enquiries.
          </p>
        </header>

        <form
          action={formAction}
          method="POST"
          className="space-y-5 rounded-xl border border-gray-800 bg-surface p-6"
        >
          <div className="space-y-2">
            <label
              htmlFor="name"
              className="block text-sm font-medium text-gray-200"
            >
              Name
            </label>
            <input
              id="name"
              name="name"
              type="text"
              className="w-full rounded-lg border border-gray-700 bg-background px-4 py-3 text-text outline-none focus:border-accent"
              required
            />
          </div>
          <div className="space-y-2">
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-200"
            >
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              className="w-full rounded-lg border border-gray-700 bg-background px-4 py-3 text-text outline-none focus:border-accent"
              required
            />
          </div>
          <div className="space-y-2">
            <label
              htmlFor="message"
              className="block text-sm font-medium text-gray-200"
            >
              Message
            </label>
            <textarea
              id="message"
              name="message"
              rows={6}
              className="w-full rounded-lg border border-gray-700 bg-background px-4 py-3 text-text outline-none focus:border-accent"
              required
            />
          </div>
          <button
            type="submit"
            className="rounded-lg bg-accent px-5 py-3 font-semibold text-white transition-colors hover:bg-accent/80"
          >
            Send message
          </button>
          {!formId && (
            <p className="text-sm text-gray-400">
              Form endpoint not configured. Use{' '}
              <a
                href="mailto:editor@example.com"
                className="text-accent hover:underline"
              >
                editor@example.com
              </a>{' '}
              for now.
            </p>
          )}
        </form>
      </div>
    </div>
  );
}
