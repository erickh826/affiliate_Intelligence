export function getSiteName(): string {
  return process.env.NEXT_PUBLIC_SITE_NAME ?? 'Affiliate Intelligence';
}

export function getSiteUrl(): string {
  const configured = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  if (configured) {
    return configured.replace(/\/+$/, '');
  }

  const productionHost = process.env.VERCEL_PROJECT_PRODUCTION_URL?.trim();
  if (productionHost) {
    const host = productionHost.replace(/^https?:\/\//, '').replace(/\/+$/, '');
    return `https://${host}`;
  }

  return 'http://localhost:3000';
}

const GA_MEASUREMENT_ID = /^G-[A-Za-z0-9]+$/;

export function getGaMeasurementId(): string | null {
  const value = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID?.trim();
  if (!value || !GA_MEASUREMENT_ID.test(value)) {
    return null;
  }
  return value;
}
