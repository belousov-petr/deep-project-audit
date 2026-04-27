# Baseline Review - 17-Agent Intelligence Pipeline

**Review date:** 2026-04-17
**Methodology:** bare "review this project" prompt - no skill methodology
**Reviewer:** Claude Opus 4.7

> **Note:** This is an anonymized baseline review - a bare "review this project" prompt with no skill methodology, used as a control to measure what the shakedown skill adds vs. unstructured Claude output. Platform names, organization names, and personal identifiers have been replaced with generic placeholders. The absence of structural sections (production readiness gates, value assessment, uncomfortable question, ranked recommendations table) is intentional - that's what the skill provides and this baseline deliberately lacks.

---

I spent an afternoon reading around this project. Below is what stuck out - what's broken, what to fix first, and roughly where the maturity sits.

## What this project is

A 17-agent Claude-based intelligence pipeline. A fleet of scouts (ten domain-specialized researchers) runs weekday mornings around 01:00 local time, each writing JSON signals to disk. A Scout Lead dedups and normalizes them, a Senior Analyst scores them, an Editor composes a daily output artifact, a Dispatcher sends it out via an external delivery provider, and a Pipeline Reviewer produces a weekly memo. There's also a pre-flight discovery routine at 00:30 that sweeps a `SOURCES.yaml` publisher list via RSS/HTML/search-API and seeds candidate queues before the scouts wake up.

The whole thing sits in one directory: embedded Postgres on port 54329, a local UI on `127.0.0.1:3100`, file-system signal storage, per-agent instructions under `companies/<uuid>/agents/<uuid>/instructions/{AGENTS,HEARTBEAT}.md`. The stated strategic deliverable is the *quarterly* aggregate artifact - daily output is accumulation + filtering, and the quarterly edition is the thing that actually ships to downstream consumers. The project charter frames this as a positioning instrument, not a newsletter. Worth reading if you're not already in the headspace.

Today's output artifact does look credible - it opens with a cross-publisher convergence top signal and pulls in multiple regulators, consulting firms, and cloud-vendor releases with a per-scout coverage footer. The synthesis is genuinely interesting. The pipeline is producing.

## What's actually working

- **Standards folder is strong.** `standards/FOCUS.md`, `QUALITY-STANDARD.md`, `SIGNAL-SCHEMA.md` (now v3.2 with a freshness block), `FRESHNESS.md`, `SOURCES.yaml` - this is a real editorial contract, not hand-waving. The ICD-203 tradecraft adaptation (sourcing transparency, fact-vs-assumption, calibrated confidence) is the kind of thing most LLM-pipeline projects skip entirely.
- **Topology is data-driven.** `pipeline-topology.json` maps role keys → agent UUIDs. Every `AGENTS.md` I opened has a "Pipeline Topology Resolution" section telling it to resolve role keys at runtime rather than hardcoding names. Adding / renaming a scout is a one-field edit, and you can see from the memory log that this actually got exercised (two renames and one new scout in the last week).
- **Graceful fallback in the fetcher stack.** `scripts/discover_candidates.py` (635 LOC) walks a `requests → cloudscraper → curl_cffi` ladder with a fast-fail detector for known bot-protection. `scripts/fetchers/email_wall.py` (478 LOC) falls through to the HTTP ladder when an optional credential isn't set instead of crashing. This is adult engineering.
- **Memory discipline.** `.claude/memory/MEMORY.md` is a proper index, not a dump. `project_state.md` has a session-by-session "WHERE WE LEFT OFF" log - resuming a session is actually cheap.
- **Backups are running.** `config.json` has 6-hour backup intervals with 30-day retention pointing at `data/backups/` (~689 MB on disk), and the OPS note mentions this was a fix from an earlier review.
- **Git exists.** Initialized in session 4; 6 commits so far. Not much, but the repo is real.

## What's broken

### 1. The project root is a bash-escape landfill

