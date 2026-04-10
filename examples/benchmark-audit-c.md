# Deep Project Audit — Browser Automation: Saved Posts CSV Exporter

**Audit date:** 2026-04-10
**Methodology:** deep-project-audit v1.0.0 (6-phase structured audit)
**Auditor:** Claude Opus 4.6

> **Note:** This is an anonymized audit of a real project. Account names
> and personal identifiers have been replaced with generic placeholders.

---

## 4.1 What the Project Is

A browser automation script that exports saved posts from a social
media platform into a CSV file. Designed to run inside an AI-powered
browser extension (Claude in Chrome). Injects a floating control panel
(4 buttons + log) into the platform's saved posts page, iterates
through each post extracting metadata from the DOM, copies the post URL
via clipboard for cross-validation, writes a verified CSV row, and
unsaves the post only after confirming the CSV write succeeded. The
project is 3 JavaScript files (~1,000 lines total): an annotated
version, a minified version, and an older v1 script.

---

## 4.2 What Works Well

**Safety-first unsave logic.** The script never unsaves a post without
a verified CSV row on disk. The flow is: extract data → write CSV →
verify write → unsave. If any step fails, the post stays saved.

**Evidence:** `appendRow()` writes to disk via File System Access API,
then `verifyLastRow()` reads the file back and confirms the post ID
exists in the last line. Only then does `doUnsave()` execute.

**Dual URL validation.** Post URLs are extracted from both the DOM and
the clipboard (via "Copy link to post"). If both sources agree, the URL
is high-confidence. If they disagree, the DOM URL is used and the
mismatch is logged as `url_mismatch` in the CSV's `error_reason` column.

**Stuck-loop detection.** If the same post stays at position 0 for 3
consecutive iterations (indicating the unsave failed or the DOM didn't
refresh), it gets `data-skip` and the loop moves on. Prevents infinite
loops.

**Resume capability.** Opening an existing CSV file loads all captured
post IDs into a `Set`. Already-captured posts are unsaved without
re-writing. New posts append after existing rows. The CSV is always in
a consistent state.

**Human-like timing.** Randomized delays (0.5-2s) after opening
dropdown menus and between posts reduce bot-detection risk. This is a
real concern on the target platform.

**Good README.** Clear setup instructions, CSV schema documentation,
resume workflow, safety principles, and guidance on updating selectors
when the platform changes its markup.

---

## 4.3 Critical Issues

**1. Three functionally-related JS files with no clear versioning.**
The repo contains `validated-script_v1.0.js` (v1), `linkedin_exporter.annotated.js` (v2 annotated), and `linkedin_exporter.min.js` (v2 minified). The v1 file is dead code — superseded by v2 but still in the repo. Git history shows 4 deleted prompt files. The repo looks like it went through several iterations without cleanup.

**Impact:** Confusion for anyone cloning the repo. Which file is current? The README clarifies (annotated + min), but the v1 file's presence contradicts this.

**2. No .gitignore, no license, no package.json.**
The repo has zero project configuration. No `.gitignore` (so any stray files get committed), no license (legally ambiguous for anyone wanting to use it), no `package.json` (no dependency management, no project metadata).

**3. CSV parsing in the "Open CSV" handler is fragile.**
The `openBtn` handler implements a hand-rolled CSV parser (lines 436-463 of the annotated version) to parse quoted fields with commas. This works for the specific CSV schema but doesn't handle all edge cases (e.g., newlines inside quoted fields, BOM characters). Since the script writes and reads its own CSV, this is low risk — but if a user edits the CSV in Excel and re-opens it, the parser may break.

---

## 4.4 Architecture & Code Quality

**Structural analysis:**

| Aspect | Assessment |
|--------|-----------|
| Storage model | Append-only CSV via File System Access API. Write-then-verify pattern. Good for crash safety. |
| Execution model | Single async loop, no parallelism. Correct for browser DOM manipulation. |
| External dependencies | Zero. Pure browser APIs (DOM, Clipboard, File System Access). |
| Single points of failure | Platform DOM structure. If selectors change, the entire tool breaks. Mitigated by documenting breakable selectors in "Section 2: DOM Finders." |
| Scalability | Linear in number of saved posts. ~3-5s per post (delays included). 100 posts ≈ 5-8 minutes. |

