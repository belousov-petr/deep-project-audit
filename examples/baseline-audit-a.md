# Project Audit -- Content Pipeline

A personal content curation pipeline that takes a social media platform's data export (saved posts/collections), downloads the actual media files (videos, images), transcribes audio using Whisper, applies tag-based categorization, and generates a static HTML gallery with filtering, search, and video playback. Built in Python (~2,800 lines across 12 files), using JSONL manifests for inter-stage communication. Currently processes ~4,500 saved items across 29 topic collections.

The pipeline design is sound. JSONL manifests for inter-stage communication, per-post folders, resumable stages, atomic manifest writes -- these are good choices for a personal tool of this scale. The code is readable and well-organized. But there are real problems, and some of them compound each other.

Here is what matters, in the order I would fix it.


## 1. Transcription stage loses work on crash

This is the single biggest operational risk. `transcribe_audio.py` processes an entire batch (up to 50 items by default), accumulating results in memory, and only writes the manifest once at the very end (line 409). If the process crashes, gets killed, or the machine reboots mid-batch, every transcription completed in that session is lost. Transcription is by far the slowest and most expensive stage -- each item involves ffmpeg audio extraction plus Whisper inference. Losing a batch of 50 means losing 30-60 minutes of compute (local) or several dollars (OpenAI API).

Compare this to `download_media.py`, which already writes the manifest every 5 items (line 324-325). The transcription stage should do the same thing. Even better, it should write after every single item, since each item takes 30-60 seconds individually and the write itself is trivial (atomic write via temp + os.replace is already implemented in the shared manifest module).

The fix is straightforward: move the `write_manifest()` call inside the processing loop, after each successful transcription. The `append_manifest()` function already exists in `shared/manifest.py` but is not used here. Alternatively, just call `write_manifest(TRANSCRIPT_MANIFEST, all_records)` after each item, same pattern as the download stage.


## 2. Retry logic retries non-retryable errors

In `download_media.py`, the `do_download()` function (lines 105-119) correctly detects 404s and login-required errors by raising `FileNotFoundError` and `PermissionError`. But these exceptions are then caught by `with_retry()` (in `shared/retries.py`), which retries on *all* exceptions indiscriminately. So a deleted post (404) gets retried 3 times with exponential backoff (5s, 10s, 20s) before finally failing. Multiply that by hundreds of failed items and you are wasting significant time plus burning through the platform's rate-limit budget on requests that will never succeed.

The fix: add an exception filter to `with_retry()`. Something like a `no_retry_on` parameter that accepts a tuple of exception types to immediately re-raise. Then pass `no_retry_on=(FileNotFoundError, PermissionError)` from the download stage. The detection logic already exists -- it just needs to stop the retry loop instead of continuing it.


## 3. XSS surface in gallery template

The gallery HTML template injects media paths directly into DOM element properties without sanitization:

```javascript
img.src = p.th;        // line 1411
vid.poster = p.th;     // line 1500
vid.src = p.v;         // line 1502
```

These values come from the JSONL manifests, which are populated from the platform export data and folder paths. In the current use case (personal tool, local data), exploitation requires an attacker to modify the manifest files or the the platform export. The risk is low but the fix is cheap: validate that paths start with expected prefixes (`content/instagram/`) and contain no protocol schemes (`javascript:`, `data:`, etc.) before assigning to `.src`.

The `_safe_json()` function in `build_gallery.py` already handles the `</script>` injection vector for the embedded JSON data. This is the remaining gap.


## 4. Tag stage re-reads all transcripts every run

`tag_posts.py` iterates over every post in the manifest and calls `load_transcript_text()` for each one, which does a `folder.glob("*.txt")` and reads the file content. With 4,500+ posts, that is 4,500 filesystem glob operations plus file reads on every run. The stage has no concept of "already tagged" -- it rebuilds the entire tags manifest from scratch each time.

This is documented as intentional ("fast"), and for the current dataset size it probably completes in a few seconds. But it scales O(n) in both filesystem ops and memory, and as the dataset grows (especially with YouTube/LinkedIn/Substack content planned), this will become the kind of thing that makes you avoid running the pipeline.

A pragmatic fix: only re-tag posts that have been transcribed since the last tag run, by comparing timestamps between the transcript manifest and the tags manifest. Or just accept the current behavior and revisit when it actually becomes slow.


