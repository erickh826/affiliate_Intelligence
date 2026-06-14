export function getSiteName(): string {
  return process.env.NEXT_PUBLIC_SITE_NAME ?? 'Affiliate Intelligence';
}
