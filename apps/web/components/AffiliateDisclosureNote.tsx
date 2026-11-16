import Link from 'next/link';
import { articleDisclosureText, type DisclosureKind } from '../lib/affiliates';

export const AFFILIATE_DISCLOSURE_PATH = '/affiliate-disclosure';

export default function AffiliateDisclosureNote({
  kind = 'affiliate',
}: {
  kind?: DisclosureKind;
}) {
  return (
    <p className="mb-6 text-sm text-secondary">
      {articleDisclosureText(kind)}{' '}
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
