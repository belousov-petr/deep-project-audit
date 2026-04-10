# Project Audit -- AI News Intelligence Pipeline

This is a working audit of a daily AI news intelligence pipeline built on Paperclip. The pipeline has been operational for roughly 11 days, producing 8 daily briefs from 333 scored signals across 16 agents. Here is what is broken, what is fragile, and what to fix first.


## The biggest risk: nobody reads the output

Before touching anything technical, the hardest question is whether these daily briefs have a consumer. Eight briefs have been produced. There is no evidence of readership, no click tracking, no feedback loop, no "reply to this email" mechanism. A pipeline that produces intelligence nobody acts on is a cost center with zero return. This should be resolved before investing further engineering time. Even a simple "did you open this?" pixel in the email would answer the question.


## Security: DB credentials in plaintext

OPS.md contains database credentials in cleartext. This is the single most urgent fix because it is the easiest to exploit and the easiest to remediate. Move credentials to environment variables or a secrets manager. If OPS.md is committed to any repository, rotate those credentials immediately after moving them.


## Reliability: the 9-hour hung run

The incident where a scout hung for 9 hours on an external site exposed the core fragility -- agents had no timeouts. Timeouts have since been added (20-30 min per agent), which is good. But timeouts alone are not sufficient:

- There is no circuit breaker. If a source is consistently slow or down, the scout will burn its full timeout every single run before failing. A circuit breaker that skips known-bad sources for N runs after repeated failures would save significant time and cost.
- There is no alerting. The 9-hour run was presumably discovered manually. A simple check -- "if the pipeline has been running longer than 90 minutes, send a notification" -- would catch this instantly.
- There is no run-level timeout. Individual agent timeouts of 30 min across 15 agents could theoretically allow a 7.5-hour sequential run. A global pipeline timeout (say 2 hours) that kills the entire run and alerts would provide a hard ceiling.


## Operational hygiene

**Server log at 170MB unrotated.** This will eventually fill the disk. Set up logrotate with weekly rotation, compress old logs, keep 4 weeks. Ten minutes of work that prevents a future outage.

**Backup storage at 173MB with no pruning.** 15 backup files with no retention policy. Implement a simple "keep last 7 daily + last 4 weekly" rotation. Without it, storage grows linearly forever.

**Duplicate Pipeline Auditor agent.** Two instances of the same agent means ambiguity about which one is authoritative and wasted resources. Delete the duplicate.


## Documentation drift

PROJECT-MEMORY.md says 12 agents; the actual count is 16. This is the kind of drift that makes documentation actively harmful -- someone trusting it will make wrong assumptions. Either keep it current (add it to a post-deployment checklist) or delete it. Stale docs are worse than no docs.

The VPS migration guide is 80% complete but untested. An untested migration guide is a liability -- it gives false confidence. Either finish and test it (ideally with a dry run to a staging VPS) or mark it clearly as DRAFT/UNTESTED so nobody relies on it during an emergency migration.


## Testing: zero automated tests

There are no automated tests of any kind. For a pipeline that runs unattended at 01:00 CET, this is a significant gap. You do not need full coverage -- start with:

1. **Smoke test for the critical path**: Can each agent start, receive a signal, and produce output? Mock the external sources, verify the JSON schema of the output.
2. **Integration test for the pipeline sequence**: Does scout output flow correctly to the lead, then to the analyst, then to the editor? Use a single known-good signal and trace it through.
3. **Schema validation**: The ~470 signal JSON files presumably have a schema. Validate that no agent produces malformed output.

This does not need a testing framework. A Python script that runs the pipeline with mocked inputs and checks outputs would be a meaningful first step.


## Signal storage sprawl

470 signal JSON files with no apparent archival or compaction strategy. At the current rate (~30-40 signals/day), this will reach thousands within months. Consider:

- Archiving signals older than 30 days to a compressed bundle
- Or migrating all signal storage to PostgreSQL (you already have it) and dropping the file-based approach entirely


## What to fix first (priority order)

1. **Rotate DB credentials out of OPS.md** -- 30 minutes, eliminates a real security exposure
2. **Set up logrotate** -- 10 minutes, prevents disk-full outage
3. **Add pipeline-level alerting** -- notification if run exceeds 90 min or fails entirely
4. **Delete the duplicate Pipeline Auditor** -- 5 minutes, removes ambiguity
5. **Add backup pruning** -- simple cron job, prevents storage creep
6. **Update PROJECT-MEMORY.md** -- 15 minutes, or delete it if nobody maintains it
7. **Answer the readership question** -- add open tracking to the email brief
8. **Write one smoke test** -- even a single end-to-end test with mocked sources is better than zero
9. **Add circuit breakers to scouts** -- skip sources that failed in the last N runs
10. **Finish or clearly label the VPS migration guide**

Items 1-5 are afternoon work. Items 6-10 are a weekend project. None of them require architectural changes. The pipeline fundamentally works -- it just needs the operational hardening that turns a prototype into something you can trust to run unattended.
