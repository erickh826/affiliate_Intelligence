interface AffiliateCTAProps {
  href: string;
  text: string;
  partner: string;
  placement: 'top' | 'inline' | 'bottom';
}

export default function AffiliateCTA({
  href,
  text,
  partner,
  placement,
}: AffiliateCTAProps) {
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
        <p className="text-xs text-gray-400">
          We may earn a commission if you click this link.{' '}
          <span className="capitalize">{partner.replace(/_/g, ' ')}</span> is an
          affiliate partner.
        </p>
      </div>
    );
  }

  return (
    <div className="my-8 p-5 bg-surface border border-gray-700 rounded-lg">
      <p className="text-sm text-gray-400 mb-3">
        We may earn a commission if you click this link.
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
