# Deep Project Audit — Job Listing Scraper Pipeline

**Audit date:** 2026-04-17
**Methodology:** deep-project-audit v1.0.0 (6-phase structured audit)
**Auditor:** Claude Opus 4.7

> **Note:** This is an anonymized audit of a real project. Usernames,
> company names, and other identifiers have been replaced with generic
> placeholders.

---

## 4.1 What the Project Is

A daily Python scraper pipeline that pulls job listings from 14 enterprise
employer career sites (banks, tech firms, telecoms, and consumer-brand
companies in one European country), deduplicates by SHA256 hash, filters
through two YAML-driven role taxonomies (a governance profile with 93
keywords and an engineering profile with 33 keywords), uses a single
hosted-LLM call per vacancy to score relevance across both roles
simultaneously, and sends a formatted digest via two independent channels
(a messaging app + email). Runs on a CI platform via manual workflow
dispatch triggered externally by a cron service at 05:00 UTC. Single-
maintainer personal tool, ~2,580 lines of source across 32 Python files,
106 passing tests. Commit history shows active development for ~3-4
weeks with a recent multi-role refactor.

---

## 4.2 What Works Well

**Notification integrity contract.** The pipeline only marks vacancies as
"seen" AFTER confirming at least one notification channel succeeded. If
both notification channels fail simultaneously, the dedup save is skipped
and the matches retry next run. This is the right pattern for a daily
fire-and-forget pipeline where missing a match is worse than duplicating
one.

**Secrets hygiene is defense-in-depth, not lip service.** Four separate
sanitization helpers redact known secret values from crash messages
before they reach the external notification channel, from scraper error
strings, from HTTP error messages in the messaging-app client, and from
SMTP error messages. Plus the bot token is never logged — only the
sanitized error is.

**Multi-role scoring done right.** A single LLM call scores all roles in
one JSON object, cutting API cost ~50% vs. per-role calls. Crucially,
the scorer filters to only roles that passed keyword filtering — no
"phantom entries" where a vacancy passes for role A and accidentally
gets scored for role B.

**LLM score semantics are defensive.** `llm_score: None` means "never
scored" (keep with keyword score); `0.0` means "LLM explicitly called it
irrelevant" (exclude). This prevents a failed API call from silently
suppressing matches.

**Scraper inheritance is genuinely DRY.** A shared base class (86 LOC)
backs three scrapers for sites on the same applicant-tracking platform
(each concrete scraper is ~10 LOC). A second shared base (129 LOC)
backs two scrapers for a different ATS. Adding a new customer of a
known ATS is ~10 minutes.

**Fault isolation is real, not theoretical.** Each scraper runs in its
own `ThreadPoolExecutor`; per-scraper exceptions are caught and logged
without aborting the run. Each scraper call is wrapped in a
per-attempt timeout with retry. Timeout-after-hang is cleaned up via
an orphan-process killer on both Windows and Linux.

**Prompt injection awareness.** User content is wrapped in XML
delimiters and the system prompt explicitly instructs the model to
ignore embedded instructions. Description truncated to 3,000 chars
before send. Not airtight against sophisticated injection but a
deliberate control.

**Test discipline.** 106 tests across 11 files, covering dedup (empty /
corrupt / invalid-date files), keyword filter (empty, 100K-char
description, emoji, duplicates, special chars), LLM scorer (markdown
fences, clamping, missing keys, API error, empty response), formatter
(XSS, zero-match, dual-role), runner (parallel vs sequential batching,
mixed unknown names), and parsing tests for 9 of 14 scrapers. Suite
runs in ~5s.

**Honest documentation.** README accurately lists the 14 target sites,
the ATS platform for each, and the scraping method. "Key Design
Decisions" section explains 13 real trade-offs. This is rarer than it
should be.

---

## 4.3 Critical Issues

**1. `.gitignore` excludes directories that are committed to the repo.**
Four directories (`docs/`, `goals/`, `tools/`, `memory/`) are listed in
`.gitignore` yet each contains tracked files. Either a future `git add`
will silently fail to include new files in these directories, or the
`.gitignore` entries are aspirational and should have been `git rm
--cached` first. Net effect: maintainer has no idea whether future
changes in these folders are being tracked.

