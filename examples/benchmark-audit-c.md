# Deep Project Audit — Browser Automation: Saved Posts CSV Exporter

**Audit date:** 2026-04-17
**Methodology:** deep-project-audit v1.0.0 (6-phase structured audit)
**Auditor:** Claude Opus 4.7

> **Note:** This is an anonymized audit of a real project. Account names, platform names, and personal identifiers have been replaced with generic placeholders.

---

## Phase 1 Summary — Discovery

| Item | Finding |
|---|---|
| Project type | Browser-injected JavaScript automation (single-use scraper / unsaver) |
| Tech stack | Vanilla JS (ES2020+), File System Access API, Clipboard API, DOM |
| Data stores | None (user-selected local CSV file on disk) |
| External dependencies | Zero npm dependencies. Pure browser APIs. |
| Files tracked | 4: `README.md`, `exporter.annotated.js`, `exporter.min.js`, `validated-script_v1.0.js` |
| Total JS LOC | 1,953 (1,010 annotated + 1 min one-liner + 943 v1) |
| Git history | 18 commits, single author, 4 deleted `Prompt*` files, 1 merged PR |
| Stated goal | "Exports all saved posts to a CSV file and unsaves each one after processing" |
| Missing project files | `.gitignore`, `LICENSE`, `package.json`, `CONTRIBUTING.md`, `CHANGELOG.md` — ALL absent |
| Agent skill? | No |
| Database? | No -> Phase 3 skipped |

---

## 4.1 What the Project Is

A browser-injected JavaScript tool that exports a user's saved posts from a social media platform into a local CSV file via the File System Access API, then unsaves each post on the platform once the CSV row is confirmed on disk. Designed to run as an AI-browser shortcut — the entire script is pasted into the shortcut body and injected into the platform's saved-posts page. Injects a floating 4-button control panel (New CSV / Open CSV / Start / Stop) plus a live log panel, iterates through each visible `<li>` post card, extracts metadata from the DOM, cross-validates the post URL by triggering "Copy link" and reading `navigator.clipboard`, appends one CSV row per post, reads the file back to verify the last line contains the expected `post_id`, and only then simulates clicks on the more-actions menu -> "Unsave". Supports resume via `Open CSV` which hydrates a dedup `Set` from the `post_id` column. Two currently-canonical files (annotated + minified) plus one dead v1 script. Zero dependencies, no build system, no test suite.

---

## 4.2 What Works Well

**Write-then-verify-then-unsave invariant (genuine data-safety primitive).** `mainLoop()` at `exporter.annotated.js:957-984` writes the row, calls `verifyLastRow()` to read the file back and confirm the `post_id` appears in the last line, and ONLY then calls `doUnsave()`. If write OR verification fails, the post stays saved. If the loop crashes between write and unsave, on resume the dedup Set recognises the `post_id` and the remaining post gets unsaved without re-writing. This is a stronger guarantee than most quick-and-dirty scrapers offer, and it's the load-bearing design decision.