**Design pattern coherence:** Clean single-file design. Helper functions
at top, DOM finders, CSV I/O, unsave subroutine, UI injection, main
loop. Logical ordering.

**Code quality:**
- Annotated version is genuinely well-commented — change markers
  (`★ CHANGE 1`, `★ CHANGE 2`) highlight v1→v2 differences.
- `validated-script_v1.0.js` (944 lines) is dead code — the v2 files
  supersede it entirely. Should be deleted or moved to a `legacy/`
  folder.
- Empty files in git history: 4 "Prompt" files were created then
  deleted in separate commits. Messy commit history.
- Template literal syntax appears broken in the minified version
  (`console.log[CSV] ${msg}`) — this is likely a display artifact
  from the minification process, not a runtime error.

**Test coverage:** None. No test files, no test framework. For a
browser automation script that interacts with a live platform, automated
testing is difficult — but at minimum, unit tests for `parsePostId()`,
`approxDate()`, `csvEscape()`, and `isValidLinkedInPostUrl()` would
catch regressions.

---

## 4.5 Error Handling, Resilience & Failure Modes

**Crash scenarios:**
- **Browser tab closed mid-run:** CSV is append-only and verified after
  each write. At most 1 post may be unsaved without CSV confirmation
  (the one currently being processed). All prior posts are safe.
- **Platform rate-limits or blocks:** Script would fail to open dropdown
  menus (8s timeout). Posts get `data-skip` and the loop continues.
  No automatic backoff beyond the randomized delays.

**Timeout coverage:**
- Dropdown menu open: 8s poll timeout. Good.
- "Link copied" confirmation: 5s poll timeout. Good.
- Unsave confirmation: 5s poll timeout. Good.
- No overall session timeout — script runs until all posts processed or
  user clicks Stop.

**Silent failures:**
- `clipboard.readText()` failure: logged as warning, falls back to DOM
  URL. Good degradation.
- Unsave not confirmed (post still visible after 5s): logged as
  `unsave_unconfirmed`, CSV row has `unsave_confirmed=false`. Good
  tracking.
- `patchUnsaveConfirmed()` failure: caught and logged as warning.
  Doesn't break the loop.

**Edge cases:**
- Post with no URL in DOM and clipboard read fails: skipped with
  `no_url`, post stays saved. Correct.
- Post with no parseable ID: skipped, post stays saved. Correct.
- Platform changes DOM structure: `findPostList()` returns null, script
  stops with clear error message. Good.

---

## 4.6 Performance & Bottleneck Analysis

**Timing:**
- Per-post processing: ~3-5s (randomized delays dominate)
- 100 posts: ~5-8 minutes
- 1000 posts: ~50-80 minutes

**Bottleneck:** The randomized delays are intentional (anti-detection).
They dominate runtime. Actual DOM operations are <100ms each. This is
the correct trade-off — faster execution risks account restrictions.

**Resource waste:**
- `verifyLastRow()` reads the entire CSV file on every post to check
  the last line. At 1000+ rows, this becomes noticeable. Could seek to
  end of file instead.
- `patchUnsaveConfirmed()` reads and rewrites the entire CSV to flip
  one field. At scale, this is O(n) per post for a single-field update.
  Not a practical issue under ~10K rows.

**Cost analysis:**
- Token cost per run: ~1,400-1,600 tokens (minified version). Minimal.
- No API costs, no infrastructure costs.
- Runtime cost: user's browser tab must stay open and focused.

---

## Phase 5: Security, Readiness & Recommendations

### 5.1 Security & Data Exposure

**Secrets:** No API keys, no credentials, no authentication tokens in
code. The script runs in the user's authenticated browser session.

**Injection:** No user input is evaluated as code. CSV values are
escaped via `csvEscape()` which replaces double quotes and strips
newlines. The injected UI uses `textContent` (not `innerHTML`) for
log messages — no XSS surface.

