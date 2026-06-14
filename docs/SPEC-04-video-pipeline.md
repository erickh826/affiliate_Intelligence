# SPEC-04 — Video Pipeline (Phase 4)

**Version:** 1.0 | **Updated:** 2026-05-12
**Related:** [README](../README.md) | [SPEC-01](./SPEC-01-content-bot.md) | [SPEC-02](./SPEC-02-web-system.md)

---

## 1. Purpose

SPEC-04 defines the AI video generation pipeline that converts published articles into short-form video content (YouTube Shorts / Reels). Videos are embedded back into article pages (via SPEC-02) to increase engagement and create an additional revenue surface.

> **Phase 4 trigger:** Activate when the site has 100+ published articles AND 1,000+ daily organic visitors.

---

## 2. Pipeline Overview

```
data/keywords.db (status=published, video_status=none)
         │
[1] Article Selector
    — gsc_impressions > 500/week
    — intent = "comparison" or "tutorial"
         │
[2] Script Extractor
    — Read apps/web/content/[category]/[slug].mdx
    — Extract: key facts, pricing, top 3 tools
    — LLM: generate 60-second HOOK→VALUE→PROOF→CTA script
         │
[3] AI Video Generator (choose one)
    — Option A: HeyGen API (talking head)
    — Option B: Creatomate (text overlay + B-roll)
    — Option C: ElevenLabs TTS + D-ID avatar
    — Output: .mp4 (1080×1920, vertical)
         │
[4] YouTube Publisher
    — YouTube Data API v3: upload
    — Set: title, description (with affiliate links), tags, thumbnail
         │
[5] Cross-embed + DB Update
    — Write youtube_url to keyword_database.csv
    — Set video_status = "published"
    — SPEC-02 picks up on next build → embeds video in article
```

---

## 3. Video Script Structure (60 seconds)

```
[0–5s]   HOOK
"Most people choosing [Tool A] over [Tool B] are wasting money. Here's why."

[5–25s]  KEY VALUE
"Tool A costs $X/month. Tool B costs $Y. For [use case], Tool B wins because..."

[25–45s] PROOF
Screen recording or text overlay: specific pricing comparison, API limits, etc.

[45–55s] CTA
"Link in description — try [Tool] free for 14 days."

[55–60s] FOLLOW
"Follow for weekly AI tool comparisons."
```

**Template file:** `apps/bot/video_script_template.txt`

---

## 4. Script Extractor

**File:** `apps/bot/video_script_extractor.py`

```python
messages = [
    {"role": "system", "content":
        "Write punchy 60-second YouTube Shorts scripts about AI tools. "
        "Lead with a contrarian hook. No filler. Specific pricing data required."
    },
    {"role": "user", "content":
        f"Article title: {title}\n"
        f"Tools compared: {tools_list}\n"
        f"Key pricing: {pricing_table}\n"
        f"Affiliate CTA URL: {cta_url}\n\n"
        "Write a 60s script: HOOK → VALUE → PROOF → CTA. "
        "Include 1 specific pricing comparison."
    }
]
# model: claude-3-5-haiku
```

Output saved to `apps/bot/video_scripts/[slug].txt`.

---

## 5. AI Video Generation Options

### Option A: HeyGen API (Recommended Phase 4+)

Best for: talking-head, high production value  
Cost: ~$0.10–$0.20 per minute

```python
payload = {
    "video_inputs": [{
        "character": {"type": "avatar", "avatar_id": "YOUR_AVATAR_ID"},
        "voice": {"type": "text", "input_text": script, "voice_id": "en-US-neural"},
        "background": {"type": "color", "value": "#111827"}
    }],
    "dimension": {"width": 1080, "height": 1920}
}
# POST https://api.heygen.com/v2/video/generate
```

### Option B: Creatomate API (Start Here)

Best for: text overlay + B-roll, lowest cost, fastest iteration  
Cost: ~$0.03–$0.05 per render  
Uses pre-built "AI Tool Comparison" template with text variable injection.

### Option C: ElevenLabs TTS + D-ID

Best for: custom voice, no avatar needed  
Cost: ~$0.05 per minute  
Pipeline: ElevenLabs audio → D-ID animates a photo avatar → merge to .mp4

**Recommendation:** Start with Option B. Move to Option A once YouTube channel proves > $50/month.

---

## 6. YouTube Configuration

### 6.1 Channel Setup

- Channel name: same as website brand
- Description: niche + affiliate disclosure
- Banner: branded, includes website URL

### 6.2 Video Metadata Template

```python
video_metadata = {
    "title": f"{keyword} — Quick Comparison 2026",
    "description": (
        f"{article_summary_2_sentences}\n\n"
        f"🔗 Full article: https://yourdomain.com/{category}/{slug}\n"
        f"💡 Try {tool_name} free: {affiliate_url}\n"
        f"(Affiliate link — we may earn a commission)\n\n"
        f"#AItools #{category.replace('-','')} #Shorts"
    ),
    "tags": keyword.split() + ["AI tools", "Shorts"],
    "category_id": "28",           # Science & Technology
    "privacy_status": "public",
    "is_shorts": True              # vertical 9:16, < 60s
}
```

### 6.3 YouTube Partner Program Threshold

- 1,000 subscribers + 10M Shorts views (for Shorts revenue share)
- Apply once threshold hit; Shorts feed revenue began 2023

---

## 7. Database Update

After successful publish:

```python
# Writes to data/keywords.db via SQLite
keyword_db.update(
    slug=slug,
    youtube_url=f"https://www.youtube.com/watch?v={video_id}",
    video_status="published"
)
# SPEC-02 auto-embeds on next Vercel deploy
```

---

## 8. KPIs

| Metric | Target |
|---|---|
| Publishing cadence | 3 Shorts/week |
| Script-to-publish time | < 2 hours (automated) |
| Video length | 45–60 seconds |
| CTA click rate | > 3% of views |
| Session time increase | +30 seconds from embedded video |

**Content rule:** Only produce videos for articles already on page 1–3 of Google (GSC position ≤ 30). These have proven demand.

---

## 9. Environment Variables

```env
HEYGEN_API_KEY=
CREATOMATE_API_KEY=
ELEVENLABS_API_KEY=
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
YOUTUBE_REFRESH_TOKEN=
```

---

*Related: [README.md](../README.md) | [SPEC-01](./SPEC-01-content-bot.md) | [SPEC-03](./SPEC-03-monetisation.md)*
