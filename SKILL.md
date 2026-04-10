---
name: deep-project-audit
description: "Full-stack audit of any project — multi-agent systems, pipelines, codebases, or applications. Dynamically discovers project structure, reads all config/code/data, queries databases, tests backup integrity, and analyzes architecture, reliability, efficiency, and security. Produces ranked actionable recommendations. Use when asked to audit, analyze, review, stress-test, or challenge any project, or when user asks 'how solid is this project', 'what is missing', or 'find the weak spots'."
license: CC-BY-4.0
compatibility: "Requires Claude Code or similar agent with file-read, shell execution, and parallel subagent capabilities"
metadata:
  author: belousov-petr
  version: "1.0.0"
---

# Deep Project Audit

Comprehensive analysis of any project. Discovers the structure dynamically,
reads everything, challenges every layer, finds bottlenecks, blind spots,
and waste, then produces ranked recommendations you can implement in the
same session.

Works on: multi-agent platforms (Paperclip, CrewAI, AutoGen), data
pipelines, web applications, CLI tools, monorepos, microservices —
any project with files to read and architecture to challenge.

---

## Phase 1: Discover Project Structure

Before reading anything, map the project. Do NOT assume folder names,
frameworks, or conventions — discover them.

### 1a. Identify What Kind of Project This Is

List files in the working directory and its immediate subdirectories to
understand the project layout. Use your platform's tools (Glob, LS, or
shell commands) to discover:

```bash
# Example commands (adapt to your platform):
ls -la
find . -maxdepth 2 -type f | head -50
```

Check for framework indicators by looking for common config files:
`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Makefile`,
`docker-compose.yml`, `.env`, `*.config.*`

Check for agent/pipeline platforms by looking for platform-specific
directories (`.paperclip`, `.crew`, `.autogen`, `.langchain`, etc.)

Check for running databases by listing active network listeners on
common database ports (5432, 3306, 27017, 6379).

From this, determine:
- **Project type**: multi-agent system, web app, data pipeline, CLI tool, library, etc.
- **Tech stack**: languages, frameworks, platforms
- **Data stores**: databases, file-based storage, caches
- **External dependencies**: APIs, services, scheduled jobs

### 1b. Map the Full Directory Tree

List all directories up to 4 levels deep to understand the project
structure. Then find all config, code, and documentation files by
searching for common extensions: `.md`, `.json`, `.yaml`, `.yml`,
`.py`, `.js`, `.ts`, `.toml`, `.env`, `.sh`

```bash
# Example:
find {projectRoot} -maxdepth 4 -type d | head -100
```

Identify all:
- **Config files**: how is the system configured?
- **Instruction/prompt files**: agent instructions, system prompts, templates
- **Code files**: source, scripts, utilities
- **Output directories**: where does the system write its results?
- **Data directories**: storage, pipelines, caches, logs
- **Documentation**: READMEs, design docs, ADRs, runbooks

### 1c. Check Git History

Review recent git history to assess project health:

```bash
git log --oneline -20                    # recent commits
git log --oneline --since="30 days ago" | wc -l  # activity level
git shortlog -sn --since="6 months ago" # contributors
git branch -a                           # branch hygiene
git stash list                          # abandoned work?
```

Determine:
- Is the project actively developed or stalled?
- Single developer or team?
- Are commits atomic and well-described, or sprawling "fix stuff" patches?
- Any long-lived branches that suggest unfinished features?

### 1d. Read the Project's Stated Goal

Look for and read (if they exist):
- README.md — what does the project claim to do?
- PRD, spec, or design doc — what was the intended scope?
- CLAUDE.md / AGENTS.md — project-level instructions
- package.json description, pyproject.toml metadata

Capture the **stated objective** in one sentence. This becomes the
benchmark for section 5.4 (does the system actually achieve its goal?).

### 1e. Confirm Scope with User

**Before proceeding to Phase 2**, present a brief summary:

```
Discovered: {project type} with {N} components/agents
  - {tech stack}
  - {data stores}
  - {file count} files across {dir count} directories
  - Stated goal: "{one sentence}"

Scope: audit everything above. Proceed?
```

Wait for user confirmation. This prevents wasting tokens auditing the
wrong project, wrong subdirectory, or wrong scope.

**If user declines scope**: ask what to narrow to or exclude. Do not
abort — adjust the scope and re-confirm.

---

## Phase 2: Full Content Read (Parallel)

Dispatch **4 parallel agents**, each reading one slice of the project.
Adapt the slices to whatever Phase 1 discovered.

**If project has >1000 files**: sample instead of reading everything.
Read representative files from each directory (2-3 per folder), count
the rest, and note which areas were sampled vs fully read.

**If a parallel agent fails**: continue with the remaining agents.
Note the gap in the final report and flag what was not covered.

