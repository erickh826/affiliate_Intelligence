import { linkDisclosure, type ProgramType } from '../lib/affiliates';

interface AffiliateCTAProps {
  href: string;
  text: string;
  partner: string;
  placement: 'top' | 'inline' | 'bottom';
  promoCode?: string;
  linkType?: ProgramType;
  disclosure?: string;
}

export default function AffiliateCTA({
  href,
  text,
  partner,
  placement,
  promoCode,
  linkType = 'affiliate',
  disclosure,
}: AffiliateCTAProps) {
  const code = promoCode?.trim();
  const referral = linkType === 'referral';
  const line = disclosure?.trim() || linkDisclosure(linkType);
  const promo = !referral && code ? ` Promo code: ${code}.` : '';

  if (placement === 'top') {
    return (
      <div className="my-6 p-4 bg-accent/10 border border-accent/30 rounded-lg flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <a
          href={href}
          rel="sponsored noopener noreferrer"
          target="_blank"
          className="inline-block bg-accent hover:bg-accent/80 text-white font-semibold px-5 py-2 rounded transition-colors shrink-0"
        >
          {text}
        </a>
        <p className="text-xs text-secondary">
          {line}
          {referral ? null : (
            <>
              {' '}
              <span className="capitalize">
                {partner.replace(/_/g, ' ')}
              </span>{' '}
              is an affiliate partner.
            </>
          )}
          {promo}
        </p>
      </div>
    );
  }

  return (
    <div className="my-8 p-5 bg-surface border border-border rounded-lg">
      <p className="text-sm text-secondary mb-3">
        {line}
        {promo}
      </p>
      <a
        href={href}
        rel="sponsored noopener noreferrer"
        target="_blank"
        className="inline-block bg-accent hover:bg-accent/80 text-white font-semibold px-5 py-2 rounded transition-colors"
      >
        {text}
      </a>
    </div>
  );
}