**2. No HTTP retry/backoff for scraper API calls — single failure kills
the scraper run for the day.** Every API scraper calls
`httpx.get(...).raise_for_status()` with no retry, no `Retry-After`
handling, no exponential backoff. The base class retries the whole
scrape once, but if a scraper returns a 503 during page 3 of 18, the
entire scrape restarts from page 1 — wasting the first 2 pages of
bandwidth and hitting the same 503. For transient network blips, a
single 500-level response loses the day's data for that company.

**3. `get_scrapers(scraper_names=[])` returns empty list instead of all
scrapers.** Passing `--scrapers ""` on the CLI produces `[""]`, which
matches no scraper and the pipeline runs zero scrapers but still sends
a "0/0 succeeded" notification. The edge-case test explicitly names
this as a known bug but it is unfixed.

**4. Registry's "highest-priority scraper first" ordering has no effect.**
The registry attempts to place one browser scraper at the top of the
list, but the runner separates scrapers by `requires_browser` anyway,
so the intended ordering is irrelevant downstream. The intent is
implemented in a place that can't produce the effect.

**5. One scraper is effectively dead code in CI.** The scraper reads a
cache file that is gitignored and never written during CI. In CI runs
it will always log "No cache file found" and return zero. The code
relies on interactive sessions to populate the cache via a different
pathway, but there's no scheduled mechanism to do so. In practice this
source is disabled but still occupies a slot in the registry and
produces a permanent "0 vacancies" log line every run.

**6. Dedup data store committed to git with auto-commit from CI.** The
workflow auto-commits the dedup state file every run. After 22 days
the file is 619 KB with 6,282 entries. Git history now contains every
daily snapshot of the file — each commit adds ~25-50 KB of diff. In
6 months the pack-file bloat will be a gigabyte-class git repo for a
3,000-line codebase. This data belongs in a blob store or the CI
platform's cache, not git.

---

## 4.4 Architecture & Code Quality

**Structural analysis:**

| Aspect | Assessment |
|--------|-----------|
| Largest file | Orchestrator (278 LOC). Well under a 500-line limit. |
| File-size distribution | Median ~70 LOC, 95th percentile ~160 LOC. Tight. |
| Abstraction layers | 3: Scraper (data collection) → Matcher (keyword + LLM) → Notifier (format + send). Each layer has a clean input/output contract. |
| Coupling | Notifier and Matcher depend only on dataclass models. Scrapers don't know about roles, keywords, or LLMs. Good separation. |
| Orchestrator responsibility | Only one file knows about every layer. Pattern is fine. |
| Dead code | One scraper file (see Critical Issue 5). No other obvious dead code. |
| Circular imports | None. |

**Design pattern coherence (MECE check):**

- **Overlap:** Three separate sanitization helpers do nearly the same
  substring-replace job. Could be one helper in a shared module.
- **Overlap:** Country filtering logic appears in three places:
  hardcoded list of 25 city names in one scraper; substring match
  `("city", "country", "cc")` in another; and URL/API params in two
  more. The substring match version false-positives on any location
  whose name contains the 2-letter country code as a substring (e.g.
  the code "nl" appears inside "Finland"). Confirmed bug.
- **Gap:** No health/status command. You learn about failures from the
  daily digest or a failed CI run.
- **Gap:** No per-scraper rate limiter. Courtesy limits are whatever
  the underlying server enforces.
- **Gap:** No structured output logging. A log aggregator would have
  to regex-parse strings to extract facts.

**Code quality:**
- All files under 280 LOC. No complexity hotspots.
- No empty Python files except expected `__init__.py` placeholders.
- Phenom-like and GetNoticed-like base classes prove refactoring
  happened (not copy-paste).
- Type hints used inconsistently but present on most function
  signatures.
- No `assert` in production code paths.
- No TODO / FIXME / XXX comments (clean).

**Test coverage assessment:** 106 tests covering dedup, keyword filter,
LLM scorer, formatter, role loader, orchestrator, and parsing logic for
9 of 14 scrapers. No parsing tests for the 4 browser-based scrapers or
the newest API scraper. Zero integration tests hitting live sites. Zero
tests for the crash-sanitization module. Coverage estimate: ~70-75% by
line count, concentrated on pure-Python logic. Browser scrapers are
structurally untested.

