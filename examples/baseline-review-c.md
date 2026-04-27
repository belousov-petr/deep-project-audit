# Baseline Review - Browser Automation CSV Exporter

**Review date:** 2026-04-17
**Methodology:** bare "review this project" prompt - no skill methodology
**Reviewer:** Claude Opus 4.7

> **Note:** This is an anonymized baseline review - a bare "review this project" prompt with no skill methodology, used as a control to measure what the shakedown skill adds vs. unstructured Claude output. Platform names, account names, and personal identifiers have been replaced with generic placeholders. The absence of structural sections (production readiness gates, value assessment, uncomfortable question, ranked recommendations table) is intentional - that's what the skill provides and this baseline deliberately lacks.

---

Read the whole project: README, annotated JS (~1000 lines), validated-script_v1.0.js (~940 lines), minified JS (1 line).

## Overall take

Small, single-purpose browser automation tool. Runs inside a Claude-in-browser context as an injected script on the target platform's "saved posts" page. Iterates saved posts, pulls metadata from the DOM, cross-checks the post URL against the clipboard, writes a verified CSV row via the File System Access API, then unsaves the post only after confirming the CSV write landed on disk.

The design is actually careful - the "never unsave without a verified CSV row" invariant is the right way to structure this, and the two-pass dedup (DOM postId first, resolved postId second) is thoughtful. The stuck-loop detection, data-skip guard, and idempotent resume via Open CSV all show that whoever wrote this thought about what happens when the target platform's UI flakes out, not just the happy path.

That said, this is a "personal script" level of maturity, not production code. Some issues below are real bugs. Others are just things that would bite anyone trying to run or maintain it.

---

## The big one: `validated-script_v1.0.js` is broken

This file will not run. It has stripped backticks off every template literal throughout the file. Examples:

- Line 31: `line.textContent = [${new Date().toLocaleTimeString()}] ${msg};` - missing both backticks. `SyntaxError` at parse time.
- Line 39: `console.log[CSV] ${msg});` - same deal, plus an extra `)`.
- Line 135: `return "${val}";` - string literal that looks like interpolation but isn't.
- Line 235: `const needle = "false","${runId}";` - this is especially bad because even if you fixed the backticks the semantics are wrong (it's parsing as the comma operator).
- Lines 365 - 367, 477, 479, 481, 483, 503, 585, 637, 689, 695, 859, 895, 903, 911 - all template literals missing backticks.

Either this file was produced by pasting from a source where Markdown stripped the backticks, or it was edited by something that mangled them. Either way, it's dead. If anyone tries to use it they will see `Uncaught SyntaxError` immediately.

**Fix first.** Either delete this file or regenerate it from the annotated version. The README doesn't even mention it, so it's probably a leftover - but it's a trap for anyone browsing the repo.

## Annotated and minified versions look fine

The annotated version (`[exporter].annotated.js`) parses cleanly - backticks are all present. Same for the minified version. The two are functionally equivalent per README, and spot-checking the logic confirms that (same helpers, same flow, same selectors).

So the actual working product is the two good files. The v1.0 file is the outlier.

## Functional issues I'd worry about

### 1. `approxDate()` has a latent bug for `mo`

```js
const unit = relative.replace(/\d+/, ''); // for "3mo" → "mo"
const key = (unit.startsWith('m') && unit.includes('o')) ? 'mo' : unit;
```

This works. But the regex that produces `relative` in the main loop is:

```js
const relMatch = innerText.match(/\b(\d+[hdwmy]o?)\b/);
```

That regex accepts `2m` as valid (month without the `o`), but `approxDate` won't resolve `m` alone because `ms` has `mo` not `m`. So if the target platform ever shortens "3mo" to "3m" the `approx_post_date` silently becomes empty string. Minor but silent. Would be worth either restricting the regex to `[hdwy]|mo` or adding an `m: 2592000000` fallback in `ms`.

Also: `y` is literally any hour/day/week/month/year suffix - no sanity check. If the platform shows "just now" or a localized string the regex just silently misses it and `postDateRelative` is empty. Not breaking, just quietly lossy.

### 2. Content snippet extraction is fragile

```js
let snippet = innerText
  .replace(authorName, '') // remove author name
  .replace(postDateRelative, '') // remove "2d" etc.
```

`.replace()` without a regex only removes the first occurrence. If the author name appears in the post body (common - "quoting [Author Name]…"), only the first hit gets stripped and the snippet includes the author. If the author name is empty string (which happens - the aria-label strip can yield `''` for certain posts) you'll match on `innerText.replace('', '')` which is a no-op. OK but brittle.

Worse: there's no guard on accidentally matching something inside the post. If an author's first name is a common word that appears in the body, you nuke that occurrence too. Small thing but the snippet is user-facing data.

### 3. The clipboard read is racy

```js
await poll(() => { /* look for toast */ }, 5000, 150);
await sleep(300); // extra buffer
clipboardUrl = (await navigator.clipboard.readText()).trim();
```

The toast element detection uses a general `div, span, p, li` scan for the text "Link copied to clipboard". That's going to false-positive on any stray element containing that substring (e.g., a comment text, a translation, a past toast that hasn't unmounted). If it matches stale content, the script reads the clipboard before it's updated.

More importantly, `navigator.clipboard.readText()` requires the page to be focused. If the user tab-switches or the browser loses focus mid-run, this throws a permission error. The script catches it and continues with DOM URL only, which is fine - but users won't know why `url_source=dom` started appearing.

### 4. `patchUnsaveConfirmed` has a fragile needle

```js
const needle = `"false","${runId}"`;
const idx = text.lastIndexOf(needle);
```