**Dual-source URL validation with explicit provenance.** Post URLs are extracted from both the DOM `<a>` tag and the clipboard (via the platform's native "Copy link to post"). The four-branch resolution in `annotated.js:886-916` records `url_source` as `both` / `dom` / `clipboard`, and on mismatch writes `url_mismatch:clip=<url>` into the `error_reason` column — the evidence of disagreement survives in the output file. This is better than the typical "trust one source" approach.

**Stuck-loop detection prevents runaway retries.** `annotated.js:756-768` tracks the post at position [0] across iterations. Three consecutive appearances of the same `postId` without progress sets `data-skip` on the `<li>` and moves on. Without this, a broken unsave path would loop forever.

**Randomised human-like delays.** `randomDelay(500, 2000)` is applied after dropdown opens and between posts (`annotated.js:483, 839, 991`). The annotated comments explicitly flag this as "bot-detection countermeasure" — the author understands the adversary.

**Append-only CSV + seek-to-end-of-file pattern.** `appendRow()` (`annotated.js:357-363`) re-opens the file, seeks `file.size`, writes one row, closes. This is the correct pattern for File System Access API which lacks a native append mode — it avoids the common pitfall of either truncating or holding a stale writable stream across `await` boundaries.

**Annotated version is genuinely educational.** `exporter.annotated.js` is ~1,010 lines of which ~60% is comments. Every non-obvious decision has a `WHY:` block. `* CHANGE 1` / `* CHANGE 2` markers highlight the v1->v2 diff (randomised delay + full URL preservation). This is maintenance documentation embedded in the source — rare for a weekend project.

**README is tight and honest.** Clear setup steps, full CSV schema, a "Safety principles" section that matches the code, a "When the platform changes their markup" section that enumerates the brittle selectors. Token-cost table at the end quantifies the minified-vs-annotated trade-off. README describes what exists, not aspirations.

---

## 4.3 Critical Issues

**1. `validated-script_v1.0.js` is committed but syntactically invalid JavaScript — it cannot be executed.** This is a parse-time failure, not a runtime bug. Verified: **the file contains zero backtick characters** (`0x60` count = 0 via bytewise scan), meaning every template literal in the file is a broken non-string (missing both opening and closing backticks). Examples from the file as stored on disk:

- L31: `line.textContent = [${new Date().toLocaleTimeString()}] ${msg};` — no backticks around the template
- L39: `console.log[CSV] ${msg});` — not even `console.log(...)` — would throw a reference error
- L135: `return "${val}";` — returns the literal 7-char string `${val}` (dollar-brace-val-brace)
- L235: `const needle = "false","${runId}";` — comma operator, not a template literal
- L249: `const patched = text.slice(0, idx) + "true","${runId}" + text.slice(idx + needle.length);` — same
- L259 in `patchUnsaveConfirmed`: `log[WARN] Could not patch unsave_confirmed: ${e.message});` — `log` is not even called as a function (no opening paren)

**Impact:** If any user pastes this v1 file into their AI-browser shortcut (as the README-less filename `validated-script_v1.0.js` arguably suggests is a "validated" version), the browser throws a syntax error at script injection, and they get no feedback from the UI. Worse, this gets indexed by search engines and could be copy-pasted by someone who doesn't read the README. This is not merely "dead code that should be deleted" — this is **broken code masquerading as a validated release** (the filename says "validated-script_v1.0").

**Evidence command:** `python -c "open('validated-script_v1.0.js','rb').read().count(b'\x60')"` -> `0`. Both annotated (42) and min (36) have backticks.

**Fix:** `git rm validated-script_v1.0.js` — or at minimum add a deprecation banner at the top. Renaming to `legacy_v1_broken_do_not_use.js` and moving to a `legacy/` folder would also work.

**2. Zero project configuration — no LICENSE, no .gitignore, no package.json.** For a public repo the first two are blockers:

- **No LICENSE**: under default copyright law anyone cloning this has **no legal right to use, modify, or redistribute** it. The README implicitly invites use ("paste this into your shortcut") but the repo license gives no such permission. Anyone incorporating it into their workflow is technically infringing.
- **No .gitignore**: the working directory has no protection against accidentally committing the user's own CSV output (which contains personal data), or `.env`, or `node_modules` if anyone ever runs tooling here.
- **No package.json**: not strictly needed for a browser-injected script, but its absence forecloses linting, minification automation, versioning, and dependency-management hygiene.

**3. No automated tests — for pure, testable functions.** Zero test files. The script has at least 5 cleanly-pure helpers that would each fit in a 10-line unit test and would catch 80% of regressions on platform markup changes: `parsePostId`, `stripQueryParams`, `isValidPostUrl`, `approxDate`, `csvEscape`. Three URL formats, two date-unit edge cases (`mo` vs `m`), and CSV escape rules for quotes and newlines — all trivially unit-testable without any browser or platform access. Their absence is a choice, not a constraint.

**4. The minified version is not source-of-truth — it's a hand-minified copy.** Both `exporter.annotated.js` and `exporter.min.js` are hand-maintained separately (committed as independent "Create ..." commits, not generated from each other). There is **no build script** to derive min from annotated. When the annotated version is updated, the minified version can silently drift. The README asserts "functionally identical" but there's no CI check — the only guarantee is the author's care at commit time. Given that the shortcut body uses the minified file (per README), any drift affects production behaviour while the annotated version remains the debugged reference. This is a correctness-of-distribution issue.

**5. `.git/config` remote URL contains an embedded Personal Access Token.** During clone, the remote was stored as `https://<account>:[REDACTED]@<git-host>/...`. This is local-only (not committed), but it means:
- Anyone with filesystem access to the working directory exfiltrates the PAT
- `git log` / `git remote -v` output (often pasted in bug reports, tutorials, or AI-assistant conversations) leaks the token
- A push from this clone authenticates as the token owner — if the clone is shared or checked in elsewhere, identity confusion

**Fix:** `git remote set-url origin https://<git-host>/<account>/<repo>.git` and rely on `gh auth login` or a credential helper. The embedded PAT in this clone's config should be treated as compromised and rotated.

---

## 4.4 Architecture & Code Quality

Below: structural analysis, MECE check, code-quality notes, dead-code inventory, and test coverage. Evidence is cited by file + line throughout.

### Structural Analysis

| Aspect | Assessment |
|---|---|
| Storage model | Append-only CSV via File System Access API. Write-verify-unsave is crash-safe. `patchUnsaveConfirmed()` introduces an in-place rewrite — only mutation step in an otherwise append-only system. |
| Execution model | Single async loop, no concurrency. Correct for DOM manipulation — parallelism here would trigger the platform's rate limiter and confuse the UI state. |
| External dependencies | Zero. Pure browser APIs: `showSaveFilePicker`, `showOpenFilePicker`, `navigator.clipboard.readText`, `MouseEvent`, `URL`. All modern Chromium-only APIs. |
| Single point of failure | Platform DOM selectors. Hardcoded strings like `button[aria-label*="take more actions"]`, `div.artdeco-dropdown__item`, `main ul`. One internationalisation change on the platform's side (e.g. `aria-label` in a non-English locale) kills the tool silently. |
| Browser SPOF | File System Access API is Chromium-only. Safari and Firefox cannot run this script at all. Not documented. |
| Scalability | O(n) per post including an O(n) full-file read in `verifyLastRow` and O(n) full-file read+rewrite in `patchUnsaveConfirmed`. At 1000 rows each post re-reads & rewrites ~1000 rows ~= O(n^2) total across the run. At 100 posts: negligible. At 10k posts: measurable disk churn but still completes. |

### MECE Check

- **Gap**: no separation between "script logic" and "platform selectors". If these were split into two files (or two sections with an exportable config object), swapping selectors for platform redesigns wouldn't risk breaking logic.
- **Overlap**: dedup check appears twice in main loop (`annotated.js:805` and `:929`). Intentional — first pass on DOM-URL id, second pass after clipboard resolution. This is correct but the two paths handle unsave differently (first pass doesn't check `_isRunning` before `randomDelay`, second does). Minor symmetry bug, not critical.
- **Contradiction**: README says min and annotated are "functionally identical" but there's no mechanism enforcing that.

### Code Quality

- Single-file monolith — acceptable given it must be injected as one `<script>` block.
- `mainLoop()` is ~305 lines (`annotated.js:688-997`). Over the 500-line / 50-line rule-of-thumb. Could be decomposed into `processPost(li)`, `resolveUrl(postUrlDom, clipboardUrl)`, `writeAndVerify(row, postId)`.
- No TypeScript, no JSDoc `@param` types, no runtime input validation.
- `window._isRunning`, `window._csvFileHandle`, `window._dedup`, `window._runId` — four globals on `window.*`. Naming convention (underscore prefix) is consistent. No conflicts with the platform's globals, but technically vulnerable to an extension or another injected script.
- `patchUnsaveConfirmed` uses `text.lastIndexOf('"false","${runId}"')` followed by a 50-char lookahead window to verify `postId`. Race condition via identical second-level run_ids is unlikely but not impossible.

### Dead Code & Debt

- `validated-script_v1.0.js` — 943 lines, entirely dead (see Critical Issue #1).
- 4 "Prompt*" files created and deleted across multiple commits. Git history weight ~= 9/18 commits = 50% noise.
- `[...document.querySelectorAll('div, span, p, li')]` in toast detection (`annotated.js:854-857`) — scans EVERY div/span/p/li on the page looking for "Link copied to clipboard" text. On a long platform feed this is thousands of nodes scanned up to 33x (5000ms/150ms). This is a correctness choice but it is wasteful.

### Test Coverage

**None.** Zero test files, no framework. Effort estimate: `parsePostId` + `csvEscape` + `approxDate` + `isValidPostUrl` + `stripQueryParams` = 5 x ~15-line tests = ~75 lines total in Jest or Node's built-in `node:test`.

**Complexity hotspots:**
1. `mainLoop` body (305 lines, 15+ branches) — should be decomposed
2. `openBtn` handler inline CSV parser (28 lines, nested state machine) — should be a named function `parseCsvLine(line)` and unit-tested

---

## 4.5 Error Handling, Resilience & Failure Modes

Every failure mode below was traced through the code (not just inferred from try/catch existence). Each row names the failure, what actually happens, the evidence, and a verdict.

### Crash Scenarios Traced

| Failure | What happens | Evidence | Verdict |
|---|---|---|---|
| Browser tab closed mid-run | Write-verify-unsave invariant holds. At most the currently-processing post may have been written but not unsaved (stays saved on the platform). On resume, dedup catches it. | `annotated.js:960, 980-984` | OK |
| File handle lost (e.g. page reload revokes permissions) | `appendRow` throws, caught at L964 -> `log('write_failed'); break`. Loop exits cleanly. User must re-Open CSV. | `annotated.js:958-966` | OK but user has to know to click Open CSV, not Start |
| Clipboard read blocked (permission prompt denied) | Caught at L863-866 -> `log('Clipboard read failed'); clipboardUrl = ''`. Falls through to "domOk only" branch. | `annotated.js:862-867` | Good degradation |
| Dropdown doesn't open (platform 429 / network lag) | `poll()` returns null after 8s -> `data-skip` set, continue. | `annotated.js:828-834` | OK, but repeated dropdown_timeout events get no aggregation / backoff |
| Unsave click succeeds but `<li>` doesn't disappear | `poll()` returns null after 5s -> returns `false`, logs `unsave_unconfirmed`, `patchUnsaveConfirmed` is **NOT** called -> row stays with `unsave_confirmed="false"` -> visible on resume | `annotated.js:497-507, 983` | Correct |
| `patchUnsaveConfirmed` fails (disk full / lost handle during rewrite) | try/catch at L400-426 -> logs warning, continues. Row keeps `unsave_confirmed="false"`. No data loss, just noisy. | `annotated.js:399-427` | OK |
| Platform redesign — selectors return null | `findPostList()` returns null -> main loop logs error and breaks. | `annotated.js:697-700` | Fails fast, good |
| Platform A/B test shows "take more actions" in a different language | `findPostList()` still succeeds on English users but returns null for e.g. German. No documented fallback. No retry with alternate selectors. | `annotated.js:279-286` | Silent total failure for localised accounts |
| User clicks Stop | Flag flips; loop exits at next `!window._isRunning` check. No abort of in-flight await — current post completes. | `annotated.js:653-656, 694, 808, 932, 987` | Correct cooperative cancellation |

### Silent Failures / No Aggregation

- No failure-rate counter. If 50% of posts produce `dropdown_timeout`, nothing surfaces this as "something is wrong with the selector" vs "the platform is slow today". Both produce line-by-line log entries.
- No heartbeat. If the script hangs inside a `poll()` call, the only symptom is an absence of new log lines — easy to miss.
- No end-of-run summary. When the loop exits (done or stop), it logs only "Loop ended" — not "Processed 47 posts, 3 unsave_unconfirmed, 2 dropdown_timeout, 1 url_mismatch".

### Retry / Backoff

**None.** No exponential backoff on repeated dropdown_timeouts. No circuit breaker. If the platform starts returning CAPTCHAs (which don't throw — the CAPTCHA is the DOM), the script marches on.

### Data Integrity

- Append-only file with verified writes. One post per row. CSV field escaping handles quotes and newlines (`csvEscape` at L228-232).
- `patchUnsaveConfirmed` performs an in-place rewrite (`createWritable()` without `keepExistingData:true` at L421 -> truncates, then writes the full patched text). **Crash during this rewrite = total CSV loss.** There's no temp-file-then-rename pattern. If the browser crashes between truncate and write completion, the file is empty or partial — every row from the run is unrecoverable. This is the worst-case data-integrity risk.
- **No backups.** Once a post is unsaved on the platform, if the CSV is lost, the data is gone permanently — the platform doesn't have an "undo unsave" endpoint.

**Data loss window:** up to the entire current CSV if `patchUnsaveConfirmed` crashes mid-rewrite at scale.

---

## 4.6 Performance & Bottleneck Analysis

Runtime is dominated by intentional anti-detection delays; the structural inefficiencies are a handful of O(n) full-file operations inside an O(n) outer loop.

### Timing (measured/estimated from code)

| Step | Duration |
|---|---|
| Per-post cycle | ~3-5s (dominated by randomised delays) |
| Dropdown open poll | up to 8s, typically <500ms |
| Clipboard confirmation poll | up to 5s, typically <500ms |
| Random delay before Copy click | 0.5-2s |
| Random delay before Unsave click | 0.5-2s |
| Random delay between posts | 1-2s |
| `verifyLastRow` | file-read O(rows x 200 bytes/row); at 1k rows ~= 200KB read -> <50ms |
| `patchUnsaveConfirmed` | file-read + full rewrite O(rows); at 1k rows ~= 2x 200KB -> <200ms |

**100 posts ~= 5-8 minutes. 1,000 posts ~= 50-80 minutes. 10,000 posts ~= 8-13 hours (requires keeping the tab focused the whole time).**

### Bottlenecks

1. **Randomised delays dominate (~90% of wallclock).** Intentional — this is the anti-detection budget. Cannot be compressed without risking account flags.
2. **`patchUnsaveConfirmed` reads+rewrites the full CSV per post.** At N posts total, this is O(N^2) total bytes written over the run. At 1k posts that's ~200MB of redundant disk writes. SSDs don't care; corporate MDM-managed laptops with disk encryption might.
3. **`verifyLastRow` reads full file per post.** Same O(N^2) pattern as above but read-only. Could be solved by seeking to `file.size - 512` and reading just the tail.
4. **Toast-detection full-page `querySelectorAll('div, span, p, li')`** up to 33x per post. At a typical feed page with ~3000 such elements, that's ~100k node scans per post. Cheap per-scan but cumulatively wasteful.

### Cost

- **Token cost**: 1.4-1.6k for minified (README claim). Per-run, one-off.
- **Compute**: the user's browser tab + their CPU. No cloud.
- **Opportunity cost**: user cannot use the browser tab for anything else while running.
- **Account risk**: non-zero. Randomised delays help but do not eliminate "this looks like automation" signals.

### Top 3 Optimisation Opportunities

1. Replace `verifyLastRow` full-file-read with `seek(file.size - 512)` tail-read -> O(1) per post instead of O(rows). Impact: ~50ms saved per post x 1000 posts = ~50s. Effort: 10 lines.
2. Replace `patchUnsaveConfirmed` in-place rewrite with append-only patch log (a second CSV that says `<post_id>,unsaved_at=<ts>`) or flip the semantics (write row AFTER unsave confirmed). Impact: eliminates the catastrophic-data-loss risk. Effort: moderate refactor.
3. Cache the toast-detection root (e.g. `document.querySelector('[role="alert"]')`) instead of re-scanning the whole document. Impact: reduces per-post overhead from ~100k nodes to ~10. Effort: 5 lines.

---

## 4.7 Code & Storage Efficiency

| Category | Finding |
|---|---|
| Empty files | None |
| Duplicate files | `exporter.annotated.js` (1,010 lines) and `exporter.min.js` (1 line) are functionally parallel — ~95% logic overlap. Acceptable because one is reference, one is distribution. BUT no build pipeline. |
| Dead files | `validated-script_v1.0.js` — 943 lines, 20,629 bytes, **syntactically invalid** (zero backticks, template literals all broken). See Critical Issue #1. |
| Build artifacts in repo | None |
| Binaries in repo | None |
| `.gitignore` coverage | **Missing .gitignore entirely.** At minimum should exclude: `*.csv`, `.env`, `node_modules/`, `.DS_Store`, `Thumbs.db`, `.vscode/` |
| Storage bloat | None relative to total repo size (~80KB). The waste is proportional, not absolute. |
| Dead dependencies | N/A — zero deps |
| Code duplication | ~95% logic duplication between annotated and min (intentional but unenforced). v1 has ~70% logic overlap with v2 but is broken so doesn't count. |
| Git history weight | 18 commits; 5 commits (28%) are `Create Prompt*` and 4 commits (22%) are `Delete Prompt*` — half the history is noise. |

**Totals:**
- Bytes of committed dead code: 20,629 (24% of tracked JS bytes).
- Bytes of committed non-functional dead code (won't even parse): 20,629 / 20,629 — the dead file is 100% broken.
- Lines of repo slated for deletion without functionality loss: 943 (48% of total JS LOC).

---

## 4.8 Agent Skill Standards Compliance

Not an agent skill — section skipped. Table retained for report-schema completeness:

| Skill Standards Check | Rating | Evidence |
|---|---|---|
| Spec conformance (SKILL.md) | N/A | Project is not an agent skill — no SKILL.md, no YAML frontmatter, no skill platform targeting |
| Description quality | N/A | Not applicable |
| Instruction quality | N/A | Not applicable |

---

## Phase 5: Security, Readiness & Recommendations

### 5.1 Security & Data Exposure

**A. Traditional Security**

- **Secrets in code**: None. Scanned all 4 tracked files for GitHub PATs, AWS keys, bearer tokens, private-key headers, Slack webhooks, generic `API_KEY=` patterns. All clean.
- **Secret in `.git/config`**: **[REDACTED] Personal Access Token embedded in remote URL** of the local clone. Not committed, but leaks via any `git remote -v` or `.git/config` exfiltration. Should be rotated and replaced with a credential helper. See Critical Issue #5.
- **Injection**: no `eval`, no dynamic `Function` constructor use, no `innerHTML` with user data. `log()` uses `textContent` — XSS-safe. CSV escape handles quote-injection.
- **Path traversal**: N/A — file path comes from user's native `showSaveFilePicker` dialog, not user-typed string.
- **Command injection**: N/A — no shell execution.
- **DOM injection of controls**: `injectUI()` writes literal strings via `textContent` and fixed `style.cssText` — no DOM-based XSS risk from the platform's page content.
- **Clipboard abuse**: reads clipboard only, after the platform's own "Copy link" button populates it. Does not write to clipboard. Acceptable.
- **File System Access API permissions**: user-granted per-file via picker. Each handle persists only for the tab lifetime. Correct use.
- **CORS / network**: script makes no `fetch` calls. Runs entirely in the platform's origin using DOM events.

**B. OWASP LLM Top 10** — N/A. No LLM, no prompts, no context window. (Note: the tool is *intended* to be pasted into an AI-browser as a shortcut; that's a hosting model not an LLM integration. The script itself does not call an LLM.)

**C. OWASP Agentic Top 10** — N/A. Not agentic. It's a deterministic loop.

**D. MCP Security** — N/A.

**E. GenAI Data Security** — partially applicable:

- **Data leakage**: CSV output contains post URLs, author names, profile URLs, date, content snippets. This is the user's own saved data — but the resulting CSV is **unencrypted plaintext** on disk. If the user syncs their Downloads folder to a third-party cloud storage provider, the file gets replicated to that cloud. No warning in the README.
- **Content snippets**: `snippet = innerText.slice(0, 150)` may contain other people's post content (the author's post body). This is scraped content — platform users did not consent to their posts being exported to a third party's disk in bulk. Privacy posture depends on downstream handling by the operator.
- **Log file PII**: the floating log panel and `console.log` both echo author names and post IDs. If DevTools is recorded or the tab is screen-shared, this leaks.

**F. AI Governance** — N/A.

**G. Red Teaming Readiness** — N/A.

**H. Platform / ToS Compliance** (material):

- **Platform Terms of Service**: the target platform's user agreement prohibits "automated bots, spiders, or data-scraping tools". Randomised delays reduce detection but do not change the underlying ToS posture. Running this against an account the user values carries **account-restriction risk**.
- **Unsaving at scale**: Legitimate user action, but performing it programmatically at high rate could trigger rate-limit / behavioural-anomaly detection on the platform's side.
- **Scraping legal posture**: US case law on scraping (e.g. CFAA / computer-misuse implications) is live and contested. For a personal tool used on one's own account only, practical risk is low. For wider distribution, the README should add a "use at your own risk / may violate platform ToS" disclaimer.
- **Selector-based bot-detection evasion**: `fireMouseEvents()` dispatches full `pointerdown -> mousedown -> pointerup -> mouseup -> click` event sequences. This is *specifically designed* to bypass event listeners that distinguish human from programmatic clicks. Ethically, this is automation-against-a-platform-that-detects-automation — grey area for personal use, problematic for sharing/commercialisation.

**Privacy-posture summary**: no third-party PII collection, but the tool exports a user's private "saved" collection (which may include other people's posts) to a plaintext local file with no encryption, retention policy, or secure-deletion guidance.

### 5.2 Logging & Observability

- **Runtime logs**: floating panel + `console.log`. Timestamped (local time). Auto-scrolls. Clean UX.
- **Structured?** No. Free text with Unicode check/warn markers. Unparseable for later analysis.
- **Persistence**: zero. When the tab closes, the panel log is gone. `console.log` persists only until DevTools is closed or the log buffer overflows.
- **CSV as audit trail**: every row records `processed_at`, `write_verified`, `unsave_confirmed`, `url_source`, `error_reason`, `run_id`. This is the ONLY persistent operational record. It's decent but missing: the stuck-loop-skipped posts (set `data-skip`, never written) and dropdown-timeout skips (same) leave **no trace** on disk.
- **Metrics**: none. No per-run count of posts processed, failures, duration.
- **Alerts**: none (correctly — it's a user-initiated foreground tool).

### 5.3 Documentation Quality

- **Accuracy**: README describes the current v2 script correctly. Setup steps are runnable as written. CSV schema matches the code header exactly.
- **Completeness**: good for scope. Missing: license, changelog, security note about ToS, privacy note about CSV being plaintext on disk, browser-compatibility note (Chromium only), mention of `validated-script_v1.0.js` (which is in the repo but undocumented — README implies only two files exist: `.min` and `.annotated`).
- **Drift**: the README says "Both files are functionally identical" about the annotated and min versions. This is enforced by author care, not CI.
- **Onboarding**: a technical user can be running this in under 5 minutes from the README. A non-technical user will stumble on "create an AI-browser shortcut" which isn't explained.
- **Maintenance posture**: README references the brittle selectors with a "When the platform changes their markup" section — good proactive maintenance UX.

### 5.4 Goal Fulfillment

**Stated objective** (README): "Browser automation script for an AI-browser that exports all saved posts to a CSV file and unsaves each one after processing."

**Actual behaviour**: exactly this. Caveats — not failures of the stated goal, but gaps vs implied scope:

- "All saved posts" depends on the "All" filter tab. If user has "Articles" tab active, only articles are processed.
- "Unsaves each one after processing" is conditional on successful DOM click registration. When `unsave_confirmed="false"`, the post was written but NOT unsaved. Resume handles this.
- Claim: "Exports to CSV" -> delivered. Claim: "for AI-browser" -> script works in any Chromium browser; the AI-browser framing is packaging, not a technical dependency.

**Verdict**: Goal 95% fulfilled. The 5% gap is silent-mode edge cases (localised platform accounts, Articles filter, Chromium-only) that aren't in the README.

### 5.5 Blind Spots

| Blind Spot | Risk |
|---|---|
| No rate-limit / CAPTCHA detection | If the platform returns a "you're moving too fast" interstitial, the DOM selectors find nothing and the script marks posts as `data-skip` — masking the underlying block. User sees "script done" when actually the platform cut them off. |
| No per-run summary | User has no "38/42 processed, 4 skipped" readout. Have to manually count CSV rows vs skipped `<li>`s. |
| No CSV backup | `patchUnsaveConfirmed` in-place rewrite is the catastrophic-corruption path. No `.csv.bak` or temp-file-rename. |
| No selector pre-flight | Script starts, fails 30 seconds in on an unexpected markup — user doesn't know until then. A 2-line pre-flight would fail fast. |
| No platform locale handling | Non-English `aria-label` strings silently fail. No fallback selectors. |
| No i18n of UI controls | Injected button labels are English. Fine for the target audience but notable. |
| Browser compatibility unmonitored | Firefox/Safari silently fail because `showSaveFilePicker` is undefined. User gets a random "window.showSaveFilePicker is not a function" stack trace with no guidance. |
| CSV file on disk is plaintext | Corporate users may have MDM/DLP policies that flag bulk export of URLs+names to CSV. No guidance. |
| Platform ToS posture | Not acknowledged in README. |

### 5.6 Objective Clarity Assessment

| Dimension | Rating (1-10) | Evidence |
|---|---|---|
| Objective clarity | 9 | One sentence in README, fully delivered |
| Goal fulfillment | 9 | Does exactly what it says with safety guarantees |
| Delivery reliability | 6 | Works on English-locale Chromium users; brittle to platform markup changes; no rate-limit detection |
| Output quality | 8 | Rich CSV schema with verification fields; full URL with query params preserved |
| Automation maturity | 5 | Manual launch, manual tab focus, manual file picker; user must supervise |
| Self-improvement | 1 | No learning from selector failures; no telemetry; no auto-detection of markup drift |
| Operational visibility | 5 | Runtime log panel good, but no persistent logs, no summary, no metrics |
| Resource efficiency | 7 | Zero deps, low token cost, intentional throttling. Minor inefficiencies in full-file reads. |
| Safety & data integrity | 7 | Write-verify-unsave is excellent; `patchUnsaveConfirmed` in-place rewrite is the weak link |

### 5.7 Overall Rating

**6.5/10** — A well-thought-through personal automation tool with one genuinely clever safety invariant (write -> verify -> unsave) and one genuinely embarrassing shipping defect (a 943-line file that doesn't parse). Cleanly written annotated version, honest README, zero dependencies. Loses points for: broken dead code file committed as "validated-script_v1.0", missing license/gitignore, zero tests on trivially-testable pure functions, no build pipeline enforcing annotated-vs-min parity, no backup/recovery for the catastrophic `patchUnsaveConfirmed` corruption path, and a local PAT exposed in `.git/config`.

### 5.8 Production Readiness Assessment

| Gate | Status | Evidence |
|---|---|---|
| **Functionality** — does it do what it promises? | PASS | Exports saved posts to CSV with write-verification and unsave. Delivers the README claim on English-locale Chromium. |
| **Reliability** — consistent without manual intervention? | PARTIAL | Requires manual launch + tab focus. Reliable once running on expected markup. Brittle to localisation, A/B tests, platform rate limits. |
| **Error handling** — recovers gracefully? | PARTIAL | Good per-failure handling (clipboard fail, dropdown timeout, unsave unconfirmed). Missing: escalating backoff, rate-limit detection, `patchUnsaveConfirmed` crash safety. |
| **Security** — no exposed secrets, injection risks, PII leaks? | PARTIAL | No secrets in tracked code. Local `.git/config` has embedded PAT [REDACTED]. CSV is plaintext third-party data. Platform ToS risk. |
| **Testing** — critical paths covered by tests? | FAIL | Zero tests. 5 trivially-testable pure functions uncovered. |
| **Monitoring** — can you tell when something breaks? | FAIL | No persistent logs, no summary, no metrics, no alerting. Silent partial failure is possible. |
| **Documentation** — can someone else operate this? | PASS | README is clear, runnable, and honest. Missing license/changelog/browser-compat note but core is good. |
| **Scalability** — handles growth without redesign? | PARTIAL | Linear for moderate N; O(n^2) bytes-written at large N via `patchUnsaveConfirmed`. Usable up to ~low-thousand posts. |
| **Data integrity** — consistent, backed up, recoverable? | PARTIAL | Append-only with write-verification is strong. `patchUnsaveConfirmed` truncate-then-rewrite is a data-loss time bomb. No backups. |
| **Dependency health** — maintained, pinned, CVE-free? | PASS | Zero external deps. Pure browser APIs. |
| **Codebase hygiene** — no dead code, no broken files? | FAIL | `validated-script_v1.0.js` is 943 lines of unparseable JS masquerading as a "validated" version. |
| **Licensing** — legally shareable? | FAIL | No LICENSE file. Default copyright = nobody has permission to use or redistribute. |

**Verdict: Needs 4 fixes before sharing widely** — (1) delete `validated-script_v1.0.js`, (2) add LICENSE (MIT recommended), (3) add `.gitignore` with `*.csv` and `.env`, (4) rotate the leaked PAT and remove it from the local `.git/config`.

### 5.9 Top 10 Ranked Recommendations

| # | Action | Impact | Effort | Who Implements |
|---|---|---|---|---|
| 1 | `git rm validated-script_v1.0.js` — broken syntax (zero backticks), 943 dead lines committed as "validated" release | Critical — actively misleading consumers who find it via search or filename | Low — one `git rm` | Human |
| 2 | Add `LICENSE` file (MIT recommended) to the repo root | Critical — without it, the repo is legally un-shareable | Low — one file | Human |
| 3 | Rotate the Personal Access Token currently embedded in `.git/config` remote URL; switch to credential helper or CLI auth | Critical — any accidental paste of `git remote -v` or share of the working directory exfiltrates the token | Low — ~5 minutes | Human |
| 4 | Add `.gitignore` excluding `*.csv`, `.env`, `node_modules/`, `.DS_Store`, `*.bak` | High — prevents accidental commit of exported personal data | Low — one file | Agent |
| 5 | Fix `patchUnsaveConfirmed` to write-new-then-rename instead of truncate-then-write, OR flip semantics to write row AFTER unsave is confirmed | High — eliminates the only catastrophic data-loss path in the script | Medium — ~30 lines | Agent |
| 6 | Add unit tests for `parsePostId`, `approxDate`, `csvEscape`, `isValidPostUrl`, `stripQueryParams` + CSV-line parser | Medium — catches URL / date / escape regressions without touching a browser | Medium — ~75 lines + package.json with node:test | Agent |
| 7 | Add a selector pre-flight at `mainLoop` start — validate `findPostList()`, dropdown selector, post-link selector all resolve; fail fast with a specific error if not | Medium — turns 30-second silent failure into 1-second clear error with the exact broken selector | Low — ~15 lines | Agent |
| 8 | Add end-of-run summary to the log panel: posts processed / written / unsaved / skipped / url_mismatch / duration | Medium — gives the user a clear "did it work" verdict | Low — ~15 lines | Agent |
| 9 | Add escalating backoff when 3+ consecutive posts produce `dropdown_timeout` — suggests platform rate-limit active; pause 60s and retry once; if still failing, stop with a clear "likely rate-limited" message | Medium — graceful degradation under rate-limiting; avoids burning through the saved list while blocked | Low — ~20 lines | Agent |
| 10 | Add a build script (`npm run build` using `terser` or similar) that generates `exporter.min.js` from the annotated version, plus a CI check comparing the committed min file to the regenerated one | Medium — eliminates drift risk between annotated (reference) and min (distribution) | Medium — ~50 lines + package.json + CI workflow | Agent + Human |

### 5.10 Value Assessment

| Dimension | Rating (1-5) | Evidence |
|---|---|---|
| Problem clarity | 5 | "I want to export my saved posts to a CSV and clean up my saved list." Universally recognisable for heavy platform users. |
| Audience definition | 3 | Implied (technical user with AI-browser access) but not stated. The AI-browser framing is narrow packaging — the script works in any Chromium. |
| Maturity vs. claims | 3 | Claims "validated v1.0" (via the broken file's name) alongside current v2 — the validation claim is not credible when the "validated" file doesn't parse. Core v2 is solid. |
| Measurable value | 4 | ~3-5s per post x N posts vs ~30-60s manual per post = 10x+ time saving. Real. |
| Differentiation | 3 | Alternatives: the platform's own "Download your data" (gives JSON of saved items but doesn't unsave). Other browser extensions exist but most are paid / bundle other features. This tool's unique angle: write-verify-unsave invariant is genuinely not common. |
| Adoption readiness | 3 | README is clear but AI-browser shortcut setup has extra friction. No one-click install. Chromium-only unstated. |

### 5.11 The Uncomfortable Question

This project's core value — the write-verify-unsave safety invariant — is good enough to be a 20-line pattern in a proper browser extension manifest. Instead it's packaged as a pasted-into-a-shortcut one-file monolith whose "distribution format" is a 1-line minified blob. The structural question is: if you trust this enough to let it unsave hundreds of posts you've curated over years, why not trust it enough to invest the half-day it would take to turn it into a proper browser extension with a popup UI, permissions declared up front, a proper update channel, and actual CI? The current shape is a scripted spike that's been lived-in long enough to accumulate a git history of "Create Prompt" / "Delete Prompt" noise — it's stuck between "hackathon artefact" and "tool". Pick one. And while you're at it, delete the 943-line broken file committed as "validated-script_v1.0" — that single file does more damage to the project's credibility than every other defect combined, because it shipped a lie (the word "validated") alongside code that doesn't even parse. That's not a bug, that's a positioning problem.

---

## Phase 6: Resilience Testing

**Backups:** None. Single CSV file is the sole output and the sole audit trail. The `patchUnsaveConfirmed` truncate-then-rewrite is the catastrophic-loss path — browser crash mid-rewrite yields an empty or partial file with no recovery. Because the platform has no "undo unsave" endpoint, the affected posts are permanently lost from the user's saved list.

**Recovery procedure:** Stated in README — Open CSV -> Start Processing. Hydrates dedup Set from the file; already-processed posts are skipped; unsave-only runs for already-written-but-not-unsaved entries. This is the intended recovery path for the common failure mode (tab close / stop / browser restart) and is **well-designed**. It works for every failure mode except the `patchUnsaveConfirmed` crash.

**Operational resilience:**
- Tab-focused script — cannot survive tab close without user intervention (Open CSV + Start).
- No daemon, no background worker, no cron equivalent.
- No multi-device (cross-browser / cross-machine) state — the CSV is the state, it lives where the user saved it.
- No migration path — changing filename or location breaks resume until user manually re-Opens.

**Resilience-testing verification:** restore testing not applicable (no backups to restore). Code-level failure-mode analysis completed in Section 4.5.

**Summary verdict:** The tool's resilience model is "the CSV is the truth + the user can re-open it" — which is robust against the common failure mode (tab close) but unprotected against its own worst case (`patchUnsaveConfirmed` corruption). Recommend fix #5 above to close this gap.

---

*Generated by [deep-project-audit](https://github.com/belousov-petr/deep-project-audit) v1.0.0*