---

## 4.5 Error Handling, Resilience & Failure Modes

**Crash scenarios traced:**

| Failure | Current behavior | Assessment |
|---------|------------------|------------|
| Single scraper raises exception | Caught in orchestrator, logged, `success=False` returned, pipeline continues. | Correct. |
| Single scraper hangs | Base class times out via executor; orphan browser processes killed on Windows/Linux. | Correct — cleanup is thoughtful. |
| LLM API is down | Vacancy keeps `llm_score=None` and is kept with keyword score. | Correct. |
| All LLM calls fail | Orchestrator logs and returns vacancies with keyword scores only. Pipeline still notifies. | Correct. |
| One notification channel down | `notification_ok = channel_a_ok or channel_b_ok` → pipeline continues and marks seen. | Correct. |
| Both notification channels down | Dedup save skipped → retries next run. | **Best-in-class.** |
| Process killed mid-run | Dedup file state is whatever was last saved. Atomic temp-file + rename. Nothing corrupted. | Correct. |
| Dedup file corrupt | Caught; starts fresh. First next-run sees all live vacancies as "new" → notification flood. | **Silent failure mode.** No upper cap on matches per message. |
| Role config malformed | Per-file errors caught; other roles continue. If ALL roles fail, pipeline returns with `error` field but does not alert. | Partial — pipeline aborts silently. |
| WAF-protected site changes detection rules | Scraper times out → `success=False` → included in daily "WARNING: 1/13 scrapers failed" section. | Correct (observable). |
| Framer-hosted search-index hash changes | Hardcoded URL with embedded content hash returns 404 → scraper fails. Comment explicitly calls this out but recovery is manual. | Explicit but fragile. |
| LLM API key rotated incorrectly | Empty-string key short-circuits LLM stage → keyword-only matches delivered. | Correct. |
| Browser driver not installed | Registry catches ImportError, logs warning, skips browser scrapers. API scrapers continue. | Correct — graceful degradation. |

**Timeouts inventory:**
- Scraper per-call: 60s
- LLM per-call: 30s
- LLM total batch: 300s
- Description fetch total: 120s
- HTTP per-request: 30s
- SMTP: 30s
- Browser page-load: 60s
- Browser selector-wait: 15s
- CI job: 10 min

All layers timeout-covered. No obvious hang surface.

**Silent failures:**
- Corrupted dedup file → all vacancies look new → notification flood
  (no upper cap).
- All role configs fail to parse → pipeline returns silently; no alert.
- DOM-scraping layout change → scraper silently succeeds with 0
  vacancies; no zero-result alarm.
- Country substring-match false-positives (see 4.4).

**Data integrity:**
- Dedup save uses `tempfile.mkstemp` + `os.replace` — POSIX-atomic
  (CI runs on Linux, so atomic in practice).
- SHA256 of `company|url` is deterministic and collision-resistant. No
  URL normalization though, so two scrapers that inconsistently append
  trailing slashes would produce duplicate entries. Per-scraper
  consistency is fine; cross-scraper consistency is not enforced.

---

## 4.6 Performance & Bottleneck Analysis

**Timing (structural estimate):**

| Stage | Duration | Bottleneck |
|-------|----------|-----------|
| Scrape (10 API, parallel) | ~7s | Slowest API call |
| Scrape (4 browser, sequential) | ~70s | Driver launch × 4 + WAF-bypass scraper |
| Dedup load/filter | <0.1s | In-memory |
| Keyword filter | <1s for 1K vacancies | Python string ops over ~130 terms × N |
| Description fetch | ≤120s cap | Per-vacancy HTTP round-trip |
| LLM scoring | ≤300s cap | Network + model latency |
| Format + send | <5s | Messaging API, SMTP |
| **Total per run** | **~3-6 minutes** (CI cap 10 min) | Browser scrapers + LLM calls |

**Parallelism:** API scrapers use one thread per scraper (no cap).
Browser scrapers are explicit sequential (tested and reverted after a
parallel attempt caused resource thrash). LLM: `min(4, len)` workers for
batches ≤30, sequential with 0.8s delay above that.

