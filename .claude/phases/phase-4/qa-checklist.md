# Phase 4 — QA Checklist

**Phase:** 4 — Video Pipeline (SPEC-04)
**Status:** NOT STARTED

---

## Trigger Conditions

- [ ] 100+ published articles verified
- [ ] 1,000+ daily organic visitors verified (GA4)
- [ ] GSC feedback loop active
- [ ] At least 1 affiliate program approved

## Article Selection

- [ ] Only selects articles with gsc_impressions > 500/week
- [ ] Only selects intent in ('comparison', 'tutorial')
- [ ] Only selects video_status = 'none'
- [ ] Priority by highest gsc_impressions

## Script Generation

- [ ] Script follows HOOK→VALUE→PROOF→CTA→FOLLOW structure
- [ ] Script length targets 45–60 seconds when read aloud
- [ ] Script includes at least 1 specific pricing comparison
- [ ] Script includes affiliate CTA URL
- [ ] Scripts saved to `bot/video_scripts/{slug}.txt`
- [ ] video_status set to 'scripted' after script generation

## Video Generation

- [ ] Output is vertical .mp4 (1080×1920)
- [ ] Video duration < 60 seconds
- [ ] Creatomate API call succeeds (mocked in test)
- [ ] Cost within $0.03-0.05 per render estimate
- [ ] Fallback to HeyGen documented and testable

## YouTube Publishing

- [ ] YouTube Data API v3 upload succeeds (mocked in test)
- [ ] Title format: "{keyword} — Quick Comparison 2026"
- [ ] Description includes: article link + affiliate link + disclosure + hashtags
- [ ] Tags include keyword terms + "AI tools" + "Shorts"
- [ ] Category: 28 (Science & Technology)
- [ ] Privacy: public
- [ ] is_shorts: True (vertical, <60s)

## Cross-Embed

- [ ] keywords.db updated: youtube_url set
- [ ] keywords.db updated: video_status = 'published'
- [ ] YouTubeEmbed renders on article page after rebuild
- [ ] Embed supports 9:16 vertical (Shorts)
- [ ] Embed lazy loads (no performance impact)

## Pipeline Integration

- [ ] `--video` flag on main.py triggers video pipeline
- [ ] `--dry-run` generates scripts only
- [ ] Structured JSON logging per video
- [ ] Batch limit respected (3 videos/run)

## Code Quality

- [ ] `black` + `ruff` pass on all new Python files
- [ ] Type hints on all public functions
- [ ] No bare `except:` blocks
- [ ] Specific exception types caught
- [ ] No code comments

## Tests

- [ ] `test_video_selector.py`: selection logic, thresholds
- [ ] `test_video_script_extractor.py`: mocked LLM, structure validation
- [ ] `test_video_generator.py`: mocked Creatomate API
- [ ] `test_youtube_publisher.py`: mocked YouTube API
- [ ] Integration: dry-run video pipeline for 1 article
