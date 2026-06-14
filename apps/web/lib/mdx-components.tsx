import type { ComponentPropsWithoutRef } from 'react';

type HeadingProps = ComponentPropsWithoutRef<'h2'>;
type SubheadingProps = ComponentPropsWithoutRef<'h3'>;

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
};