**Resource waste:**
- `max_workers=len(api_scrapers)` has no upper bound — adding 20 more
  scrapers would spike to 30+ concurrent threads.
- Every scraper recreates its HTTP client per call; no connection
  pooling across pages. On the 10-page paginated scraper this is ~10
  extra TLS handshakes (~2s).
- `hash_key` is a `@property` (not `@cached_property`); recomputed on
  every access in the dedup loop.

**Cost analysis:**

Per vacancy needing LLM scoring: ~1,250 input + 300 output tokens = ~$0.0022.

Daily needs_llm volume: keyword_passed is ~5-15% of ~1,200 daily
vacancies = 60-180 vacancies/day; direct-match short-circuits ~30% of
those. Rough daily LLM cost: **$0.10-0.30/day = ~$3-9/month**.

Other infra: CI minutes (well under free tier), SMTP free, messaging
free, cron service free.

**Total estimated monthly cost: ~$3-10.** Lean.

**Top 3 optimization opportunities:**
1. Add per-scraper HTTP retry with exponential backoff (e.g.
   `HTTPTransport(retries=3)`) — eliminates the "one 503 kills the
   day" failure mode at zero cost.
2. Cache `hash_key` with `@cached_property` — trivial micro-win.
3. Move the dedup state to the CI platform's cache instead of
   committing it — reduces repo growth from ~1 MB/month to 0.

---

## 4.7 Storage Efficiency

- **Empty files:** 4, all expected `__init__.py` placeholders.
- **Duplicate code:** 3 secret-sanitization helpers, ~30 duplicate LOC.
- **Build artifacts committed:** None. `__pycache__/` gitignored.
- **Binary assets:** None in repo.
- **Large files:** Dedup state at 619 KB is the largest single file.
- **Dead dependencies:** All 5 production deps are in active use.
- **Undeclared dependencies:** None.
- **Storage bloat:** Git packfile will grow unboundedly from daily
  commits of the dedup state (see Critical Issue 6).

Total waste: ~30 duplicate LOC, zero wasted bytes in repo at present,
but an exponential git-repo-growth curve if nothing changes.

---

## Phase 5: Security, Readiness & Recommendations

### 5.1 Security & Data Exposure

**Traditional security:**
- **Secrets in code:** None. All read from env vars. `.env` is
  gitignored, `.env.example` committed.
- **Secrets in git history:** Clean on spot-check of the config module.
- **Secrets in logs:** Four sanitization helpers redact known secret
  env-var values from error strings before logging.
- **Injection:** No SQL, no shell strings, no user input beyond CLI
  args. Subprocess calls use list args — safe.
- **SSRF:** `fetch_description(url)` accepts URLs from scraper output,
  but the URLs originate from trusted API responses, not user input.
  Low risk.
- **Supply chain:** Deps pinned with compatible-release operator, not a
  lock file. 5 production deps, all major/maintained. **Non-reproducible
  builds.**
- **CI workflow:** Pinned action versions, permissions minimized to
  `contents: write`, concurrency group prevents overlapping runs,
  `if: failure()` alert step. Good hygiene.
- **License:** MIT. No dep conflicts.

**OWASP LLM-related controls (2025 list):**
- **Prompt injection:** Defense in depth — XML-tag delimiters, system-
  prompt instruction, 3K-char truncation. Remaining risk: crafted
  description could exfiltrate via the reasoning JSON field, which goes
  only to the escaped messaging / email output. Low severity.
- **Sensitive info disclosure:** System prompt contains only public
  role profiles; no user PII or secrets passed to the LLM.
- **Supply chain:** Official SDK, pinned minor.
- **Data & model poisoning:** N/A (no fine-tuning, no RAG, no vector
  store).
- **Improper output handling:** Output is JSON-parsed with explicit
  schema; score is float-clamped to [0, 100]; reasoning is HTML/
  Markdown-escaped in formatters. Solid.
- **Excessive agency:** N/A — the LLM is a classifier with no tools.
- **System prompt leakage:** Prompt is public code — non-issue.
- **Unbounded consumption:** Global batch timeout cap, per-call max-
  tokens cap. But **no daily spend cap** — if dedup is corrupted and
  8K vacancies all keyword-pass, LLM cost spikes ~50× in one
  recovery run (~$15 incident).

