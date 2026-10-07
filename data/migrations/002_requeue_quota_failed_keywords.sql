-- Requeue keywords the 2026-10-03 through 2026-10-07 cron runs marked failed.
-- Each run died in outline generation with OpenAI credit_balance_exhausted
-- and wrote no MDX. Rows that were already failed before those runs stay failed.
UPDATE keywords
SET status = 'pending'
WHERE status = 'failed'
  AND slug IN (
    'ai-art-generators-for-beginners',
    'best-ai-background-removers',
    'best-ai-meeting-assistants-2026',
    'best-ai-tools-for-content-marketing',
    'best-ai-tools-for-developers-2026',
    'best-ai-video-generators-2026',
    'best-text-to-video-ai-tools',
    'cursor-ai-review-2026',
    'dall-e-3-review-2026',
    'elevenlabs-review-2026',
    'github-copilot-review-2026',
    'github-copilot-vs-cursor',
    'grammarly-ai-review-2026',
    'how-to-remove-backgrounds-with-ai',
    'how-to-use-cursor-ai',
    'how-to-use-github-copilot',
    'how-to-use-notion-ai',
    'how-to-write-midjourney-prompts',
    'jasper-ai-review-2026',
    'jasper-ai-vs-chatgpt-for-writing',
    'midjourney-review-2026',
    'midjourney-vs-dall-e-3',
    'notion-ai-review-2026',
    'stable-diffusion-setup-guide',
    'stable-diffusion-vs-midjourney'
  );
