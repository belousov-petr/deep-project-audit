# Baseline Review - Personal Media Content Pipeline

**Review date:** 2026-04-17
**Methodology:** bare "review this project" prompt - no skill methodology
**Reviewer:** Claude Opus 4.7

> **Note:** This is an anonymized baseline review - a bare "review this project" prompt with no skill methodology, used as a control to measure what the shakedown skill adds vs. unstructured Claude output. Platform names, collection names, and personal identifiers have been replaced with generic placeholders. The absence of structural sections (production readiness gates, value assessment, uncomfortable question, ranked recommendations table) is intentional - that's what the skill provides and this baseline deliberately lacks.

---

# Review - content-library (Saved-Posts Gallery)

**Scope:** Full project at `<workspace>/content-library/`
**What it is:** Personal pipeline that turns a social media platform's saved-posts data export into a searchable static HTML gallery (parse → yt-dlp download → whisper transcribe → tag → build gallery).

---

## The headline finding

**The gallery is showing you about 8% of what the pipeline actually downloaded.**

`work/manifests/download_manifest.jsonl` has 4,507 records, of which 4,043 are marked `downloaded` / `skipped` / `partial` - i.e. gallery-eligible. On disk, `content/<platform>/` has 4,513 post folders, totalling **32 GB**. But `work/reports/gallery/data/posts.json` contains only **366 items**, and they're almost all from one collection (346/366).

The cause is a path-format mismatch. There are two generations of download records in the same manifest:

| Prefix | Count | Notes |
|---|---|---|
| `content/<platform>/...` | 366 | Modern records. Gallery picks these up. |
| `Content\<Collection>\...` (backslashes, capital C) | 4,141 | Legacy records from before the project was restructured from an older name + `Content/` → current name + `content/<platform>/`. |

`app/build_gallery.py` computes `folder_rel = os.path.relpath(Path(folder_path), PROJECT_ROOT).replace("\\", "/")` and then looks it up in an `fs_index` built from walking `content/<platform>/`. Legacy records resolve to paths like `Content/<Collection>/2026-03-16__...` which don't exist, so `fs_entry` is `None` and the post is silently `continue`'d. No warning, no count. You get a working gallery, just with 92% of the media invisible.

This is the single most valuable fix on this project. Everything else is secondary.