**Agentic / MCP security:** N/A — not an agent system, not an MCP
server; only consumes one external scraping platform's API via a
token.

**Scraper ethics (regional context):**
- **robots.txt:** Not checked by any scraper. For public career pages
  this is grey area — the sites are meant to be indexed by job
  aggregators, and 10 of 14 scrapers hit official JSON APIs. For the
  4 HTML/DOM-scraping cases, `robots.txt` compliance is undocumented.
- **Terms of service:** No ToS review in the repo. One scraper uses a
  headed browser with a virtual display to bypass a WAF specifically
  designed to block automated access. Not illegal, but a real concern
  if the operator is applying for a role at that same employer.
- **Rate limiting:** Only a 0.8s sleep in the sequential LLM path.
  Scrapers hit API endpoints as fast as pagination allows. For small
  daily runs this is invisible but would be noticeable at hourly
  frequency.
- **Identification:** User-Agent is a standard desktop-Chrome string
  — deliberately non-identifying. Standard scraping practice but
  arguably should identify as a research bot.

**Data-protection concerns:**
- Scraped content is **public job postings** — no personal data
  collected.
- `.gitignore` explicitly excludes raw profile-harvesting outputs
  (names, emails). Good discipline.
- **BUT** a committed summary file contains 19 named individuals
  (first + last name) linked to their employers and role titles. In
  the applicable regulatory framework, this is personal data about
  identified natural persons. The `.gitignore` covers the raw file
  but not the summary — inconsistent.
- Recipient email is only the maintainer's own address; no third-
  party recipients.

**Red teaming:** No adversarial testing on LLM injection, no fuzz
tests on the YAML config loader, no test for malicious scraped
content.

**Key security findings summary:**
1. **Committed summary file contains 19 named individuals + employers**
   — personal-data exposure risk if the repo goes public.
2. **No lock file** → non-reproducible builds; any dep with a
   compatible version bump could introduce a vulnerability on next
   CI run with no code change.
3. **No daily LLM spend cap** — dedup corruption can cause a ~50×
   cost spike in one recovery run.
4. **Deliberate WAF bypass** on one target site is a ToS grey-area
   action.
5. **No robots.txt check.** Polite to add, trivial to implement.
6. **No bot-identifying User-Agent.**

---

### 5.2 Logging & Observability

- **Log format:** stdlib logging, `%(asctime)s | %(name)s | %(levelname)s
  | %(message)s` → stdout only.
- **Structured logs:** None. Grep-friendly, not machine-parseable.
- **Per-run audit trail:** Only the daily digest message. No
  persisted metrics (duration per scraper, LLM cost, LLM call count,
  filter throughput).
- **Log retention:** CI platform retains workflow logs for 90 days.
  After that, forensics are impossible.
- **Alerting:** Two-tier — pipeline-crash alert via messaging app if
  Python exits non-zero; workflow-failure alert for any CI-level
  failure. Good coverage for "something broke". Nothing for
  "something is quietly wrong" (e.g. scraper returns 0 for 5 days).
- **Metrics dashboard / monitoring:** None.

---

### 5.3 Documentation Quality

**README (167 lines):** Accurate. Lists 14 target sites, ATS platform
per site, role-profile counts, pipeline diagram matching code, and 13
real design decisions with rationale.

**Discrepancies found:**
- Keyword-count claim "126+" matches exactly (93 + 33 = 126). OK.
- One project-instructions file says "LinkedIn and Indeed" as data
  sources; LinkedIn is not implemented and Indeed is effectively
  disabled. Out-of-date.
- The same file references two design-spec documents; neither exists
  in the spec directory. **Broken reference.**
- The security-policy file is a 7-line stub with no threat model,
  scope, or response SLA.
- Persistent-memory notes still say "10 target sites" — actual is 14.
  Stale.
- The tools manifest lists only 10 of the 14 scrapers. Stale.

**Onboarding:** A new user could get running in <30 min: `pip install`,
set 5 env vars, `python -m src`. Clear.

**Completeness:** Excellent for README, partial for project-
instruction doc, stub for security policy. Spec docs referenced in the
project instructions don't exist.

---

### 5.4 Goal Fulfillment

