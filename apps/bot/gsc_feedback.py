"""
GSC Feedback Loop — Phase 4 implementation stub.

Full implementation: GitHub Actions weekly cron (Phase 4).
Setup docs: docs/SPEC-05-deployment.md §5.3

Manual domain verification:
  1. Add the site in Google Search Console.
  2. Choose DNS verification and add the TXT record at your DNS provider.
  3. Submit sitemap: https://{domain}/sitemap.xml
  4. Create a service account, download the JSON key, and set
     GSC_SERVICE_ACCOUNT_JSON in the runtime environment.
"""