**Privacy:** The CSV contains post URLs, author names, profile URLs,
and content snippets from the platform. This is the user's own saved
data — no third-party PII collection. However, the CSV file has no
encryption and no access controls beyond the filesystem.

**Platform compliance:** DOM scraping and automated unsaving may violate
the platform's Terms of Service. The randomized delays mitigate
detection but don't eliminate the risk.

### 5.2 Logging & Observability

- **Runtime log:** Floating panel in the browser shows per-post
  progress with timestamps. Also logs to `console.log` for DevTools.
- **CSV as audit trail:** Every row records `processed_at`,
  `write_verified`, `unsave_confirmed`, `url_source`, and
  `error_reason`. This is an unusually thorough audit trail for a
  browser script.
- **No persistent logging.** When the tab closes, the log panel is
  gone. Only the CSV survives.

### 5.3 Documentation Quality

**Accuracy:** README accurately describes the current v2 script.
CSV schema documentation matches the actual fields. Setup instructions
are correct.

**Discrepancy:** README does not mention `validated-script_v1.0.js` —
the file exists in the repo but is not referenced anywhere. This
suggests it was forgotten during cleanup.

**Completeness:** Good for the scope. Missing: changelog, contribution
guidelines, license.

### 5.4 Goal Fulfillment

**Stated objective** (from README): "Browser automation script that
exports all saved posts to a CSV file and unsaves each one after
processing."

**Actual behavior:** Does exactly this. URL extraction, CSV writing,
verification, unsaving, resume, dedup, and stuck-loop detection all
work as described. The tool delivers on its promise.

**Verdict:** Goal 95% fulfilled. Minor gap: the README mentions
"Claude in Chrome shortcut" setup, which is specific to one browser
extension. The script itself works in any browser with File System
Access API support.

### 5.5 Blind Spots

| Blind Spot | Risk |
|-----------|------|
| No rate-limit detection | If the platform starts returning errors or CAPTCHAs, the script keeps trying. No escalating backoff. |
| No session tracking across runs | The `run_id` identifies a session, but there's no summary of how many posts were processed per run. |
| No CSV backup | A filesystem error during `patchUnsaveConfirmed()` could corrupt the CSV. No backup copy. |
| No selector health check | No pre-flight validation that expected DOM selectors exist before starting the loop. |

### 5.6 Objective Clarity Assessment

| Dimension | Rating (1-10) | Evidence |
|-----------|---------------|----------|
| Objective clarity | 9 | Single clear purpose: export saved posts to CSV |
| Goal fulfillment | 9 | Does exactly what it promises, with safety guarantees |
| Delivery reliability | 7 | Works reliably when selectors are valid; brittle to DOM changes |
| Output quality | 8 | Thorough CSV schema with verification and audit fields |
| Automation maturity | 6 | Requires manual trigger, manual page navigation, browser tab focus |
| Self-improvement | 2 | No learning from failures, no selector auto-detection |
| Operational visibility | 6 | Good runtime log; no persistent analytics |
| Resource efficiency | 8 | Zero dependencies, minimal token cost, intentional throttling |

### 5.7 Overall Rating

**7/10** — A well-engineered browser automation script that delivers
exactly what it promises with genuine safety guarantees (never unsave
without verified CSV). Clean code, good README, thoughtful error
handling. Loses points for dead code in the repo (v1 file), missing
project configuration (no license, no .gitignore), zero tests, and
brittleness to DOM changes. For a personal tool, this is solid.

### 5.8 Production Readiness Assessment

