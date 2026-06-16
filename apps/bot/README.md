# apps/bot

Python content pipeline (SPEC-01).

Use this directory for keyword selection, research, writing, QA, MDX generation, and feedback automation.

## Search Console setup

`gsc_feedback.py` is a Phase 4 stub. Before enabling the weekly feedback loop:

1. Add the production domain to Google Search Console.
2. Complete DNS TXT verification with your DNS provider.
3. Submit `https://{domain}/sitemap.xml`.
4. Create a service account, download the JSON key, and expose it as
   `GSC_SERVICE_ACCOUNT_JSON`.