**Stated goal:** "Automated daily scraper that finds role-specific job
vacancies at major national companies."

**Actual behavior:** Does exactly this. 14 target sites scraped, 2 role
profiles active, daily digest delivered, dedup works, LLM scoring
operational. Multi-role extension shipped cleanly over 2 weeks and is
proven by the commit history.

**Scope creep / undocumented capabilities:**
- CLI subset flag (documented).
- Dry-run flag (documented).
- LinkedIn scraping mentioned in project-instruction doc but not
  implemented.
- One scraper is theoretically present but dead in CI.
- Profile-harvesting artifacts exist in `data/` but there's no code in
  the repo that produces them — presumably populated by one-off
  interactive runs.

**Verdict:** Goal ~90% fulfilled. Core promise (daily role-specific
digest) is delivered reliably. Two aspirational sources are not
operational.

---

### 5.5 Blind Spots

| Blind Spot | Risk |
|-----------|------|
| No "scraper returned 0 for N consecutive days" alarm | DOM / API changes fail silently as "0 vacancies today" |
| No LLM daily spend cap or alarm | Dedup corruption → ~50× cost spike in one recovery run |
| Git repo growth unmonitored | Dedup state auto-committed daily; ~1 MB/month growth curve |
| Committed summary file with 19 named individuals | Personal-data exposure risk if repo goes public |
| Project-instruction doc references 2 spec files that don't exist | Future maintainer will hunt for missing context |
| `.gitignore` excludes 4 committed directories | Confusion about whether new files are tracked |
| Country substring-match false positives | Silent scope creep into non-target locations |
| No per-scraper ban / 429 alert | IP-block fails as one line in the daily footer — easy to miss |
| Single recipient hardcoded | Can't add a second recipient without code change |
| Test coverage excludes the 4 browser scrapers | Highest-risk code (DOM drift, WAF bypass) has zero parsing tests |

---

### 5.6 Objective Clarity Assessment

| Dimension | Rating (1-10) | Evidence |
|-----------|---------------|----------|
| Objective clarity | 9 | README is explicit, scope is bounded, role profiles are versioned YAML. |
| Goal fulfillment | 8 | 14/14 configured scrapers run; two sources aspirational vs. real. |
| Delivery reliability | 7 | Pipeline resilient to per-scraper / per-channel failure; no self-healing, no zero-result alarm. |
| Output quality | 8 | Multi-role sections, score + reasoning per match, escaped, link-sanitized. Polished. |
| Automation maturity | 8 | Fully automated via CI + external cron; zero manual steps on a normal day. |
| Self-improvement | 2 | No feedback loop — doesn't learn which matches mattered. |
| Operational visibility | 4 | Daily digest is a snapshot; no history, no dashboard, no metrics. |
| Resource efficiency | 8 | ~$3-10/month total cost, <6 min/day on free CI minutes. |
| Security posture | 7 | Secrets discipline strong; no lock file, no robots.txt check, one personal-data concern. |
| Test coverage on critical paths | 7 | 106 tests covering logic; browser scrapers untested structurally. |

---

### 5.7 Overall Rating

**7.5/10** — A well-architected, honestly-documented personal pipeline
with disciplined secrets handling, thoughtful notification-integrity
contracts, and a clean multi-role extension that shipped in 2 weeks.
The test suite (106 green tests in 5s) is better than most paid-SaaS
codebases. Points deducted for: dead source path, `.gitignore`-vs-
committed-dirs confusion, no-alarm-on-zero-results blindness, personal-
data exposure on the summary file, substring false-positive bug, no
lock file, and the committed-to-git dedup state.

---

### 5.8 Production Readiness Assessment

