import Image from 'next/image';

interface ArticleMediaProps {
  image: string | null;
  sizes: string;
  className?: string;
}

export default function ArticleMedia({
  image,
  sizes,
  className = '',
}: ArticleMediaProps) {
  return (
    <div
      className={`relative overflow-hidden bg-[linear-gradient(135deg,#F6F7F9_0%,#E8EAED_100%)] ${className}`}
    >
      {image ? (
        <Image src={image} alt="" fill sizes={sizes} className="object-cover" />
      ) : (
        <div
          className="grid h-full w-full place-items-center text-[12px] font-semibold uppercase tracking-[0.04em] text-[#9ca3af]"
          aria-hidden="true"
        >
          No image
        </div>
      )}
    </div>
  );
}
