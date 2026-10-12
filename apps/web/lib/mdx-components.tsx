import type { ComponentPropsWithoutRef } from 'react';
import AffiliateCTA from '../components/AffiliateCTA';
import { getProgram } from './affiliates';
import { ctaFromProgram } from './cta_injector';

type HeadingProps = ComponentPropsWithoutRef<'h2'>;
type SubheadingProps = ComponentPropsWithoutRef<'h3'>;

function ArticleAffiliateCTA({ partner }: { partner?: string }) {
  const cta = ctaFromProgram(getProgram(partner));
  if (!cta) return null;
  return <AffiliateCTA placement="inline" {...cta} />;
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
      <h2 {...props} tabIndex={-1} className="scroll-mt-28 font-display">
        {children}
      </h2>
    );
  },
  h3: ({ children, ...props }: SubheadingProps) => (
    <h3 {...props} tabIndex={-1} className="scroll-mt-28 font-display">
      {children}
    </h3>
  ),
  AffiliateCTA: ArticleAffiliateCTA,
};