| Gate | Status | Evidence |
|------|--------|----------|
| **Functionality** — does it do what it promises? | PASS | 14 scrapers, 2 roles, daily digest. Dedup works. LLM scoring works. 106 tests green. |
| **Reliability** — consistent without manual intervention? | PASS | Runs daily for 22+ days with auto-commits; fault-isolated scrapers; both-channel-fail retry protects the 1-in-N outage. |
| **Error handling** — recovers gracefully? | PASS | 4 timeout layers, graceful degradation when deps missing, orphan-process cleanup, atomic dedup writes. |
| **Security** — no exposed secrets, injection, personal-data leaks? | PARTIAL | Secrets OK. Prompt injection mitigated. Committed summary file has 19 named individuals; no lock file; no daily LLM spend cap. |
| **Testing** — critical paths covered? | PARTIAL | 106 tests cover pure-Python logic well. 4 browser scrapers have no parsing tests; no integration tests against live sites. |
| **Monitoring** — can you tell when something breaks? | PARTIAL | Crash + workflow-failure alerts exist. No alarm on "scraper returned 0 for 3 days" or "LLM cost > $X". |
| **Documentation** — can someone else operate this? | PARTIAL | README excellent. Project-instructions doc references nonexistent spec docs. Security-policy stub. Manifests stale. |
| **Scalability** — handles growth without redesign? | PARTIAL | Dedup fine at 6K entries; will need a DB at 100K. Git repo growth curve is bad. LLM batch path already splits at 30. |
| **Data integrity** — consistent, backed up, recoverable? | PARTIAL | Atomic writes. Dedup state is both the only state AND git-tracked, so "backup" = "previous commit". Corrupt file = notification flood. |
| **Dependency health** — maintained, pinned, vulnerability-free? | PARTIAL | Top 5 deps maintained. But compatible-release operator is not a lock file. No vulnerability scan in CI. |

**Verdict: Ready to ship for personal use. Needs ~4 fixes before being
shareable as a public reference project.**

Blockers for public reuse:
1. Scrub the committed summary file of personal names.
2. Fix `.gitignore` vs committed-dirs confusion.
3. Add a lock file for reproducible installs.
4. Move dedup state out of git into the CI platform's cache.

---

### 5.9 Top 10 Ranked Recommendations

