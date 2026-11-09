# Drive research packets

The daily bot reads verified research from a Google Drive folder, then writes the article with OpenAI and Anthropic, applies the affiliate disclosure, and commits as it does today. It does not call the Perplexity API when a packet matches the keyword.

`PERPLEXITY_API_KEY` is optional. If a selected keyword has no packet and Perplexity is unset or out of quota, that keyword stays `pending` and the cron does not turn red for that skip.

Branded cover and Open Graph images are not on `main`. They are in open pull request #16 (`cursor/article-covers-referrals-32d1`). This pipeline does not scrape article images. After that pull request merges, the site builds a cover from the article title and keyword.

## One-time Drive setup

1. In Google Cloud, create or choose a project and enable the **Google Drive API**.
2. Create a service account and download its JSON key. Do not commit the file.
3. Create a Drive folder for packets. Share the folder with the service account `client_email` as **Viewer**.
4. Copy the folder id from the URL: `https://drive.google.com/drive/folders/FOLDER_ID`.
5. Add GitHub Actions secrets (Settings → Secrets and variables → Actions). Cursor Runtime Secrets are not visible to `bot-cron.yml`.

| Secret | Value |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | The service-account JSON file contents, or base64 of that JSON. |
| `DRIVE_FOLDER_ID` | The folder id only. |
| `OPENAI_API_KEY` | Already required. |
| `ANTHROPIC_API_KEY` | Already required. |
| `FIRECRAWL_API_KEY` | Still required so the workflow can start. Firecrawl runs only if a keyword has no packet and Perplexity is used. |
| `PERPLEXITY_API_KEY` | Optional. Leave it unset to stop Perplexity calls. |

Packets must sit directly in that folder. Subfolders are ignored.

## Which slug to research

The bot still selects keywords with the usual category mix and priority. See the next batch without locking rows:

```bash
python apps/bot/main.py --preview 5
```

The first column is the slug. Name the Drive file with that slug.

## File names

Use one file per article:

- `{slug}.json`
- `{slug}.md`
- `{slug}.markdown`
- `{slug}.txt`
- a Google Doc titled `{slug}`

`{slug}` is the `keywords.db` slug. A file named from the keyword (`best ai writing tools` → `best-ai-writing-tools`) also matches. If both a `.json` and a `.md` exist, the JSON file is used. Leave older packets in the folder; only the selected slug is read.

## Markdown packet

```markdown
---
keyword: best ai writing tools
slug: best-ai-writing-tools
title: Best AI Writing Tools in 2026
affiliate_partner: jasper
cta: Compare Jasper plans
disclosure: This article contains affiliate links. We may earn a commission if you buy through them.
---

## Talking points

- Jasper Pro is $69 per month when billed monthly.
- Copy.ai has a free plan with a limited word allowance.

## Sources

- [Jasper pricing](https://www.jasper.ai/pricing)
- https://www.copy.ai/prices

## Tools

### Jasper
- Pricing: $69/month
- Pros: brand voice, templates
- Cons: costly for solo use

## FAQ

- How much does Jasper cost?
```

A line that is exactly `Talking points`, `Sources`, `Tools`, or `FAQ` also starts that section, which is what a Google Doc export usually produces.

The title is used as the H1 only when it contains the keyword and is at least 10 characters. Include at least one talking point and one `http` or `https` source. A matched file that fails those checks skips that keyword instead of calling Perplexity.

## JSON packet

```json
{
  "keyword": "best ai writing tools",
  "slug": "best-ai-writing-tools",
  "title": "Best AI Writing Tools in 2026",
  "talking_points": [
    "Jasper Pro is $69 per month when billed monthly."
  ],
  "sources": [
    {"title": "Jasper pricing", "url": "https://www.jasper.ai/pricing"}
  ],
  "tools_mentioned": [
    {
      "name": "Jasper",
      "pricing": "$69/month",
      "pros": ["brand voice"],
      "cons": ["costly for solo use"]
    }
  ],
  "faq_seeds": ["How much does Jasper cost?"],
  "affiliate": {
    "partner": "jasper",
    "cta": "Compare Jasper plans",
    "disclosure": "This article contains affiliate links. We may earn a commission if you buy through them."
  }
}
```

`facts` may be used instead of `talking_points`. Each fact is `{"claim": "...", "source": "https://..."}`.

## What the bot does with the packet

- Talking points and facts are the only claims passed to the writer.
- Source links are stored as the research sources. The bot does not scrape those pages for images.
- The disclosure sentence is written under the article H1. The site still shows its standard affiliate note when an enabled program renders a CTA.
- `cta` is saved as `cta_text` in `monetisation/affiliate_map/{slug}.json`. The button uses it when that program is `enabled` in `monetisation/affiliates.json`. The keyword row's `affiliate_partner` is kept when it is already set.
- OpenAI writes the outline and Anthropic writes the sections. The existing quality gate, MDX commit, and deploy hook are unchanged.
