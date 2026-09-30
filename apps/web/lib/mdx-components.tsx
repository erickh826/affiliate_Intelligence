import type { ComponentPropsWithoutRef } from 'react';
import AffiliateCTA from '../components/AffiliateCTA';
import { AFFILIATE_LINKS } from './affiliate-links';

type HeadingProps = ComponentPropsWithoutRef<'h2'>;
type SubheadingProps = ComponentPropsWithoutRef<'h3'>;

function ArticleAffiliateCTA({ partner }: { partner?: string }) {
  const key = (partner ?? '').trim();
  const href = AFFILIATE_LINKS[key];
  if (!href || !key) return null;
  const label = key.replace(/_/g, ' ');
  return (
    <AffiliateCTA
      href={href}
      text={`Try ${label} →`}
      partner={key}
      placement="inline"
    />
  );
}

export const mdxComponents = {
  h1: () => null,
  h2: ({ children, ...props }: HeadingProps) => {
    if (
      typeof children === 'string' &&
      children === 'Frequently Asked Questions'
    ) {
      return null;
    }
    return (
      <h2 {...props} className="font-display">
        {children}
      </h2>
    );
  },
  h3: ({ children, ...props }: SubheadingProps) => (
    <h3 {...props} className="font-display">
      {children}
    </h3>
  ),
  AffiliateCTA: ArticleAffiliateCTA,
};