| # | Action | Impact | Effort | Who Implements |
|---|--------|--------|--------|----------------|
| 1 | Scrub the committed profile-summary file — replace personal names with role-title patterns only, or move the file out of any public-bound repo. Personal-data regulation applies. | Critical | Low — 30-min edit | Human |
| 2 | Move the dedup state file from git-tracked to the CI platform's cache (keyed on a rolling date). Delete the "commit updated dedup" step from the workflow. Stops ~1 MB/month repo-size growth. | High | Medium — rewrite 30 lines of workflow YAML + test | Agent |
| 3 | Fix the country-filter substring bug: replace `any(... in location.lower())` for a 2-letter code with a proper city-list check or parsed country code. | High | Low — replace 1 line per scraper | Agent |
| 4 | Add a "zero-results alarm": if any scraper returns 0 for 3 consecutive days, emit a `[SCRAPER DRIFT]` warning in the digest. Catches DOM / WAF changes before they silently miss a week of matches. | High | Medium — add rolling counter to a health-state file | Agent |
| 5 | Pin dependencies with a lock file (`uv.lock` or `requirements.txt`) and make CI use it. Reproducible builds. | High | Low — one command + one workflow-line change | Human |
| 6 | Fix `.gitignore` inconsistency: either `git rm --cached -r` the committed-but-ignored directories (if they shouldn't be tracked) OR remove those lines from `.gitignore` (if they should be). Pick one. | Medium | Low — 5 min | Human |
| 7 | Add per-scraper HTTP retry with exponential backoff. Single transient 503 currently loses the day for that company. | Medium | Low — 1 line per scraper or a shared helper | Agent |
| 8 | Delete the dead scraper and its registry entry, OR document it as "interactive-mode only" with a clear skip reason in the digest footer. | Medium | Low — 5 min to delete, 15 min to gate | Agent |
| 9 | Add a daily LLM spend cap — track total API calls in the scoring function and abort if > N (default 500). Protects against dedup-corruption cost spike. | Medium | Low — one counter + one conditional | Agent |
| 10 | Repair doc references: restore the two referenced spec files from git history or remove the broken links. Update persistent-memory notes to say "14 sites" not "10". Update tools manifest to list all 14 scrapers. | Low | Low — 15 min of edits | Agent |

---

### 5.10 Value Assessment

| Dimension | Rating (1-5) | Evidence |
|-----------|--------------|----------|
| Problem clarity | 5 | Precisely scoped: daily role-matched jobs at a defined set of target sites. README + project-instructions define the audience and output in one paragraph. |
| Audience definition | 4 | Audience = the maintainer personally. YAML role profiles make it re-usable by anyone who edits the files, but no onboarding docs for a second user. |
| Maturity vs. claims | 4 | Claims "automated daily pipeline for 14 sites" and delivers exactly that. Multi-role upgrade from single-role shipped cleanly. |
| Measurable value | 4 | User receives ~80 vacancies/day filtered to 0-5 matches. If even 10% of matches are worth reading, the user saves ~30 min/day vs. manual checking. |
| Differentiation | 3 | Commercial job alerts cover the general market better. This project's differentiator is the **per-role YAML taxonomy** + **LLM relevance scoring**, which no generic job board offers. But the codebase is not packaged for other users. |
| Adoption readiness | 2 | Personal tool, private repo, secrets managed as platform secrets with opinionated names, role profiles hardcoded to one career arc. Would need documentation, templating of env-var names, and a sample role profile for non-target use cases to be shareable. |

---

### 5.11 The Uncomfortable Question

One of the 14 scraped sites belongs to an employer the maintainer might
realistically want to work for, and the scraper deliberately uses a
headed-browser-via-virtual-display technique to bypass that employer's
WAF (specifically designed to block automated access). The README's
"Key Design Decisions" section calls this out openly — admirable, but
the repo is private, so the admission exists only for the maintainer.
If this project ever goes public as a portfolio piece, you are openly
demonstrating willingness to bypass a security control at an
organisation you might interview with. That's a tension worth naming
before a hiring manager reads a commit from a week earlier and
notices the headed-mode rationale in a nearby file.

Harder question: value created is ~30 min/day of time saved for one
person. Effort invested is 22 days of active commits, ~2,600 lines of
production Python, a multi-role refactor, 106 unit tests, and daily
auto-commits for the foreseeable future. That's ~40-60 hours of
engineering work. Would you ship this exact architecture at a company?
Probably not — you'd use a vendor product or an RSS-to-email alert on
each career page. You built it because it's interesting, because it
demonstrates capability, and because it solves a real (small) problem.
That's fine — **but recognize that the project's value is now primarily
as a portfolio artifact, not as a time-saver**. Invest accordingly:
every hour spent fixing a rare-edge-case bug is an hour that didn't go
into the real career work.

---

## Phase 6: Resilience Testing

**Backups:** No backup mechanism for the dedup state exists in the
project, but the file is committed to git, so every daily run produces
an implicit git snapshot. Recovery path: `git checkout HEAD~1 --
data/dedup_file.json`. This is not a backup strategy (git is not a
backup), but it's observable and restorable.

**Restore test (code analysis only — no writes to the project):** The
dedup loader catches `JSONDecodeError` and falls back to an empty dict
(unit-tested). If the dedup file is deleted, the next run rebuilds from
scratch. Downstream impact: every currently-live vacancy across all 14
sites (estimated 2,000-3,000) would be "new" and pass through the
pipeline. With ~10-15% keyword-pass rate, ~200-300 vacancies would hit
LLM scoring, costing ~$0.50-1.00 in API calls for that one recovery
run. Recoverable but noisy — the digest message would be massive and
might hit the chunked-send path multiple times.

**Operational resilience assessment:**
- **Component failure:** Any single scraper failing is absorbed.
- **Service failure:** LLM down → keyword-only matches. One channel
  down → the other delivers. Both down → retry next run.
- **Platform failure:** CI platform down → no run that day; no
  notification, no state change.
- **State corruption:** Dedup corruption → notification flood, then
  self-heal.
- **Secret rotation:** Works transparently via env vars; next run
  picks up new secret.

**Disaster recovery:** RPO 1 day (yesterday's dedup from git), RTO ~10
minutes (clone, install, set secrets, run). For a personal pipeline,
both are fine.

**Resilience rating: STRONG** for the failure modes the maintainer
anticipated (scraper outages, LLM outages, notification outages);
**WEAK** for silent-drift failures (a scraper returns 0 for 5 days;
the keyword taxonomy is 6 months out-of-date with how companies
describe the target roles). The second class is the one to worry
about going forward.

---

*Generated by [deep-project-audit](https://github.com/belousov-petr/deep-project-audit) v1.0.0*
