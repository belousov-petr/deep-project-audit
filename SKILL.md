---
name: shakedown
description: >-
  Full-stack review of any project - multi-agent systems, pipelines, codebases,
  or applications. Dynamically discovers project structure, reads all
  config/code/data, queries databases, tests backup integrity, and analyzes
  architecture, reliability, efficiency, and security. Produces ranked actionable
  recommendations. Use when asked to review a project, do a project health check,
  stress-test a codebase, do a gap analysis, or assess technical debt.
  Also when user asks 'how solid is this project', 'what is missing',
  'find the weak spots', 'what would break first',
  'where does this need tightening', 'what's wrong with this project',
  or 'how mature is this project'.
  Do NOT activate for simple code reviews, PR reviews, or single-file analysis.
license: MIT
compatibility: >-
  Requires Claude Code or similar agent with file-read, shell execution,
  and parallel subagent capabilities
metadata:
  author: belousov-petr
  version: "1.0.0"
---

# Shakedown

Comprehensive review of any project. Discovers the structure dynamically,
reads everything, challenges every layer, finds bottlenecks, blind spots,
and waste, then produces ranked recommendations you can implement in the
same session.

Works on: multi-agent platforms (Paperclip, CrewAI, AutoGen), data
pipelines, web applications, CLI tools, monorepos, microservices -
any project with files to read and architecture to challenge.

---

## Phase 1: Discover Project Structure

Before reading anything, map the project. Do NOT assume folder names,
frameworks, or conventions - discover them.

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

Check for **agent skill indicators**:
- `SKILL.md` in the project root -> this project IS an agent skill
- `.agents/skills/` directory -> project contains or uses skills
- Skill-like YAML frontmatter (`name:`, `description:` fields)
- References to skill platforms (Claude Code, Copilot, Gemini CLI, Codex)

If agent skill detected, set a flag. This triggers section 4.8 (Agent
Skill Standards Compliance) during Phase 4.

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
- README.md - what does the project claim to do?
- PRD, spec, or design doc - what was the intended scope?
- CLAUDE.md / AGENTS.md - project-level instructions
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

Scope: review everything above. Proceed?
```

Wait for user confirmation. This prevents wasting tokens reviewing the
wrong project, wrong subdirectory, or wrong scope.

**If user declines scope**: ask what to narrow to or exclude. Do not
abort - adjust the scope and re-confirm.

### 1f. Choose Delivery Mode

After scope confirmation, ask the user how they want the report delivered:

```
Deliver the report:
  [1] Inline (default) - full report in this session. Nothing saved to disk.
  [2] File - full report in this session AND saved to
      shakedown-YYYY-MM-DD.md at the project root. Pick this when you want
      a standalone artifact to archive, share, or feed into a fresh session
      later.

