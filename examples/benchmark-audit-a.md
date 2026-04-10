# Deep Project Audit — Content Pipeline & Media Gallery

**Audit date:** 2026-04-10
**Methodology:** deep-project-audit v1.0.0 (6-phase structured audit)
**Auditor:** Claude Opus 4.6

> **Note:** This is an anonymized audit of a real project. Usernames,
> file paths, API keys, and personal identifiers have been replaced
> with generic placeholders.

---

## 4.1 What the Project Is

A personal content curation pipeline that takes a social media platform's
data export (saved posts/collections), downloads the actual media files
(videos, images), transcribes audio using Whisper, applies tag-based
categorization, and generates a static HTML gallery with filtering,
search, and video playback. Built in Python (~2,800 lines across 12
files), using JSONL manifests for inter-stage communication. Currently
processes ~4,500 saved items across 29 topic collections, with ~3,500
videos downloaded and ~2,600 transcribed.

---

## 4.2 What Works Well

**Pipeline architecture is genuinely good.** Five standalone stages
communicate through JSONL manifest files — each stage can be run
independently, stopped mid-run, and resumed without data loss. This is
the right pattern for a long-running media processing pipeline.

**Evidence:**
- `app/shared/manifest.py` implements atomic writes via temp-file +
  `os.replace()` — crash-safe by design
- Download stage saves progress every 5 items (line 324), so a crash
  loses at most 5 downloads, not the whole run
- Every stage has `--batch-size` or `--max` flags for incremental
  processing

**Folder naming convention is deterministic and sortable.**
`YYYY-MM-DD__type__author__platform_shortcode` gives natural sort order,
human-readable browsing, and zero naming collisions across 4,500+ items.

**Honest README.** Documents what works, what doesn't, known limitations,
cost estimates, and architecture decisions with rationale. Rare for a
personal project.

**Smart use of existing organization.** Instead of building AI-based
categorization, the pipeline uses the user's own saved collections as
the primary tag system. Sub-tags add granularity via keyword matching
only where configured. This avoids the "AI categorization is wrong 30%
of the time" problem entirely.

**Gallery is self-contained.** One HTML file + two JSON data files.
No build toolchain, no node_modules, no framework dependencies. Serves
with `python -m http.server`.

---

## 4.3 Critical Issues

**1. Transcription manifest not written incrementally.**
`transcribe_audio.py` processes an entire batch and writes the manifest
only at the end (line 409). A crash during the slowest pipeline stage
loses all progress from that session. The download stage already solves
this (writes every 5 items) — transcription doesn't.

**Impact:** On a 50-item batch at ~30s per transcription, a crash at
item 49 loses ~25 minutes of work.

**2. XSS surface in gallery template.** Media paths are injected into
HTML `src` and `poster` attributes without escaping. An `h()` HTML
escape helper exists in the template JavaScript but is not applied to
these attributes. A crafted filename containing `"onload="` could
execute arbitrary JavaScript.

**Risk:** Low for a locally-served personal tool, but blocks any future
sharing or hosting.

**3. Retry logic retries non-retryable errors.** `with_retry` in the
download stage retries on all exceptions, including 404 (post deleted)
and login-required errors. These will never succeed on retry, wasting
3x the time and rate-limit budget per permanently-failed item.

**Evidence:** `download_media.py` lines 105-130 — the `do_download`
function raises `PermissionError` and `FileNotFoundError` for
non-retryable cases, but `with_retry` catches all exceptions uniformly.

---

## 4.4 Architecture & Code Quality

**Structural analysis:**

| Aspect | Assessment |
|--------|-----------|
| Storage model | JSONL manifests — human-readable, crash-safe, zero dependencies. Trade-off: no querying capability, scales linearly with reads. |
| Sequential bottlenecks | Download and transcription are sequential per item. Download has rate-limiting (1.5s between items). Transcription is CPU/API-bound. |
| Schema consistency | Manifest schemas are implicit (no validation). Each stage assumes fields exist. A schema change in stage 1 silently breaks stage 4. |
| Single points of failure | Cookie file for authenticated downloads. If cookies expire, the entire download stage fails on login-required items. |
| Scalability | Current: 4,500 items. At 10x (45K items), manifest reads become slow (full-file scan each time). At 100x, the `os.walk()` in gallery build becomes the bottleneck. |

**Design pattern coherence:** Consistent across all stages — each is
a standalone script with argparse, manifest I/O, progress printing, and
a `main()` entry point. No drift between modules.

**MECE check:**
- **Overlap:** `tag_posts.py` and `build_gallery.py` both implement
  transcript-loading logic independently (DRY violation).
