interface YouTubeEmbedProps {
  url?: string;
}

export default function YouTubeEmbed({ url }: YouTubeEmbedProps) {
  if (!url) return null;

  const videoId = url.match(/(?:v=|youtu\.be\/)([^&\s]+)/)?.[1];
  if (!videoId) return null;

  return (
    <div className="my-8 aspect-video w-full rounded-lg overflow-hidden">
      <iframe
        src={`https://www.youtube.com/embed/${videoId}`}
        title="YouTube video"
        loading="lazy"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
        className="w-full h-full"
      />
    </div>
  );
}
