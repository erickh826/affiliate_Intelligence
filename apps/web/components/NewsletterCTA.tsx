export default function NewsletterCTA() {
  return (
    <div className="my-6 p-5 bg-surface border border-border rounded-lg">
      <p className="font-semibold text-text mb-1">Stay updated</p>
      <p className="text-sm text-secondary mb-3">
        Get the latest AI tool comparisons and reviews.
      </p>
      <a
        href="#newsletter"
        className="inline-block bg-accent hover:bg-accent/80 text-white font-semibold px-5 py-2 rounded transition-colors"
      >
        Subscribe
      </a>
    </div>
  );
}