There are ~25 zero-byte garbage files in the instance root with names like `100`, `20%`, `300`, `5000`, `ERROR`, `Industry`, `Leadership`, `PNG`, `Three`, `URL`, `{en`, `{ended}`, `` ` ``, `4}`, `6}`, `,`, `C)`, `-platform-`. Recent timestamps. A prior review cleaned ~30 of these and they've regrown in two days. Something is shelling out with unquoted arguments and creating files named after tokens that Claude (or a Bash tool call) emitted - probably an `echo "30%" > ...` pattern or an unguarded `$VAR` expansion. This isn't just cosmetic: it means there's a harness bug quietly running, and at some volume it'll start colliding with real filenames.

Fix first: `find . -maxdepth 1 -type f -empty -delete` as a hygiene cron, but the real fix is to grep hook scripts and agent tool specs for unquoted `$` expansions and `echo` redirects with un-escaped content. Until the source is identified, the cleanup is treating a symptom.

### 2. Multi-day pipeline blackouts with no alerting

OPS.md flags a recent 4-day gap as a P0: scouts ran but the Scout Lead → Analyst → Editor chain didn't complete end-to-end. Looking at `output/daily/`, there's a 4-weekday hole (plus the expected weekend gaps). OPS says "root cause unknown, no alerting." That's still open.

There's a plan in memory (`project_watchdog_non_claude.md`) for a standalone Python watchdog that detects missing output artifacts without burning Claude tokens, but it's carried as an open item across sessions. Until it lands, the pipeline can blackout silently for days and nobody sees it until the maintainer opens the UI. That's the single biggest reliability gap.

Fix first: ship the watchdog before anything else. If `output/daily/<today>.md` doesn't exist by 03:00 local time on a weekday, fire a desktop notification or a cheap email. Don't route it through Claude - the whole point is that the watchdog works when the pipeline is broken.

### 3. Enrichment queue full, commit tree 5 sessions deep

`enrichment-queue/pending/` has 88 items. `done/` has 1. The Pipeline Reviewer flagged this a couple of days ago - scouts seeded items the pipeline had already processed, 60% dedup rate in the smoke sample, effective unique backlog ~35 - 40. A weekend-drain routine runs Saturdays at 01:00. If that fires cleanly the backlog will drop; if not, you've got dead work sitting around.

Separately: the uncommitted tree now stacks six sessions on top of the last commit. That's 40+ files of schema v3.2 work, a YouTube deep-read flow, an email-wall bypass, persistent-profile mode, and a `SOURCES.yaml` expansion - all of it live in the running system, none of it in git. Two problems with that: (a) if the repo dies you can't reconstruct what's running, and (b) a code review / rollback story is impossible. The memory log has a commit plan, but it keeps slipping because new work lands before the old work is committed.

Fix: force a commit day. Land the topical commits before starting the next session.

### 4. Doc-vs-runtime path drift

`SIGNAL-SCHEMA.md` says signals live at `signals/<today>/raw/<scout>/`. I looked - they live BOTH there and at a flat `signals/raw/` (54 files, no date bucketing). `signals/scored/` has 360 files, also flat. The runtime has diverged from the schema, and no one decided which is canonical. OPS flags this as a known P1 ("Pick one and normalize") - it's been open for days.

This matters because the Pipeline Reviewer is reading from both shapes and the freshness-filter work in `standards/` assumes one shape. Dedup and forensic investigation gets harder every day you leave it unresolved.

Fix: decide canonical (probably the nested date-bucketed form, since that's what the schema says and new routines write there). Write a one-off migration that moves flat → nested, verify, then delete the flat copies. Add a Pipeline Reviewer check that fails on either flat writes or missing date buckets.

### 5. Server log is 279 MB and growing, no date prefix

`logs/server.log` was 143 MB ten days ago, 253 MB a couple of days ago, 279 MB today. No rotation configured. Worse - the log lines are timestamped `[HH:MM:SS]` with no date. If something broke a week ago and you come back to find it, you literally can't tell when the error happened. A prior review flagged this as P1; it's still open.

Fix: add logrotate equivalent (weekly rotate, 4 weeks retention), change the log formatter to ISO-8601 with date. Both are ~15-minute changes.

### 6. No automated tests, no monitoring dashboard

There are no tests anywhere in the repo (I checked `scripts/` - just `__pycache__` and production code). The Pipeline Reviewer IS the monitoring system, but it's itself a Claude agent that runs weekly and produces a Saturday memo - useless for catching an intra-day regression. The reviewer is diagnostic, not alerting.

Fix: two layers. (a) Smoke tests on the Python code - the two fetcher scripts are 1,100 LOC with no coverage. Even three happy-path tests per file would have caught the "cached branch serves challenge-page HTML as article content" bug that shipped last session. (b) A simple HTML dashboard reading from Postgres + file timestamps - one-screen view of last scout run, last output artifact, queue depth, log size. Again, doesn't have to be fancy; a minimal web framework in an afternoon.

### 7. Heavy reference assets inside the runtime data dir

`skills/<id>/report-design/` is 316 MB (JPEGs + a PDF). `.gitignore` excludes it correctly, but it means the runtime instance directory is 1+ GB heavier than it needs to be, backups include it implicitly, and the PDF/PNG binaries are arguably design assets that belong in a separate repo. OPS has this as a P2 ("move to external design-assets folder"). Low urgency, but it's a smell.

### 8. One scout is silently missing and nobody escalates

Today's output footer: "Security Scout: missing (no status file)." Coverage was 6 of 10 scouts contributing. Some scouts go quiet on days with genuinely no newsworthy items, which is correct - but "missing (no status file)" is a failure mode distinct from "quiet," and the pipeline is logging it but not escalating it. If Security Scout has been missing for N consecutive days the reviewer should notice. Worth a grep in the reviewer's HEARTBEAT to see whether this rolls up into the weekly memo.

### 9. Secrets hygiene - an exposed search-API key in chat history

Session 25 notes say a `BRAVE_SEARCH_API_KEY` was pasted in chat for a smoke test. Session 28 notes memory-rule "never persist API keys in memory files" - good discipline - but the key from session 25 needs to be rotated as noted. I'd check that this actually happened. Also: `secrets/master.key` is 44 bytes, sitting in `secrets/` with the encrypted-local provider - fine in principle, but the whole `secrets/` dir is git-ignored and there's no apparent key-rotation story. If this laptop dies, everything encrypted under that key is toast unless it's backed up separately.

### 10. The "17 agents" count needs reconciling

`pipeline-topology.json` lists 10 scouts + collector + scorer + composer + dispatcher + reviewer = 15 roles. OPS.md's agent ID table lists 16. `ls agents/` shows 17 directories. Somewhere between the topology file, OPS.md, and the directory listing there's a CEO + Report Designer that aren't in topology but are in OPS. A prior review cleaned up an orphaned duplicate. I'd re-reconcile: every UUID on disk should either be in `pipeline-topology.json` OR explicitly documented in OPS as "floating role" (like the CEO, apparently). Otherwise there's no way to catch a future orphan spawn.

## How mature is this?

Honestly? It's further along than most "run-agents-on-a-cron" projects I've seen. The standards are real, the topology is factored, the memory discipline is unusual for a solo project. The output (today's artifact) is readable and has genuine synthesis beyond keyword aggregation.

But it's **production-adjacent, not production**. Here's what's missing if this has to survive past the next hard deadline:

- **No alerting.** The recent 4-day blackout is the canary. Until the watchdog ships, "did the pipeline run today?" is answered by the maintainer checking manually.
- **No tests.** 1,100 LOC of fetcher code is one bad refactor away from silently serving interstitials as article content (which has already happened once).
- **Uncommitted changes.** Git history doesn't reflect what's running. If the laptop dies, six sessions of work evaporate.
- **Single point of failure.** One person, one laptop, one provider subscription. The charter's "named backup editor" open item is open for good reason.
- **No measurement of the strategic deliverable.** Daily artifacts are produced, but the charter itself admits there's no measurement of whether they're being consumed or whether the positioning goal is actually being achieved. That's not a technical review finding, but it's the thing that matters - the pipeline could be perfect and still fail the real goal.

Call it **6.5 / 10 as a technical system, 5 / 10 as a product that ships independently of the maintainer**.

## If you only do three things

1. **Ship the non-Claude watchdog.** Nothing else matters if the pipeline can blackout silently. Memory already has the plan; it's been carried across sessions. This is overdue.
2. **Commit the 6-session tree.** Schema → freshness → youtube → email-wall → profile → sources. One day of work. Git should reflect what's running.
3. **Delete the garbage files AND find the source.** One-line cron to clean them, one afternoon to grep hook scripts for unquoted bash expansions. Don't just clean; fix.

Then: decide the flat-vs-nested signal layout, rotate the server log, add date prefixes, ship smoke tests on the two fetcher scripts, and reconcile the 15-vs-16-vs-17 agent count.

The output artifact itself is good. The plumbing is held together by the maintainer's attention. Move some of that load off them before the next deadline.
