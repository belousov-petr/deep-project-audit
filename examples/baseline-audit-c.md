# Project Audit — Browser Automation CSV Exporter

This is a browser automation script (~1,000 lines across 3 JS files) that exports saved posts from a social media platform into a CSV. It runs inside Claude in Chrome, injects a floating control panel into the page, iterates through saved posts, extracts metadata, cross-validates URLs via clipboard, writes verified CSV rows, and unsaves posts only after confirming the write succeeded.

Overall impression: surprisingly well-engineered for a personal browser script. The safety logic is genuinely good. But there are some clear things to clean up.

---

## What works well

The safety-first unsave flow is the standout feature. The script never unsaves a post without first writing it to CSV and then reading the file back to verify the row landed. That write-then-verify pattern means you cannot lose data under normal operation. Even if the browser crashes mid-run, at most one post is in an ambiguous state -- everything before it has been verified on disk.

The dual URL validation is a nice touch. URLs are pulled from both the DOM and the clipboard (via the platform's "Copy link" feature), and if they disagree, the mismatch gets logged. Most scripts would just grab the href and move on.

Stuck-loop detection prevents the script from spinning forever if an unsave silently fails. If the same post stays at position 0 for 3 consecutive iterations, it gets flagged and skipped. Simple, effective.

Resume works well. Opening an existing CSV loads all post IDs into a Set, so already-exported posts get unsaved without re-writing. You can stop and restart without duplicating data.

The randomized delays (0.5-2s between actions) are the right call for a tool that automates a platform that actively detects bots.

---

## What is broken or needs fixing

**1. Dead code in the repo.** `validated-script_v1.0.js` is the old v1 script, completely superseded by the v2 files. It is 944 lines of code that does nothing except confuse anyone who clones the repo. Delete it.

**2. No .gitignore.** This means CSV files with personal data (post URLs, author names, content snippets) could easily get committed by accident. Also no protection against committing OS junk files. Add a .gitignore that excludes *.csv, .DS_Store, node_modules, etc.

**3. No license.** If anyone else wants to use or contribute to this, they legally cannot without a license. Even for a personal tool, adding MIT takes 30 seconds and removes ambiguity.

**4. The CSV parser in the Open handler is hand-rolled and fragile.** It handles quoted fields with commas, which covers the happy path. But it will break on newlines inside quoted fields, BOM characters from Excel, or other edge cases. Since the script writes its own CSV and reads it back, this is low-risk in practice -- until someone opens the CSV in Excel, edits it, saves it, and tries to resume. Then it breaks.

**5. `verifyLastRow()` reads the entire file every time.** After writing each post, the verification step reads the whole CSV from the top to check the last line. At 100 posts this is invisible. At 5,000+ posts the file reads start adding real latency on top of the intentional delays. Reading just the last ~1KB of the file would fix this.

**6. No tests at all.** There are several pure functions -- `parsePostId()`, `approxDate()`, `csvEscape()`, `isValidLinkedInPostUrl()` -- that are easy to unit test and whose correctness matters. A URL parser that silently returns null on a valid URL means a post gets skipped and stays saved. These are the functions most worth testing.

**7. Brittle to DOM changes.** Every selector in the script is hardcoded against the platform's current markup. When the platform updates its HTML (and it will), the script breaks completely. The README documents this and provides guidance on updating selectors, which is the right mitigation for a personal tool. But there is no pre-flight check that verifies selectors are still valid before starting the main loop. Adding a quick validation pass at startup would fail fast with a clear message instead of failing confusingly mid-run.

**8. No rate-limit detection or backoff.** If the platform starts throttling or serving CAPTCHAs, the script just keeps trying and failing. Each failed post gets skipped after timeout, but there is no logic to slow down or stop when multiple consecutive failures suggest a systemic problem. Adding escalating backoff (double the delay after each consecutive failure, reset on success) would handle this gracefully.

**9. Messy git history.** There are 4 deleted "Prompt" files visible in git history -- created and removed in separate commits. Not harmful, but makes the repo look unfinished. A history cleanup or squash would tidy this up.

---

## What to fix first

In priority order:

1. **Delete `validated-script_v1.0.js`** -- immediate confusion reducer, 30 seconds of work.
2. **Add `.gitignore`** -- prevents accidental data leaks (CSV files contain personal data).
3. **Add a LICENSE file** -- MIT, takes one minute, unblocks anyone who wants to use this.
4. **Add a selector pre-flight check** -- validate that key DOM selectors resolve before starting the loop. Maybe 15 lines of code. Saves debugging time when selectors inevitably break.
5. **Add unit tests for pure functions** -- `parsePostId`, `csvEscape`, `approxDate`, URL validation. These are the functions where a silent bug causes data loss.
6. **Add escalating backoff on consecutive failures** -- graceful degradation instead of burning through timeouts.
7. **Optimize `verifyLastRow`** -- read last 1KB instead of entire file. Only matters at scale but easy fix.

Everything else (CSV parser hardening, run summaries, persistent logging) is nice-to-have but not urgent for a personal tool that works today.

---

## The bigger picture question

This tool's entire existence depends on DOM selectors that a third party controls and has no interest in keeping stable. Every platform redesign -- even a minor CSS refactor -- can break every selector at once. The README acknowledges this and documents how to update selectors, which is pragmatic. But the fundamental fragility remains: this is an injected script fighting against a platform that actively discourages automation.

For a personal tool run occasionally, that is fine -- you fix the selectors when they break and move on. If this were meant for wider use, the right answer would be a proper browser extension with MutationObserver-based DOM detection instead of hardcoded selectors. But for what it is, the current approach is the right trade-off.

---

**Bottom line:** 7/10. Well-engineered safety logic, clean code structure, good README. Loses points for dead code, missing project hygiene files (.gitignore, license), zero tests, and inherent DOM fragility. The safety-first design (never unsave without verified CSV) is genuinely better than most browser automation scripts I have seen. Fix the hygiene issues first, add basic tests, and this is a solid personal tool.