Which? (default: inline)
```

Capture the choice. This only changes whether the report is persisted to
disk - both modes render the complete report in the current session, so
"fix them all" works identically in either mode.

- **Inline mode**: render the complete report in the session per the Output
  Format section below. Do not write any file.
- **File mode**: render the complete report in the session AS WELL, then
  also write the identical report to `shakedown-YYYY-MM-DD.md` at the
  project root (use today's date). After writing, append one line to the
  session:

  ```
  Report saved: ./shakedown-YYYY-MM-DD.md
  ```

  If `Write` or file-creation is not available on the platform, fall back
  to inline mode and say so once.

---

## Phase 2: Full Content Read (Parallel)

Dispatch **4 parallel agents**, each reading one slice of the project.
Adapt slices to whatever Phase 1 discovered.

**Fallbacks**: If no subagent support, run slices sequentially. If
>1000 files, sample 2-3 per directory and count the rest. If an agent
fails, continue with the rest and note the gap.

### Agent 1: Architecture & Configuration
Read all configuration and architectural files:
- Config files (JSON, YAML, TOML, .env - note secrets, don't expose values)
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
- Review files if they exist
- Scripts (build, deploy, report generation)

### Agent 4: Data, Infrastructure & Supporting Files
Explore and quantify (count, don't read every file):
- All data directories - count files, read 2-3 samples to understand schema
- Logs - check latest entries for errors, check if structured (JSON) or unstructured
- Backups - list, check sizes and dates
- Skills/plugins/extensions - read definitions
- Memory/state files - understand persistence model

---

## Phase 3: Data Store Diagnostics

If the project has a database (SQL, NoSQL, or embedded), run diagnostics.

**If no database found**: skip this phase. Note "No data store detected"
in the report and proceed to Phase 4.

**If database found but credentials unavailable**: skip queries. Note
"Database detected but could not access - manual credential needed" and
proceed to Phase 4.

**If shell execution is not available**: skip this phase entirely. Note
"Data store diagnostics skipped - no shell access" and proceed to Phase 4.

See [DB Diagnostics](references/db-diagnostics.md) for database-specific
queries and inspection guidance.

---

## Phase 4: Quality Analysis

Synthesize everything from Phases 1-3.

### 4.1 What the Project Is
One paragraph: purpose, who it serves, architecture summary, tech stack.
Derived from what you read, not assumed.

### 4.2 What Works Well
Genuine strengths with evidence. Be specific - cite files, patterns,
design decisions that are genuinely good.

### 4.3 Critical Issues
Things that will cause failures soon. Must include evidence:
- Reliability data (failure rates, error messages)
- Broken coordination (instructions reference things that don't exist)
- Dead code, placeholder files, unfinished features presented as complete
- Pipeline stages that are out of sync

### 4.4 Architecture & Code Quality

Evaluate structural analysis, design pattern coherence (MECE check,
contradictions), algorithm efficiency, code quality (dead code,
complexity hotspots, naming), dependency graph, and test coverage.

See [Architecture & Code Quality](references/architecture-quality.md)
for the full checklist. Key outputs: biggest structural risk, MECE gaps,
test coverage assessment, and complexity hotspots.

### 4.5 Error Handling, Resilience & Failure Modes

Trace actual behavior - don't just note that mechanisms exist. Cover
crash scenarios, timeout coverage, silent failures, data integrity,
edge cases, system-level failure modes, retry patterns, and graceful
degradation.

See [Error Handling & Resilience](references/error-resilience.md)
for the full checklist. Key outputs: failure paths traced, silent
failure inventory, data loss window, and recovery readiness.

### 4.6 Performance & Bottleneck Analysis

See [Performance Analysis](references/performance-analysis.md) for the
full checklist covering timing, parallelism, scaling, resource waste,
cost analysis, and optimization opportunities.

Summarize key findings here: biggest bottleneck, biggest waste, estimated
cost, and top 3 optimization opportunities with expected impact.

### 4.7 Code & Storage Efficiency

Assess how lean the project's file footprint is. Check for: empty
(0-byte) files, duplicate files across directories, build artifacts or
temp files committed to git, copy-pasted code blocks, dead dependencies
(declared but unused), and storage bloat (large binaries, oversized logs).

See [Storage Efficiency](references/storage-efficiency.md) for the full
checklist with commands. Quantify: total waste in file count and bytes.

### 4.8 Agent Skill Standards Compliance

**Conditional - only run if Phase 1 detected this project is an agent skill.**
If not a skill, note "Not an agent skill - section skipped."

Evaluate against the Agent Skills specification (agentskills.io) and
platform best practices. See [Skill Standards](references/skill-standards.md)
for the full compliance checklist.

Summarize as: spec conformance, description quality, instruction quality,
script quality, eval framework, and progressive disclosure - each rated
PASS / PARTIAL / FAIL with specific issues noted.

---

## Phase 5: Security, Readiness & Recommendations

### 5.1 Security & Data Exposure

See [Security Checklist](references/security-checklist.md) for the full
list of checks organized into 8 sections:

- **A. Traditional Security** - secrets, injection, PII, supply chain,
  workflow, network, licensing
- **B. OWASP LLM Top 10 (2025)** - prompt injection, sensitive info
  disclosure, supply chain, data poisoning, output handling, excessive
  agency, system prompt leakage, vector weaknesses, misinformation,
  unbounded consumption
- **C. OWASP Agentic Top 10 (2026)** - agent goal hijack, tool misuse,
  identity abuse, supply chain, RCE, memory poisoning, inter-agent
  communication, cascading failures, trust exploitation, rogue agents
- **D. MCP Security** - architecture, tool safety, data validation,
  prompt injection controls, authentication, deployment
- **E. GenAI Data Security (DSGAI)** - data leakage, credential
  exposure, shadow AI, poisoning, governance, vector stores, telemetry
- **F. AI Governance & Compliance** - asset inventory, threat modeling,
  regulatory compliance, TEVV
- **G. Red Teaming Readiness** - process, coverage, tooling
- **H. Concrete Test Procedures** - 23 detailed how-to test guides
  with specific attack techniques and OWASP references

Run sections B-G only if the project uses LLM/GenAI/agentic components.

Summarize key findings here: any secrets exposed, injection risks found,
PII handling issues, dependency vulnerabilities, LLM/agent-specific risks.

### 5.2 Logging & Observability

Assess log existence, quality (structured vs free text), traceability
(can you follow a request end-to-end?), lifecycle (rotation, retention),
and monitoring/alerting.

See [Operational Health](references/operational-health.md) for the full
checklist.

### 5.3 Documentation Quality

Compare documentation against the actual system: accuracy (docs vs
reality), completeness (could someone else operate this?), maintenance
(when last updated?), and onboarding quality.

See [Operational Health](references/operational-health.md) for the full
checklist. Flag any doc that describes nonexistent features or omits
existing ones.

### 5.4 Goal Fulfillment

**Scope:** Technical comparison - does the code match the docs? For
strategic assessment (should this exist?), see 5.10 Value Assessment.

Compare the **stated objective** (captured in Phase 1d) against actual behavior:
- Does the system do what it claims to do?
- Are there features described in docs/README that don't work?
- Are there capabilities the system has that aren't documented?
- Is the objective achievable with the current architecture?

### 5.5 Blind Spots

What nobody is monitoring: feedback loops, cost tracking, SLA adherence,
input health, error visibility, graceful degradation, and drift/rot.

See [Operational Health](references/operational-health.md) for the full
checklist.

### 5.6 Objective Clarity Assessment

**Scope:** Operational dimensions (does it work reliably?). For
strategic dimensions (is it worth building?), see 5.10 Value Assessment.

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
| **Functionality** - does it do what it promises? | | |
| **Reliability** - does it work consistently without manual intervention? | | |
| **Error handling** - does it recover from failures gracefully? | | |
| **Security** - no exposed secrets, injection risks, or PII leaks? | | |
| **Testing** - are critical paths covered by tests? | | |
| **Monitoring** - can you tell when something breaks? | | |
| **Documentation** - can someone else operate this? | | |
| **Scalability** - will it handle growth without redesign? | | |
| **Data integrity** - is data consistent, backed up, recoverable? | | |
| **Dependency health** - are deps maintained, pinned, vulnerability-free? | | |

**Readiness summary**: State the count of PASS / PARTIAL / FAIL gates, then list the specific blockers in priority order. Do not issue a "ready to ship" or "not production-ready" verdict - that call is the user's, not yours.

### 5.9 Top 10 Ranked Recommendations

| # | Action | Impact | Effort | Who Implements |
|---|--------|--------|--------|----------------|
| 1 | ... | Critical | Low | ... |

For "Who Implements": can the system's own agents/workers fix this,
or does the human need to intervene directly?

### 5.10 Value Assessment

**Scope:** Strategic assessment - should this project exist in its
current form? For technical goal comparison (code vs docs), see 5.4.
For operational ratings (reliability, automation), see 5.6.

Assess: problem clarity, target audience definition, maturity vs.
claims, measurable value, differentiation from alternatives, and
adoption readiness.

See [Value Assessment](references/value-assessment.md) for the full
framework with questions per dimension.

Summarize as a table:

| Dimension | Rating (1-5) | Evidence |
|-----------|--------------|----------|
| Problem clarity | | |
| Audience definition | | |
| Maturity vs. claims | | |
| Measurable value | | |
| Differentiation | | |
| Adoption readiness | | |

### 5.11 The Uncomfortable Question
The one thing the project owner needs to hear but probably doesn't
want to. Infrastructure gaps, fundamental design flaws, or unstated
assumptions that undermine everything else.

---

## Phase 6: Resilience Testing

**If no backups exist**: note as critical gap in the report. Skip
restore testing but still assess operational resilience.

**If shell execution is not available**: skip restore testing. Instead,
assess resilience from code analysis only - check whether backup logic
exists in the code, whether recovery procedures are documented, and
whether there are any disaster recovery references. Note "Resilience
testing limited - no shell access for restore verification."

See [Resilience Testing](references/resilience-testing.md) for backup
validation steps and operational resilience checks.

---

## Output Format

Structured markdown report with:
- Tables for ratings, recommendations, and reliability metrics
- Direct, challenging tone - find what's wrong, not just what's right
- Evidence for every claim (file paths, query results, counts)
- Actionable: user should be able to say "fix them all" immediately

Apply the delivery mode captured in Phase 1f: either stream the full
report into the session (inline) or write it to
`shakedown-YYYY-MM-DD.md` and print the short summary block (file).

## Gotchas

See [Gotchas](references/gotchas.md) for the full list of 10 common
agent mistakes with examples and fixes. Read before starting Phase 4.

Key ones: don't praise by default, evaluate don't just list features,
read files before referencing them, treat code as truth over README,
go deep on security, always estimate cost, make recommendations
specific, and check what happens at scale.

## Key Principles

1. **Discover, don't assume** - map structure before reading content
2. **Confirm scope** - present discovery to user before deep read
3. **Read before judging** - never critique what you haven't read
4. **Quantify** - "23% duplicate rate" not "some duplicates"
5. **Compare stated vs actual** - docs say X, system does Y
6. **Every recommendation needs**: what, why, effort, who implements
7. **Actionable in same session** - user says "fix them all", you proceed
8. **Test resilience** - verify backups restore, trace failure paths
9. **Challenge the project** - the goal is to make it better, not praise it
10. **Surface constraints** - subscription limits, peak hours, budgets, SLAs