It searches for `"false","run_..."`. That's `unsave_confirmed`=false then `run_id`. The safety check is then "does the chunk around `idx` contain the `postId`". That's reasonable, but: if the CSV row has anything after `unsave_confirmed` that also ends in `"false"` and is followed by another `"run_..."` pattern, you'd hit it. Since `run_id` is the 12th column and `error_reason` (the 13th) is last and usually empty, it's unlikely to collide in practice. But if `error_reason` ever contained `"false"` somehow, you'd be in trouble.

Also the patch rewrites the entire file by reading → mutating in memory → `createWritable()` (truncates) → write. For a file with thousands of rows this is O(n) per patch, and you patch once per post. It gets progressively slower as the CSV grows. Not catastrophic, but if you have 5,000 saved posts you end up reading and rewriting the whole CSV for each one - millions of bytes of churn. For a script that's already slow (500 - 2000ms random delays, 3s scroll waits) it's a minor fraction, but worth noting.

### 5. No concurrent-write protection

Global `window._csvFileHandle` is accessed across async boundaries. If the user double-clicks Start, or if the user clicks Stop then Start again during the same animation frame, you could get two `mainLoop()` running concurrently. There's no re-entrancy guard beyond `window._isRunning`. The main loop checks the flag *between* iterations, not before the `appendRow` stream work.

Unlikely in practice, but a user-visible race.

### 6. Dedup Set isn't persisted mid-run

If the browser tab crashes mid-run, the in-memory `window._dedup` Set is gone. Resume relies on re-reading the CSV, which is fine - but it means any row written with `write_verified=true` but no corresponding CSV flush (File System Access API buffering? - unlikely because each write closes the stream, but) could lead to duplicate processing. Again unlikely but possible.

### 7. "Stuck loop" threshold is arbitrary

3 consecutive iterations with the same postId at position 0 → mark `data-skip`. Fine. But `stuckCount` only resets when `postId !== lastFirstPostId`, and the reset also happens on the stuck-trigger branch. If the platform has a transient hiccup where the same post appears at position 0 three times in a row for legitimate reasons (slow unsave animation + retries), you can lose data (post stays saved, never gets unsaved). Would be safer to reset `stuckCount` on any successful CSV write, not on position change.

### 8. The `random` delay is `Math.random()` not cryptographic

Fine for human-like timing. Just noting that the target platform's bot detection is (presumably) more sophisticated than a `Math.random()` delay can fool. If the platform is actually running ML on session telemetry, the delays buy you time but not safety. The script also doesn't vary scroll speed, cursor movement, or dwell time - just click timing. A motivated bot-detection system would catch this. For personal-scale use (a few hundred saved posts) it's probably fine.

## Security and privacy

- Clipboard read is the only sensitive capability. Browser prompts for it. Fine.
- File System Access API - user picks the file, explicit consent. Fine.
- No telemetry, no external fetches. All processing is local to the tab. Clean.
- No secrets in the repo source files.

## What's missing

- **No tests.** Not even a smoke test for `parsePostId`, `approxDate`, `csvEscape`. These are pure functions that could trivially have unit tests and the bugs in `approxDate` would be caught.
- **No selector fallback strategy.** README says "if the platform changes markup, update these selectors." Fair, but the script just dies with "Post list not found" when that happens. A list of alternate selectors to try would buy resilience.
- **No rate-limit backoff.** If the platform starts returning errors or showing a rate-limit banner, the script doesn't notice. It just keeps clicking and either times out on dropdown polls or silently produces no-op iterations.
- **No CSV schema version.** If you add a column later, resume on an old CSV will misalign. The dedup parsing grabs `cols[0]` (post_id), `cols[9]` (write_verified), `cols[10]` (unsave_confirmed). Change the order and resume silently breaks. A schema_version column would future-proof this.
- **No CHANGELOG.** The `validated-script_v1.0.js` filename suggests there's been iteration, but there's no history of what changed when. The annotated file references "v2" changes in comments, but which file is v2?
- **Package metadata missing.** No `package.json`, no LICENSE, no `.gitignore`. If you're going to put this on a public host, these matter.

## Maturity assessment

This is a **competent personal script**, maybe 5-6 out of 10 on a production-readiness scale.

What it does well:
- Thoughtful failure semantics (verify write before destructive action)
- Good documentation (README + annotated version)
- Careful about bot detection heuristics
- Idempotent resume
- Token-efficient (minified + annotated split is clever for the Claude-in-browser context)

What holds it back from being shippable:
- Broken `validated-script_v1.0.js` file in the repo root
- No tests
- Several quiet-failure modes (snippet extraction, approxDate for `m` vs `mo`, toast false-positive)
- No resilience when the platform changes selectors - just dies
- No license, no contribution guide, no CI

## What to fix first (prioritized)

1. **Delete or regenerate `validated-script_v1.0.js`.** It's broken and it's not linked from the README. Currently it's a booby trap for anyone who finds it first.
2. **Add unit tests for pure helpers** - `parsePostId`, `approxDate`, `csvEscape`, `stripQueryParams`, `isValidPostUrl`. 10 minutes of work, catches regressions forever.
3. **Fix `approxDate` so `m` without `o` falls through to `mo`** (or restrict the regex to require `mo`). Trivial.
4. **Make the snippet extraction use word boundaries or a regex** so substring matches don't corrupt content.
5. **Add a LICENSE file.**
6. **Version the CSV schema** (first column or header comment) so future column changes don't break resume.
7. **Consider selector fallbacks** - at least warn "found via fallback selector" vs. dying silently.

Anything below here is polish.

## Verdict

If this is a personal utility you run once on your own saved posts, it's good enough - just delete the broken v1 file. If you're thinking of sharing it with others, there's 2 - 4 hours of cleanup before it's safe to publish.