- **Gap:** No stage handles content metadata generation — there's a
  `content_meta.json` reader in `build_gallery.py` but no writer in
  the pipeline. Files like `generate_titles.py` and
  `generate_content_meta.py` exist in `scripts/` but aren't integrated
  into the main pipeline.
- **Gap:** No cleanup or archival stage. Deleted/expired content stays
  in the manifest and on disk forever.

**Code quality:**
- All files under 420 lines (largest: `transcribe_audio.py` at 420).
- Dead code: `retry_decorator` in `shared/retries.py` (lines 38-49) is
  never imported or used.
- Unused config: `max_items` in `settings.json` is never read.
- Unused dependency: `jinja2` in `pyproject.toml` is never imported.
- 0 empty files, 1 artifact file (`for` — empty, likely accidental).

**Test coverage:** None. No `tests/` directory, no test files, no
pytest configuration. `pyproject.toml` lists `pytest` as an optional
dev dependency but no tests exist.

---

## 4.5 Error Handling, Resilience & Failure Modes

**Crash scenarios:**
- **Download crash:** Recovers well — on-disk folder scan at startup
  detects already-downloaded items even if manifest is lost.
- **Transcription crash:** Loses entire batch (see Critical Issue #1).
- **Gallery build crash:** No data loss — gallery is regenerated from
  manifests. Worst case: stale `index.html`.
- **Parse crash:** No impact — parse is fast (<1s) and always runs from
  scratch.

**Timeout coverage:**
- `yt-dlp` subprocess: 120s timeout (line 111 of download_media.py)
- `ffmpeg` audio extraction: 120s timeout
- `ffprobe` duration check: 30s timeout
- `whisper` local: 600s timeout (10 min per video)
- No timeout on OpenAI API call — will hang if API is down

**Silent failures:**
- `json.JSONDecodeError` in manifest reads prints a warning but
  continues — a corrupted line is silently skipped.
- `build_gallery.py` silently skips posts where the content folder
  doesn't exist in the filesystem index. No error logged.

**Data integrity:**
- Manifest writes are atomic (temp + `os.replace()`). Good.
- No validation on manifest schema — a malformed record propagates
  silently through the pipeline.
- No orphan detection — deleted posts stay in manifests and on disk.

**Edge cases:**
- Non-English platform exports: Hard-coded `"Saved on"` key in
  `parse_export.py` line 82. Exports in other languages will silently
  produce 0 posts.
- Empty transcripts: Handled — writes empty `.txt` file and marks as
  `no_speech`.
- Carousel posts: `partial` status, not dropped. Correct behavior.

---

## 4.6 Performance & Bottleneck Analysis

**Timing (estimated from pipeline structure):**

| Stage | Duration | Bottleneck |
|-------|----------|-----------|
| Parse | <1s | N/A |
| Download (4,500 items) | ~2 hours | Rate limit (1.5s/item) + network |
| Transcribe (3,500 videos) | ~3-5 hours local / ~30 min cloud | CPU (local) or API cost (cloud) |
| Tag | <5s | Disk I/O for transcript reads |
| Gallery build | ~10s | `os.walk()` over 22K+ files |

**Parallelism:** Zero. All stages are sequential, single-threaded.
Downloads could parallelize (3-4 concurrent downloads with separate
rate-limiting). Transcription could parallelize across CPU cores (local)
or concurrent API calls (cloud).

**Resource waste:**
- Tag stage re-reads all transcript files from disk on every run, even
  if nothing changed. At 2,600 transcripts, this is ~2,600 file reads.
- Gallery build triple-indexes the filesystem (3 keys per directory in
  `scan_content_dirs`). Functional but wasteful.
- 423KB generated HTML file embeds all post data inline. At 10x scale,
  this becomes a 4MB HTML file.

**Cost analysis:**
- Local transcription: Free (CPU time only)
- Cloud transcription (OpenAI Whisper): ~$0.006/min * ~1,750 min = ~$10-20
- Storage: ~22K files, estimated 15-30 GB for video content
- No recurring costs — no hosted infrastructure

---

## Phase 5: Security, Readiness & Recommendations

### 5.1 Security & Data Exposure

**Secrets:**
- Cookie file (`config/cookies_*.txt`) is gitignored. Good.
- `OPENAI_API_KEY` is read from environment variable, never hardcoded.
  Good.
- No other secrets detected in source code.
- `.gitignore` excludes `work/`, `content/`, `exports/`, and cookies.
  Good coverage.

**Injection:**
- XSS in gallery template (see Critical Issue #2). Media paths injected
  without escaping.
- No SQL (no database). No command injection (subprocess calls use list
  arguments, not shell strings).
- No user-facing input beyond CLI arguments — low attack surface.

**PII:**
- Content folders contain social media usernames in folder names and
  filenames. This is inherent to the tool's function.
- No email addresses, phone numbers, or financial data in source code.
- Transcript files may contain spoken PII from video content — no
  sanitization or flagging.

**Supply chain:**
- `pyproject.toml` lists 3 dependencies: `yt-dlp`, `openai` (optional),
  `openai-whisper` (optional). All from PyPI, well-maintained.
- No lock file (`requirements.txt` or `poetry.lock`). Builds are not
  reproducible.
- No CI/CD pipeline — no workflow security concerns.

### 5.2 Logging & Observability

- **Logs:** `print()` statements to stdout. No structured logging.
- **Traceability:** Each manifest record has `post_id` and `updated_at`,
  enabling per-item tracking. But no request IDs or correlation across
  stages.
- **Log rotation:** N/A (stdout only).
- **Monitoring:** None. No alerting, no dashboard. Pipeline health is
  checked manually via `status.py`.

### 5.3 Documentation Quality

**Accuracy:** README accurately describes the current system. The
`CLAUDE.md` project instructions are current and match the codebase.

**Discrepancy found:** README line 149 says "See
`examples/sample-audit.md` for an anonymized example" — but the README
is for the gallery project, not the audit skill. No discrepancy.

**Actually:** `CODE_REVIEW.md` describes issues #1, #2, #3 as "Fixed"
but issues #4-#17 as "Open" — these 13 open issues from a prior code
review are not tracked anywhere actionable (no GitHub Issues, no TODO
file). Risk of these being forgotten.

**Completeness:** Good. README covers installation, usage, architecture,
design decisions, limitations, and cost estimates.

**Onboarding:** A new user could get the pipeline running in ~30 minutes
following the README. The main friction point is obtaining platform
cookies.

### 5.4 Goal Fulfillment

**Stated objective** (from CLAUDE.md): "Parse saved content from
[social media] into a searchable, browsable media gallery with tag
filtering and transcript search."

**Actual behavior:** The system does exactly this for one platform
(Instagram). Multi-platform support is mentioned in CLAUDE.md and
README but only Instagram parsing exists. The gallery data model
includes a platform field (`"p"`) and platform detection logic, but
no other parsers are implemented.

**Verdict:** Goal 90% fulfilled. Core promise delivered for the primary
platform. Multi-platform is architected but not implemented.

### 5.5 Blind Spots

| Blind Spot | Risk |
|-----------|------|
| No monitoring of cookie expiration | Downloads silently fail when cookies expire — user discovers this only after a failed batch |
| No content freshness tracking | Deleted/expired source posts stay in manifests forever |
| No transcript quality validation | Whisper output is saved as-is — no confidence scoring, no flagging of likely-bad transcripts |
| No storage growth monitoring | 22K+ files growing with each run, no cleanup/archival policy |
| No run-level logging | Individual item statuses tracked, but no "run X processed Y items in Z minutes" audit trail |
| 13 open code review findings | Tracked in `CODE_REVIEW.md` but not in an issue tracker — risk of being forgotten |

### 5.6 Objective Clarity Assessment

| Dimension | Rating (1-10) | Evidence |
|-----------|---------------|----------|
| Objective clarity | 9 | Clear, well-scoped goal stated in README and CLAUDE.md |
| Goal fulfillment | 7 | Core pipeline works well; multi-platform promised but not delivered |
| Delivery reliability | 7 | Pipeline is resumable and crash-safe (except transcription batch loss) |
| Output quality | 8 | Gallery is polished — themes, search, filtering, keyboard shortcuts |
| Automation maturity | 5 | Manual CLI runs only; no scheduling, no cron, no watched folders |
| Self-improvement | 3 | No feedback loop — doesn't track which transcripts are wrong or which tags are inaccurate |
| Operational visibility | 4 | `status.py` gives snapshot, but no history, no trends, no alerting |
| Resource efficiency | 6 | Sequential processing leaves performance on the table; storage grows unbounded |

### 5.7 Overall Rating

**6.5/10** — A well-built personal tool with clean architecture and
honest documentation. Delivers on its core promise (one-platform gallery
with search). Falls short on resilience (transcription batch loss),
automation (manual runs only), testing (zero tests), and the
multi-platform promise. The 13 unresolved code review findings and lack
of any test coverage prevent a higher score.

### 5.8 Production Readiness Assessment

| Gate | Status | Evidence |
|------|--------|----------|
| **Functionality** — does it do what it promises? | PARTIAL | Core pipeline works for one platform; multi-platform claimed but not implemented |
| **Reliability** — consistent without manual intervention? | PARTIAL | Resumable pipeline, atomic manifest writes. But transcription loses batch on crash, and requires manual CLI runs |
| **Error handling** — recovers gracefully? | PARTIAL | Download recovery is good; transcription recovery is not. Non-retryable errors waste retry budget |
| **Security** — no exposed secrets, injection, PII? | PARTIAL | Secrets handled correctly. XSS surface in gallery template. No PII in code, but transcripts may contain spoken PII |
| **Testing** — critical paths covered? | FAIL | Zero tests. No test directory, no test files, no CI |
| **Monitoring** — can you tell when something breaks? | FAIL | No alerting, no structured logging. `status.py` is manual-only |
| **Documentation** — can someone else operate this? | PASS | Excellent README, clear CLAUDE.md, architecture documented |
| **Scalability** — handles growth without redesign? | PARTIAL | Works at 4,500 items. At 45K, manifest reads and gallery HTML size become bottlenecks |
| **Data integrity** — consistent, backed up, recoverable? | PARTIAL | Atomic writes good. No backups, no cleanup, no orphan detection |
| **Dependency health** — maintained, pinned, vulnerability-free? | PARTIAL | Dependencies are maintained but not pinned. No lock file. Unused `jinja2` dependency |

**Verdict:** Needs 4 fixes before shipping — add incremental
transcription writes, add basic test coverage for critical paths,
fix XSS in gallery template, and add a dependency lock file.

### 5.9 Top 10 Ranked Recommendations

| # | Action | Impact | Effort | Who Implements |
|---|--------|--------|--------|----------------|
| 1 | Add incremental manifest writes to transcription stage | Critical — prevents losing hours of transcription work on crash | Low — copy the pattern from download stage (write every N items) | Agent or human |
| 2 | Add basic tests for manifest I/O, URL parsing, and tag matching | Critical — zero test coverage on a 2,800-line codebase | Medium — ~200 lines of pytest for the 3 shared modules + parse logic | Agent or human |
| 3 | Fix XSS in gallery template — escape media paths in src/poster attributes | High — blocks any future sharing or hosting | Low — apply existing `h()` helper to 2-3 attribute insertions | Agent |
| 4 | Make retry logic skip non-retryable errors (404, login-required) | High — saves 3x time and rate-limit budget per permanently-failed item | Low — add exception type check in `with_retry` | Agent |
| 5 | Add a lock file (`pip freeze > requirements.txt` or use `uv lock`) | Medium — enables reproducible builds | Low — one command | Human |
| 6 | Add scheduled/automated pipeline runs (cron or task scheduler) | Medium — currently requires manual CLI execution for each stage | Medium — write a wrapper script + schedule with OS scheduler | Human |
| 7 | Track open code review findings in GitHub Issues instead of CODE_REVIEW.md | Medium — 13 open findings at risk of being forgotten | Low — create 13 issues, link to CODE_REVIEW.md | Agent |
| 8 | Add cookie expiration detection — check cookie file age or test auth before batch | Medium — prevents silent batch failures when cookies expire | Low — stat the cookie file, warn if > 7 days old | Agent |
| 9 | Remove dead code: unused `retry_decorator`, unused `jinja2` dep, empty `for` file, unused `max_items` config | Low — hygiene, reduces confusion | Low — 4 deletions | Agent |
| 10 | Add transcript confidence scoring — flag transcripts below a word-count or duration threshold | Low — improves sub-tag accuracy over time | Medium — add a validation step after transcription | Agent |

### 5.10 The Uncomfortable Question

The tool is built for one person's workflow on one platform. The README
hints at multi-platform support (YouTube, LinkedIn, Substack), and the
data model is ready for it, but none of those parsers exist. If the
goal is a personal tool — it works. If the goal is to share it or grow
it — the missing tests, missing platforms, and 13 unresolved code review
findings say "side project that got 80% done." The question is: is this
a finished personal tool, or an unfinished sharable one? The answer
determines whether the next investment is polish (tests, automation,
cleanup) or features (more platforms, better UI).

---

## Phase 6: Resilience Testing

**Backups:** None exist. No backup mechanism, no export functionality,
no snapshot tooling. If the content directory is lost, all downloaded
media and transcripts must be re-downloaded and re-transcribed from
scratch. The manifests in `work/` are the only recovery mechanism —
they track what was processed but cannot restore the actual files.

**Recovery path:** Re-run the pipeline from stage 1. Parse is
idempotent. Download skips existing files. Transcription skips existing
`.txt` files. Full recovery is possible but time-expensive (~5-7 hours
for the current dataset).

**Operational resilience:** The project runs on a local machine with
cloud-synced storage. No migration documentation. No deployment
procedure (it's a local tool). Recovery time: hours, not minutes.

---

*Generated by [deep-project-audit](https://github.com/belousov-petr/deep-project-audit) v1.0.0*