### Agent 1: Architecture & Configuration
Read all configuration and architectural files:
- Config files (JSON, YAML, TOML, .env — note secrets, don't expose values)
- Agent/worker definitions (instruction files, prompt templates, role definitions)
- Pipeline/workflow definitions
- Infrastructure config (Docker, CI/CD, deployment)

### Agent 2: Execution Logic & Coordination
Read all files that define HOW the system runs:
- Heartbeats, schedulers, cron definitions, event handlers
- Coordination mechanisms (handoffs, queues, barriers, locks)
- Error handling, retry logic, fallback paths
- Entry points, main loops, orchestrators

### Agent 3: Outputs, Docs & Reviews
Read all output and documentation:
- Recent outputs (latest 3-5 of each type)
- Documentation (design docs, runbooks, ADRs, project memory)
- Review/audit files if they exist
- Scripts (build, deploy, report generation)

### Agent 4: Data, Infrastructure & Supporting Files
Explore and quantify (count, don't read every file):
- All data directories — count files, read 2-3 samples to understand schema
- Logs — check latest entries for errors, check if structured (JSON) or unstructured
- Backups — list, check sizes and dates
- Skills/plugins/extensions — read definitions
- Memory/state files — understand persistence model

---

## Phase 3: Data Store Diagnostics

If the project has a database (SQL, NoSQL, or embedded), run diagnostics.

**If no database found**: skip this phase. Note "No data store detected"
in the report and proceed to Phase 4.

**If database found but credentials unavailable**: skip queries. Note
"Database detected but could not access — manual credential needed" and
proceed to Phase 4.

See [DB Diagnostics](references/db-diagnostics.md) for database-specific
queries and inspection guidance.

---

## Phase 4: Quality Analysis

Synthesize everything from Phases 1-3.

### 4.1 What the Project Is
One paragraph: purpose, who it serves, architecture summary, tech stack.
Derived from what you read, not assumed.

### 4.2 What Works Well
Genuine strengths with evidence. Be specific — cite files, patterns,
design decisions that are genuinely good.

### 4.3 Critical Issues
Things that will cause failures soon. Must include evidence:
- Reliability data (failure rates, error messages)
- Broken coordination (instructions reference things that don't exist)
- Dead code, placeholder files, unfinished features presented as complete
- Pipeline stages that are out of sync

### 4.4 Architecture & Code Quality

**Structural analysis:**
- Storage model trade-offs (file vs DB, consistency, queryability)
- Sequential bottlenecks and idle time
- Schema/contract inconsistencies between components
- Missing infrastructure (monitoring, alerting, retry, graceful degradation)
- Single points of failure
- Scalability limits — what breaks at 2x, 10x, 100x current load?

**Design patterns & coherence:**
- Are design patterns consistent across the codebase?
- MECE check: are responsibilities mutually exclusive and collectively
  exhaustive? Look for overlapping ownership and gaps.
- Contradictions: do any instructions, configs, or code paths contradict
  each other?

**Code quality (if source code exists):**
- File sizes — any files > 500 lines that should be split?
- Dead code, commented-out blocks, unaddressed TODOs
- Naming consistency across the codebase
- Complexity hotspots (deeply nested logic, long functions)

**Test coverage:**
- Do tests exist? What kind (unit, integration, e2e)?
- What's the coverage? Are critical paths tested?
- If no tests: flag as critical gap for production readiness

### 4.5 Error Handling, Resilience & Failure Modes

Trace actual behavior for each — don't just note that mechanisms exist.

**Crash scenarios:**
- What happens when each component fails? Trace the failure path.
- Are there try/catch blocks, error boundaries, or crash handlers?
- Do errors propagate silently or get surfaced?

**Timeout coverage:**
- Are there timeouts on external calls (APIs, DB queries, web fetches)?
- What happens when a timeout fires? Retry? Fail? Hang?

**Silent failures:**
- Search for bare `except:` / `catch {}` blocks that swallow errors
- Check if scheduled jobs log failures or fail silently
- Are there any "fire and forget" operations with no confirmation?

**Data integrity:**
- Can a crash mid-write corrupt data? (atomic writes, transactions)
- Are there orphaned records, dangling references, or stale state?
- Is there validation at system boundaries?

**Edge cases:**
- What happens with empty input, null values, malformed data?
- What happens at boundary conditions (0 items, max items, duplicates)?
- What happens with concurrent access (two agents writing same file)?

**System-level failure modes:**
- What happens if the primary data store goes down?
- What happens if an external API/service is unavailable?
- What happens if a scheduled job fails silently?
- What's the maximum data loss window?
- What's the recovery time objective?
- Has any of this been tested?

### 4.6 Performance & Bottleneck Analysis

See [Performance Analysis](references/performance-analysis.md) for the
full checklist covering timing, parallelism, scaling, resource waste,
cost analysis, and optimization opportunities.

Summarize key findings here: biggest bottleneck, biggest waste, estimated
cost, and top 3 optimization opportunities with expected impact.

---

## Phase 5: Security, Readiness & Recommendations

### 5.1 Security & Data Exposure

See [Security Checklist](references/security-checklist.md) for the full
list of checks covering secrets, injection, PII, supply chain, workflow
security, and network exposure.

Summarize key findings here: any secrets exposed, injection risks found,
PII handling issues, dependency vulnerabilities.

### 5.2 Logging & Observability

- Do logs exist? Where are they written?
- Are logs structured (JSON with fields) or unstructured (free text)?
- Can you trace a request/signal end-to-end through the system?
- Is there log rotation? Are old logs purged or do they grow forever?
- Are errors logged with enough context to diagnose?
- Is there any monitoring dashboard or alerting?

### 5.3 Documentation Quality

Compare documentation against the actual system:
- **Accuracy**: does the README/docs describe what the system actually
  does today, or a past/aspirational version?
- **Completeness**: could someone else set up, operate, and troubleshoot
  this system from the docs alone?
- **Maintenance**: when was documentation last updated vs last code change?
- **Onboarding**: is there a quickstart? Could a new team member get
  productive in < 1 hour?

Flag: any doc that describes features that don't exist, or omits features
that do exist.

### 5.4 Goal Fulfillment

Compare the **stated objective** (captured in Phase 1d) against actual behavior:
- Does the system do what it claims to do?
- Are there features described in docs/README that don't work?
- Are there capabilities the system has that aren't documented?
- Is the objective achievable with the current architecture?

### 5.5 Blind Spots
What nobody is monitoring. Check for:
- Human feedback loop (does anyone evaluate the output?)
- Cost/resource tracking
- SLA monitoring (are deadlines/targets met?)
- Input health monitoring (are data sources reliable?)
- Error alerting (do failures surface or stay silent?)
- Graceful degradation (what happens when one component fails?)

### 5.6 Objective Clarity Assessment

| Dimension | Rating (1-10) | Evidence |
|-----------|---------------|----------|
| Objective clarity | | Is the goal well-defined? |
| Goal fulfillment | | Does the system actually achieve it? |
| Delivery reliability | | Does it work consistently? |
| Output quality | | Is the output actually good? |
| Automation maturity | | How much runs unattended? |
| Self-improvement | | Does it learn from failures? |
| Operational visibility | | Can you see what's happening? |
| Resource efficiency | | Is it wasteful or lean? |

Adapt dimensions to the project type. Drop irrelevant ones, add
project-specific ones.

### 5.7 Overall Rating
X/10 with one-sentence justification.

### 5.8 Production Readiness Assessment

Rate each gate as PASS / PARTIAL / FAIL:

| Gate | Status | Evidence |
|------|--------|----------|
| **Functionality** — does it do what it promises? | | |
| **Reliability** — does it work consistently without manual intervention? | | |
| **Error handling** — does it recover from failures gracefully? | | |
| **Security** — no exposed secrets, injection risks, or PII leaks? | | |
| **Testing** — are critical paths covered by tests? | | |
| **Monitoring** — can you tell when something breaks? | | |
| **Documentation** — can someone else operate this? | | |
| **Scalability** — will it handle growth without redesign? | | |
| **Data integrity** — is data consistent, backed up, recoverable? | | |
| **Dependency health** — are deps maintained, pinned, vulnerability-free? | | |

**Verdict**: Ready to ship / Needs N fixes before shipping / Not production-ready

If not ready: list the specific blockers in priority order.

### 5.9 Top 10 Ranked Recommendations

| # | Action | Impact | Effort | Who Implements |
|---|--------|--------|--------|----------------|
| 1 | ... | Critical | Low | ... |

For "Who Implements": can the system's own agents/workers fix this,
or does the human need to intervene directly?

### 5.10 The Uncomfortable Question
The one thing the project owner needs to hear but probably doesn't
want to. Infrastructure gaps, fundamental design flaws, or unstated
assumptions that undermine everything else.

---

## Phase 6: Resilience Testing

**If no backups exist**: note as critical gap in the report. Skip
restore testing but still assess operational resilience.

See [Resilience Testing](references/resilience-testing.md) for backup
validation steps and operational resilience checks.

---

## Output Format

Structured markdown report with:
- Tables for ratings, recommendations, and reliability metrics
- Direct, challenging tone — find what's wrong, not just what's right
- Evidence for every claim (file paths, query results, counts)
- Actionable: user should be able to say "fix them all" immediately

## Key Principles

1. **Discover, don't assume** — map structure before reading content
2. **Confirm scope** — present discovery to user before deep read
3. **Read before judging** — never critique what you haven't read
4. **Quantify** — "23% duplicate rate" not "some duplicates"
5. **Compare stated vs actual** — docs say X, system does Y
6. **Every recommendation needs**: what, why, effort, who implements
7. **Actionable in same session** — user says "fix them all", you proceed
8. **Test resilience** — verify backups restore, trace failure paths
9. **Challenge the project** — the goal is to make it better, not praise it
10. **Surface constraints** — subscription limits, peak hours, budgets, SLAs
