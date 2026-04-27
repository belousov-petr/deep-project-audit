# Error Handling, Resilience & Failure Modes - Reference

Detailed checks for Section 4.5. Trace actual behavior for each - 
don't just note that mechanisms exist.

**Scope boundary:** This file covers code-level analysis of failure
modes (what *would* happen). For live data store queries, see
`db-diagnostics.md` (Phase 3). For hands-on restore and recovery
testing, see `resilience-testing.md` (Phase 6).

---

## Crash Scenarios

- What happens when each component fails? Trace the failure path.
- Are there try/catch blocks, error boundaries, or crash handlers?
- Do errors propagate silently or get surfaced?
- Does a crash in one component cascade to others?
- Is there a process supervisor that restarts crashed workers?
- What's the startup behavior after a crash? (clean start vs resume)

## Timeout Coverage

- Are there timeouts on external calls (APIs, DB queries, web fetches)?
- What happens when a timeout fires? Retry? Fail? Hang?
- Are timeout values appropriate? (too short = false failures, too
  long = resource exhaustion)
- Is there a global timeout for end-to-end operations?
- What happens when a timeout fires mid-transaction?

## Silent Failures

- Search for bare `except:` / `catch {}` blocks that swallow errors
- Check if scheduled jobs log failures or fail silently
- Are there any "fire and forget" operations with no confirmation?
- Do background workers report failures to anyone?
- Are there operations that return success even when they fail internally?
- Check for error codes that are generated but never checked

## Data Integrity

- Can a crash mid-write corrupt data? (atomic writes, transactions)
- Are there orphaned records, dangling references, or stale state?
- Is there validation at system boundaries?
- Are writes idempotent? (safe to retry without duplicating data)
- Is there a consistency check or repair mechanism?
- Can you detect when data is corrupted vs. when it looks normal but wrong?

## Edge Cases

- What happens with empty input, null values, malformed data?
- What happens at boundary conditions (0 items, max items, duplicates)?
- What happens with concurrent access (two agents writing same file)?
- What about unicode, special characters, or very long strings?
- What about clock skew, timezone issues, or daylight saving transitions?
- What about disk full, memory exhaustion, or network partition?

## System-Level Failure Modes

- What happens if the primary data store goes down?
- What happens if an external API/service is unavailable?
- What happens if a scheduled job fails silently?
- What's the maximum data loss window?
- What's the recovery time objective (RTO)?
- What's the recovery point objective (RPO)?
- Has any of this been tested?
- Is there a documented runbook for incident response?

## Retry & Recovery Patterns

- Is there retry logic? What's the strategy? (fixed, exponential backoff,
  jitter, circuit breaker)
- Are retries bounded? (max attempts, max total time)
- Is there a dead letter queue or fallback path for permanent failures?
- Can the system resume from where it left off after a partial failure?
- Are partial results handled correctly or does it require all-or-nothing?

## Graceful Degradation

- Can the system operate in a reduced capacity when parts fail?
- Are there feature flags or circuit breakers for non-critical paths?
- Does the system communicate degradation to users/operators?
- What's the minimum viable configuration (which components are required
  vs. optional)?

---

## GenAI & Agentic Failure Modes

**Conditional - only evaluate if the project uses LLMs, agents, or MCP.**

_[Ref: OWASP Top 10 for Agentic Applications 2026 ASI08 - Cascading
Failures; OWASP GenAI Data Security 2026 DSGAI17 - Data Availability
& Resilience Failures in AI Pipelines]_

### Agent Cascading Failures
- Can a failure, hallucination, or poisoned output in one agent
  propagate to downstream agents?
  _[Ref: OWASP Agentic Top 10 ASI08]_
- Are there circuit breakers between agents to stop error propagation?
- Can a hallucinating agent trigger real-world actions (delete, send,
  modify) before the error is caught?
- Are there blast radius controls (isolation, bulkheads) to contain
  agent failures?
- Is there a kill switch for runaway autonomous agents?
  _[Ref: OWASP Agentic Top 10 ASI10 - Rogue Agents]_

### Hallucination-Driven Failure Paths
- What happens when the LLM generates confident but incorrect output?
- Are downstream systems protected against acting on hallucinated data?
- Is there validation of LLM output before it triggers actions?
- Can hallucinated tool calls cause data corruption or loss?
  _[Ref: OWASP LLM Top 10 LLM09 - Misinformation; Agentic Exploits
  Tracker: Replit Vibe Coding Meltdown Jul 2025 - agent hallucinated
  data, deleted production DB, generated false outputs to hide mistakes]_

### LLM/API Availability Failures
- What happens when the LLM provider API is down or rate-limited?
- Is there a fallback model or degraded-mode behavior?
- What happens when RAG retrieval fails (vector store down, index
  corrupted)? Does the system hallucinate without retrieval?
- Are there timeouts on LLM inference that prevent resource exhaustion?
  _[Ref: OWASP LLM Top 10 LLM10 - Unbounded Consumption]_

### Tool & MCP Failure Modes
- What happens when an MCP server or tool is unavailable?
- Can a malicious tool response crash the agent or cause infinite loops?
- Are tool timeouts enforced to prevent hanging agents?
- What happens when a tool returns malformed or adversarial output?
  _[Ref: OWASP Cheatsheet for Securely Using Third-Party MCP Servers
 - Tool Interference: "Set Timeouts"]_

### Memory & State Corruption
- Can corrupted agent memory cause persistent failures across sessions?
- Is there a mechanism to detect and repair corrupted state?
- Can poisoned memory entries cause the agent to make wrong decisions
  indefinitely? _[Ref: OWASP Agentic Top 10 ASI06]_
- Is there a clean-state restart option for agents?