| Gate | Status | Evidence |
|------|--------|----------|
| **Functionality** — does it do what it promises? | PASS | Exports saved posts to CSV with verification and unsave. Works as documented. |
| **Reliability** — consistent without manual intervention? | PARTIAL | Requires manual trigger and browser focus. Reliable once running, but brittle to DOM changes. |
| **Error handling** — recovers gracefully? | PASS | Dropdown timeouts, clipboard failures, stuck loops — all handled with fallbacks. |
| **Security** — no exposed secrets, injection, PII? | PASS | No secrets in code. CSV escaping prevents injection. No third-party PII collection. |
| **Testing** — critical paths covered? | FAIL | Zero tests. Pure functions (parsePostId, csvEscape, approxDate) are easily testable. |
| **Monitoring** — can you tell when something breaks? | PARTIAL | Runtime log panel good. No persistent logging or analytics. |
| **Documentation** — can someone else operate this? | PASS | Clear README with setup, usage, resume workflow, and selector update guide. |
| **Scalability** — handles growth without redesign? | PARTIAL | Linear scaling. CSV read-all-on-verify becomes slow at 10K+ rows. |
| **Data integrity** — consistent, backed up, recoverable? | PARTIAL | Append-only CSV with verification. No backups. Patch operation risks corruption. |
| **Dependency health** — maintained, pinned, vulnerability-free? | PASS | Zero external dependencies. Pure browser APIs. |

**Verdict:** Needs 2 fixes before sharing — add a license file and
remove the dead v1 script. Add basic tests for pure functions if aiming
for community contributions.

### 5.9 Top 10 Ranked Recommendations

| # | Action | Impact | Effort | Who Implements |
|---|--------|--------|--------|----------------|
| 1 | Add a LICENSE file (MIT recommended for a utility tool) | High — legally required for others to use | Low — one file | Human |
| 2 | Delete `validated-script_v1.0.js` (dead code, superseded by v2) | Medium — reduces confusion, cleans repo | Low — one git rm | Human |
| 3 | Add `.gitignore` (exclude .csv files, node_modules, .DS_Store) | Medium — prevents accidental data commits | Low — one file | Human or agent |
| 4 | Add unit tests for pure functions: `parsePostId`, `approxDate`, `csvEscape`, `isValidLinkedInPostUrl` | Medium — catches regressions on URL parsing | Medium — ~50 lines | Agent |
| 5 | Add selector pre-flight check: validate all key selectors exist before starting main loop | Medium — fails fast with clear error instead of mid-run failures | Low — ~15 lines | Agent |
| 6 | Add escalating backoff when multiple consecutive posts fail | Medium — graceful degradation under rate-limiting | Low — ~10 lines | Agent |
| 7 | Optimize `verifyLastRow` to read only last 1KB instead of entire file | Low — performance at scale | Low — seek to end | Agent |
| 8 | Add run summary at end: posts processed, succeeded, failed, duration | Low — operational visibility | Low — ~10 lines | Agent |
| 9 | Squash or clean up git history (4 deleted Prompt files, messy commits) | Low — cosmetic, improves repo presentation | Low — one rebase | Human |
| 10 | Add CHANGELOG.md documenting v1→v2 changes | Low — helpful for contributors | Low — one file | Human |

### 5.10 The Uncomfortable Question

This is a browser automation tool that modifies another platform's data
(unsaving posts). It works today because the DOM selectors are correct.
When the platform ships a markup update — and they will — every selector
in "Section 2: DOM Finders" could break at once. There's no selector
versioning, no fallback strategy, no automated detection of selector
breakage. The tool's reliability is entirely dependent on a third party
that has no interest in keeping it working. The real question is: should
this be a browser extension with proper DOM observation patterns instead
of an injected script?

---

## Phase 6: Resilience Testing

**Backups:** No backup mechanism. The CSV file is the sole output. If
it's deleted or corrupted, all data is lost. The posts have already been
unsaved on the platform, so there's no way to re-export them.

**Recovery:** If the script stops mid-run, the resume feature
(Open CSV → Start) recovers cleanly — already-processed posts are
skipped via dedup. This is effective disaster recovery for the most
common failure mode (browser tab closing).

**Operational resilience:** The script runs in a browser tab. It cannot
survive tab closure, browser crash, or machine restart. No persistence
layer beyond the CSV file.

---

*Generated by [deep-project-audit](https://github.com/belousov-petr/deep-project-audit) v1.0.0*
