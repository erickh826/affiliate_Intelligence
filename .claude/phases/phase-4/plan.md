# Phase 4 Plan — Video Pipeline (SPEC-04)

**Status:** DRAFT
**Spec:** `docs/SPEC-04-video-pipeline.md`
**Timeline:** Week 12+ (after 100+ articles AND 1,000+ daily organic visitors)
**Depends on:** Phase 1 (published articles), Phase 2 (site + GSC data), Phase 3 (affiliate links)

---

## Objective

Build the AI video generation pipeline that converts high-traffic published articles into 60-second YouTube Shorts. Videos are embedded back into article pages to increase engagement and create an additional revenue surface.

---

## Trigger Conditions (MUST be met before starting)

- [ ] 100+ published articles on site
- [ ] 1,000+ daily organic visitors (verified via GA4)
- [ ] GSC feedback loop active (Phase 2 complete)
- [ ] At least 1 affiliate program approved (Phase 3 complete)

---

## Deliverables

| # | Deliverable | File/Dir | Acceptance Criteria |
|---|---|---|---|
| 1 | Article selector | `bot/video_selector.py` | SELECT by GSC impressions > 500/week + intent |
| 2 | Script extractor | `bot/video_script_extractor.py` | 60s HOOK→VALUE→PROOF→CTA script via LLM |
| 3 | Script template | `bot/video_script_template.txt` | Timing markers + structure per SPEC-04 §3 |
| 4 | Video generator (Creatomate) | `bot/video_generator.py` | Vertical .mp4, 1080×1920, <60s |
| 5 | YouTube publisher | `bot/youtube_publisher.py` | Data API v3 upload, metadata, tags |
| 6 | Cross-embed update | `bot/video_db_updater.py` | youtube_url + video_status in keywords.db |
| 7 | YouTubeEmbed component | `web/components/YouTubeEmbed.tsx` | Lazy iframe, responsive, 9:16 or 16:9 |
| 8 | Pipeline runner | `bot/main.py` (extend) | `--video` flag, batch video generation |
| 9 | Tests | `bot/tests/test_video*.py` | Mocked API calls, script validation |

---

## Task Breakdown

### T4.1 — Article selector
- `bot/video_selector.py`: SELECT from keywords.db WHERE status='published' AND gsc_impressions>500 AND intent IN ('comparison','tutorial') AND video_status='none'
- Priority: highest gsc_impressions first
- Batch: 3 videos/week cadence

### T4.2 — Script extractor
- `bot/video_script_extractor.py`: read MDX, extract title, tools, pricing
- LLM call (claude-3-5-haiku): generate 60-second script per SPEC-04 §3
- Script structure: HOOK (0-5s) → VALUE (5-25s) → PROOF (25-45s) → CTA (45-55s) → FOLLOW (55-60s)
- Output: `bot/video_scripts/{slug}.txt`
- Set video_status='scripted' in keywords.db

### T4.3 — Script template
- `bot/video_script_template.txt`: reusable template with timing markers
- Variable placeholders: `{tool_a}`, `{tool_b}`, `{price_a}`, `{price_b}`, `{cta_url}`

### T4.4 — Video generator (Creatomate start)
- `bot/video_generator.py`: Creatomate API with "AI Tool Comparison" template
- Input: script text + tool names + pricing data
- Output: .mp4 (1080×1920, vertical, <60s)
- Cost: ~$0.03-0.05 per render
- Fallback path: HeyGen API (talking head) when channel proves > $50/month

### T4.5 — YouTube publisher
- `bot/youtube_publisher.py`: YouTube Data API v3
- Upload: video file, title, description (with affiliate links), tags, thumbnail
- Metadata template per SPEC-04 §6.2
- Privacy: public, category_id=28 (Science & Technology)
- is_shorts: True (vertical 9:16, <60s)
- OAuth2: service account or refresh token flow

### T4.6 — Cross-embed update
- `bot/video_db_updater.py`: UPDATE keywords.db
- Set youtube_url = full YouTube URL
- Set video_status = 'published'
- SPEC-02 picks up on next Vercel build → embeds <YouTubeEmbed>

### T4.7 — YouTubeEmbed component (enhance existing)
- Already created in Phase 2 as stub
- Enhance: support 9:16 vertical (Shorts) + 16:9 landscape
- Lazy load iframe, placeholder thumbnail
- Caption: "Watch the quick comparison"

### T4.8 — Pipeline runner extension
- Extend `bot/main.py` with `--video` flag
- `python main.py --video --batch 3` → select → script → generate → upload → update DB
- `--dry-run`: generate scripts only, skip video generation and upload
- Structured JSON logging per video

### T4.9 — Tests
- `bot/tests/test_video_selector.py`: selection logic, GSC threshold
- `bot/tests/test_video_script_extractor.py`: mocked LLM, script structure validation
- `bot/tests/test_video_generator.py`: mocked Creatomate API
- `bot/tests/test_youtube_publisher.py`: mocked YouTube API

---

## Dependencies

| Dependency | Version | Purpose |
|---|---|---|
| google-api-python-client | >=2.0 | YouTube Data API v3 |
| google-auth | >=2.0 | OAuth2 for YouTube |
| httpx | >=0.27 | Creatomate / HeyGen HTTP calls |
| moviepy | >=1.0 | Video post-processing (if needed) |

---

## Environment Variables (New)

```env
CREATOMATE_API_KEY=
HEYGEN_API_KEY=
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
YOUTUBE_REFRESH_TOKEN=
```

---

## KPI Targets

| Metric | Target |
|---|---|
| Publishing cadence | 3 Shorts/week |
| Script-to-publish time | < 2 hours (automated) |
| Video length | 45–60 seconds |
| CTA click rate | > 3% of views |
| Session time increase | +30 seconds from embedded video |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Creatomate API quality low | Medium | Unusable videos | Switch to HeyGen (higher cost, better quality) |
| YouTube API quota exceeded | Low | Upload blocked | Request higher quota, batch uploads across days |
| YouTube copyright strike | Low | Channel suspended | Use original content only, no copyrighted music/images |
| Low video views | High | Minimal ROI | Only produce videos for articles with GSC position ≤ 30 |
| Affiliate links blocked in description | Medium | Lost commissions | Use landing page redirect instead of direct affiliate links |