**How to fix:** one-shot migration of `download_manifest.jsonl` that rewrites any `folder_path` starting with `Content\` or `Content/` to the new `content/<platform>/<collection>/<folder_name>` shape. The `folder_name` field on posts_manifest already has the correct `{collection}/{folder}` value, so you can re-derive the right path without re-downloading anything. After migrating, rerun `build_gallery.py` - you should jump from 366 to ~4,000 gallery items.

---

## Other things I'd fix soon

**1. Security: a live session cookie for the source platform sits in `config/cookies_<platform>.txt` on a cloud-synced path.** The file is gitignored (good) but it's still replicating across every device where the cloud sync client is installed. The `sessionid` value is a real cookie valid for about a year [REDACTED]. Any process or compromised device with that cloud sync mounted can hijack the session. At minimum: move cookies outside the synced folder, or mark the whole `config/` subtree as sync-excluded. Also consider rotating the session now, since the cookie has already been sitting on cloud sync for a while.

**2. `config/settings.json` has a dead `max_items` key.** The code never reads it. Either wire it up or remove it - right now it's a configuration lie.

**3. `work/` is a graveyard.** 30+ one-shot scripts (`process_batch03.py`, `gen_titles_batch02.py`, `fix_batch_exploring.json`, `failed_half_a.json`…) that were clearly copy-pasted variations of the same batch processor during an incremental titling run. They all hard-code an old absolute path under a previous project name that no longer exists. If you ever re-run one of them, it will fail in a confusing way. Move them to an `archive/` subfolder or delete - they're not part of the resumable pipeline. The same applies to `work/scripts/` which is a near-duplicate of `scripts/` with more old paths.

**4. Two parallel transcription implementations.** `app/transcribe_audio.py` (openai-whisper / OpenAI API via ffmpeg intermediate WAV) and `scripts/batch_transcribe.py` (faster-whisper, large-v3-turbo, int8, reads video directly). They use different manifest conventions - `transcribe_audio.py` writes `work/manifests/transcript_manifest.jsonl` (which **doesn't exist on disk**, meaning that script has likely never been run to completion on this data), whereas `batch_transcribe.py` updates `content_meta.json` in-place per folder. You have two truths for "is this post transcribed?" and downstream code (`tag_posts.py`, `build_gallery.py`) only looks at on-disk `.txt/.srt` files, silently agreeing with neither manifest. Pick one backend, delete the other, make the manifest authoritative.

**5. `scripts/batch_transcribe.py` points at `PROJECT_DIR / "Content"` (capital C).** On Windows this works on a case-insensitive filesystem, but any intentional relocation (Linux, Docker, a cloud runner) will silently find nothing. It should read `content/<platform>/<category>`.

**6. `download_failures.json` categorization is broken.** All 376 failures bucket as `other`. Looking at the actual error text, they're yt-dlp errors like `ERROR: [<platform>] <id>: There is no video in this post` - the string "not found" doesn't appear, so the heuristic in `write_failure_report` misses. Add a `"no video"` / `"no video formats"` pattern and promote those to a non-retryable `unsupported` category. These are structurally unrecoverable (image posts getting fetched as videos by a video downloader) and retrying them burns rate-limit budget on something that will never succeed.

**7. `content_meta.json` pipeline is only half-wired.** `work/content_meta_progress.json` shows 1,012 posts done out of 3,032 processable - meaning ~2,000 post folders have *no* content_meta.json, so `build_gallery.py` treats them as title-less. The title/summary generation logic lives in `scripts/generate_content_meta.py` and `scripts/gen_content_meta.py` (two versions - pick one). Neither is part of the documented pipeline in README.md or CLAUDE.md. That whole subsystem feels like it was bolted on during an ad-hoc LLM-subagent experiment and never integrated. The existing CODE_REVIEW.md also predates this addition.

**8. Empty / stub platform dirs.** Three additional platform subdirs under `content/` and `exports/` exist but are empty or have no parser. CLAUDE.md promises multi-platform support - the actual codebase is source-platform-only. Either add the parsers or remove the aspirational scaffolding so the folder layout reflects reality.

**9. A zero-byte file named `for` sits at the project root.** Almost certainly a shell typo (`python … for …` that truncated). Harmless but indicative - nobody is doing an `ls` hygiene check.

---

## Prior review vs. current state

There is a `CODE_REVIEW.md` from 2026-03-24 that lists 17 issues with 4 fixed at the time. Quick check on the "still-open" ones I can verify:

- **#4 (XSS via `src`/`poster` in HTML)** - The review assumed template-level string substitution. Reading `app/templates/gallery.html`, the posts are injected as a JSON blob and rendered with `createElement` + `textContent`. There is no `innerHTML` anywhere. The `h()` escape helper isn't needed because it's not doing string concat. Separately, `build_gallery.py` replaces `</` with `<\/` in the JSON blob it embeds, so the `</script>` breakout concern (#10) is actually addressed. These two are effectively closed; the review was written before the current rendering approach.
- **#16/#17 (`jinja2` / `openai` deps)** - `pyproject.toml` was cleaned up. `jinja2` is gone, `openai` is now an optional extra. Closed.
- **#12 (dead `retry_decorator`)** - Still present in `app/shared/retries.py`. Defined, never imported.
- **#14 (dead `max_items` config)** - Still present.
- **#7 (no incremental transcript manifest writes)** - Moot: the whole `transcribe_audio.py` path appears unused; transcripts are being written by `scripts/batch_transcribe.py` which updates per-folder `content_meta.json` instead of a manifest at all. The risk has moved rather than resolved.

So the prior review is partially stale, which is normal. The rotting pieces are the dead code and the "drift" issues that have emerged since (path mismatch, dead config key, stub platforms, two transcribers).

---

## What's genuinely good here

- The JSONL-manifest-per-stage architecture is the right call for a personal tool. Human-readable, crash-safe, easy to re-run one stage.
- `app/shared/manifest.py::write_manifest` does atomic writes via `.tmp` + `os.replace`. Good.
- `app/serve.py` is nicely done: Range-request support for video seeking, localhost-only bind, path-traversal guard, blocklist for cookies/.env/.git. This file would survive a review on its own merit.
- Naming scheme for post folders (`YYYY-MM-DD__type__author__<platform>_SHORTCODE`) is deterministic, sorts usefully, and embeds enough info to reconstruct metadata from the filename alone. Nice.
- Resume semantics (disk-scan fallback in `download_media.py` when the manifest is lost) is the kind of belt-and-suspenders touch that actually matters at 4,500 items.
- `scripts/batch_transcribe.py` detects audio-less videos via `av.open().streams.audio` *before* paying for transcription - that's a real cost/time saver.

---

## Maturity read

This is a working personal tool that's grown one feature at a time (basic pipeline → gallery → content_meta titles → tentative multi-platform) without a consolidation pass in between. The core pipeline (stages 1 - 4 + gallery) works. The bolt-ons (titles, multi-platform, second transcriber) are half-done, and the drift between them is what's causing the 92% invisibility of the gallery content.

I wouldn't call this production-ready, but it doesn't have to be - it's a local tool for one user. For that use case it's "a good weekend of cleanup away from being excellent": fix the path migration, retire the duplicate transcriber, clear out `work/`, and either finish or remove the multi-platform scaffolding.

Top three things to do, in order:
1. **Migrate the 4,141 legacy `folder_path` entries in `download_manifest.jsonl`.** This unlocks the rest of the gallery immediately.
2. **Move `config/cookies_<platform>.txt` off the cloud sync path** (or rotate + exclude `config/` from sync).
3. **Delete `work/*.py` one-shot scripts and `work/scripts/`**, pick one transcriber, delete the other. Consolidate before building anything new.
