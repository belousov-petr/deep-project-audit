---
name: "deep-project-audit"
version: "1.0.0"
description: "Full-stack audit of any project — multi-agent systems, pipelines, codebases, or applications. Dynamically discovers project structure, reads all config/code/data, queries databases, tests backup integrity, and analyzes architecture, reliability, efficiency, and security. Produces ranked actionable recommendations. Use when asked to audit, analyze, review, stress-test, or challenge any project, or when user asks 'how solid is this project', 'what is missing', or 'find the weak spots'."
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

---

## Phase 2: Full Content Read (Parallel)

Dispatch **4 parallel agents**, each reading one slice of the project.
Adapt the slices to whatever Phase 1 discovered.

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

If the project has a database (SQL, NoSQL, or embedded):

### 3a. Find Connection Credentials
- Check config files, .env, source code for connection strings
- For embedded databases, trace from running processes to find binaries and auth

### 3b. Query Operational Metrics

Adapt queries to whatever database exists:

**For SQL databases (PostgreSQL, SQLite, MySQL):**
```sql
-- Schema overview: what tables exist and how big are they?
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- If there are agent/run/job tables, get reliability stats:
-- Success rate, failure rate, average duration per agent/worker

-- Recent failures with error details

-- Data freshness: when was the last write to key tables?
```

**For file-based data stores:**

Count files per directory, check modification dates. Identify stale
data (last modified > expected interval). Check for schema consistency
across sample files.

**For NoSQL databases:**
- Collection sizes, document counts
- Index health
- Recent error logs

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
- Are design patterns consistent across the codebase? (e.g., one module
  uses event-driven, another uses polling — is this intentional or drift?)
- MECE check: are responsibilities mutually exclusive and collectively
  exhaustive? Look for overlapping ownership (two components doing the
  same thing) and gaps (work that nobody owns).
- Contradictions: do any instructions, configs, or code paths contradict
  each other? (e.g., agent A told to write to path X, agent B told to
  read from path Y for the same data)

**Code quality (if source code exists):**
- File sizes — any files > 500 lines that should be split?
- Dead code, commented-out blocks, TODOs that were never addressed
- Naming consistency across the codebase
- Complexity hotspots (deeply nested logic, long functions)

**Test coverage:**
- Do tests exist? What kind (unit, integration, e2e)?
- What's the coverage? Are critical paths tested?
- If no tests: flag as critical gap for production readiness

### 4.5 Error Handling, Resilience & Failure Modes

This section covers both code-level error handling and system-level
failure modes. For each, trace the actual behavior — don't just note
that mechanisms exist.

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
- Is there validation at system boundaries (input from users, APIs, files)?

**Edge cases:**
- What happens with empty input, null values, malformed data?
- What happens at boundary conditions (0 items, max items, duplicate items)?
- What happens with concurrent access (two agents writing same file)?

**System-level failure modes:**
- What happens if the primary data store goes down?
- What happens if an external API/service is unavailable?
- What happens if a scheduled job fails silently?
- What's the maximum data loss window?
- What happens if the host goes down? Is there a migration/deployment path?
- What's the recovery time objective?
- Has any of this been tested?

### 4.6 Performance & Bottleneck Analysis

**Timing:**
- How long does each pipeline stage take? Where is time spent?
- What's the end-to-end latency from input to output?
- Are there unnecessary sequential operations that could be parallel?

**Parallelism:**
- What runs in parallel? What's forced sequential?
- Are there lock contention or race condition risks?
- Could throughput increase with more parallelism?

**Scaling:**
- What happens at 2x, 10x, 100x current data volume?
- Are there O(n^2) operations hiding in loops?
- Is storage growing linearly or accelerating?

**Resource waste (quantified):**
- Duplicate processing across pipeline stages
- Empty/low-value items consuming processing time
- Redundant operations (same data read/written multiple times)
- Oversized storage (backups, logs, caches)
- Logic waste: unnecessary steps, over-engineered paths, actions that
  produce no value
- Token/API waste: calls that could be batched, cached, or skipped

**Cost analysis:**
- What does this project cost to run per day/week/month?
- For LLM-powered: token/message consumption vs subscription/API budget
- For API-based: external service costs
- For infrastructure: compute, storage, bandwidth
- Is the cost justified by the value delivered?

**Optimization opportunities** with estimated impact.

---

## Phase 5: Security, Readiness & Recommendations

### 5.1 Security & Data Exposure

**Secrets & credentials:**
- Scan for hardcoded API keys, tokens, passwords, connection strings
- Check .gitignore — are .env, credentials, key files excluded?
- Check git history for accidentally committed secrets
- Are secrets in plaintext or encrypted/vault store?

**Injection vulnerabilities:**
- SQL injection: user input parameterized or string-concatenated?
- Prompt injection: can external data influence LLM system prompts?
- Command injection: does any code pass user input to shell commands?
- Path traversal: can file paths be manipulated?

**Privacy & PII:**
- Scan data files and database for PII (names, emails, phone numbers,
  addresses, IPs, financial data, government IDs)
- How is PII stored? Encrypted at rest? Access-controlled?
- Data retention policy? Are old records purged?
- GDPR: right to deletion, portability, consent tracking
- Are logs sanitized or do they contain sensitive data?

**Supply chain:**
- Dependencies from trusted sources? Lock files committed?
- Known CVEs? (`npm audit`, `pip audit`, `cargo audit`)
- CI/CD actions pinned to specific versions?

**Workflow security:**
- Who can trigger runs? Is there authentication?
- Can a worker escalate privileges or access other workers' data?
- Are webhook endpoints authenticated?

**Network & infrastructure:**
- What ports are open? Localhost only or publicly accessible?
- TLS/SSL where needed?
- Rate limits on external services (LLM providers, APIs)
- Peak hour pricing or throttling

### 5.2 Logging & Observability

- Do logs exist? Where are they written?
- Are logs structured (JSON with fields) or unstructured (free text)?
- Can you trace a request/signal end-to-end through the system?
- Is there log rotation? Are old logs purged or do they grow forever?
- Are errors logged with enough context to diagnose (stack trace, input
  data, timestamp, component name)?
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
- Is the objective achievable with the current architecture, or is there
  a fundamental mismatch?

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

### 6a. Backup Validation (if backups exist)

**Test it. Don't just note that backups exist.**

1. Find the latest backup file
2. Check its structure (header, footer, completeness)
3. If possible: restore into a temporary location, verify data integrity,
   compare with production, clean up
4. Report: does disaster recovery actually work?

### 6b. Operational Resilience
- Is there a documented recovery procedure?
- Can the system be migrated to a different host?
- What's the recovery time objective?
- Has disaster recovery ever been tested?

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