## 5. No tests

Zero test files exist. For a personal tool this is not unusual, but for a pipeline processing ~4,500 items with multiple external dependencies (yt-dlp, ffmpeg, Whisper), having no tests means every change is verified manually by running the full pipeline. The most valuable tests would be:

- **Manifest round-trip**: write records, read them back, verify integrity. This protects the pipeline's backbone.
- **SRT parsing**: `parse_srt()` in `build_gallery.py` handles real-world subtitle files with various edge cases. A few test cases here would catch regressions.
- **URL normalization and shortcode extraction**: `normalize_url()` and `extract_shortcode()` are pure functions that determine post identity. If they break, deduplication breaks.
- **Sub-tag matching**: `match_sub_tags()` has boundary-matching logic for short keywords. A test would document the expected behavior.

I would not aim for full coverage. Just the pure functions that determine correctness of the pipeline's data flow.


## 6. README and project identity are out of date

The README title and description still focus exclusively on a single platform. But the project was restructured for multi-platform support. The `pyproject.toml` metadata has not been updated to reflect this. Someone reading just the README or pyproject would not know the project supports multiple platforms.

Similarly, the README says "Python 3.10+" as a requirement, but the actual environment uses Python 3.14 and the code uses `float | None` union syntax, which requires 3.10+. This happens to be consistent but was likely not deliberately tested against 3.10.


## 7. Only one platform parser exists

The project structure has directories for multiple platforms, and the gallery template detects platform from source URLs and shows platform-specific icons. But only one parser exists. Export data for a second platform was placed in the exports directory but no parser was built.

This is not a bug -- it is planned future work. But it is worth noting because the gallery's platform detection logic is already implemented and tested only against data from the first platform. When data from other platforms arrives, the entire downstream pipeline (download, transcribe, tag, build) needs to handle different post ID formats, folder structures, and media formats.


## 8. Dead code and unused dependencies

- `retry_decorator` in `shared/retries.py` (lines 38-49) is never imported or used anywhere. `with_retry` is the function actually used.
- `config/settings.json` has a `max_items` key that no code reads. It looks like it was intended for the download stage but the CLI `--max` flag serves that purpose.
- `jinja2` was listed as a dependency in the prior code review but has since been removed from `pyproject.toml`. This appears to have been fixed.

These are trivial to clean up. Remove `retry_decorator`, remove the `max_items` config key.


## 9. Duplicate transcript-loading logic

Both `tag_posts.py` (line 40-49, `load_transcript_text()`) and `build_gallery.py` (lines 133-141, inline in `build_post_data()`) independently implement "find .txt files in a folder, read the first non-empty one." If the logic for finding transcripts changes (e.g., to prefer `.vtt` over `.txt`, or to handle multi-video posts differently), it needs to change in two places. This should be a shared utility in `shared/manifest.py` or a new `shared/transcript.py`.


## 10. Minor issues

- **`parse_export.py` line 82**: The key `"Saved on"` is hard-coded in English. If someone downloads their the platform data in another language, this silently produces zero posts. No error, no warning.
- **`transcribe_audio.py` line 237**: The temp file is created *before* the `try` block. If `extract_audio()` raises before the `finally` block, the temp file leaks. In practice, the `finally` block with `unlink(missing_ok=True)` covers this, but the tempfile creation should be inside the try block.
- **`download_images_apify.py`**: Uses bare `urllib.request` without retry logic, while `download_media.py` uses `with_retry`. Inconsistent resilience between the two download paths.


## Summary of priorities

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| 1 | Incremental manifest writes in transcription | 15 min | Prevents losing hours of work |
| 2 | Skip retry on non-retryable errors | 30 min | Saves time + rate-limit budget |
| 3 | XSS path sanitization | 20 min | Closes security surface |
| 4 | Add tests for pure functions | 2 hours | Enables safe refactoring |
| 5 | Extract shared transcript loader | 15 min | DRY, prevents divergence |
| 6 | Update README + pyproject identity | 15 min | Accuracy |

The first three are the only ones that affect correctness or operational reliability. The rest are hygiene and future-proofing. The project works well for its purpose -- these are improvements, not emergencies.
