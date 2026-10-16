import Link from 'next/link';

export const AFFILIATE_DISCLOSURE_PATH = '/affiliate-disclosure';

export default function AffiliateDisclosureNote() {
  return (
    <p className="mb-6 text-sm text-secondary">
      This article contains affiliate links. We may earn a commission if you buy
      through them.{' '}
      <Link
        href={AFFILIATE_DISCLOSURE_PATH}
        className="text-accent hover:underline"
      >
        Affiliate disclosure
      </Link>
      .
    </p>
  );
}
