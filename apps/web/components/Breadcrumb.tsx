import Link from 'next/link';

interface BreadcrumbProps {
  category: string;
  slug: string;
  title: string;
}

export default function Breadcrumb({ category, slug, title }: BreadcrumbProps) {
  return (
    <nav className="mb-8 text-sm text-gray-500" aria-label="Breadcrumb">
      <ol className="flex flex-wrap items-center gap-x-2">
        <li>
          <Link href="/" className="hover:text-accent transition-colors">
            Home
          </Link>
        </li>
        <li aria-hidden="true">/</li>
        <li>
          <Link
            href={`/${category}`}
            className="hover:text-accent transition-colors capitalize"
          >
            {category.replace(/-/g, ' ')}
          </Link>
        </li>
        <li aria-hidden="true">/</li>
        <li className="text-gray-300 line-clamp-1">{title}</li>
      </ol>
    </nav>
  );
}
