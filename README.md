# Deep Project Audit

A reusable audit methodology for any software project -- multi-agent systems, data pipelines, web applications, CLI tools, or microservices. Built as a [Claude Code Skill](https://code.claude.com/docs/en/skills) that runs a structured 6-phase analysis, producing a ranked report with actionable recommendations.

Born from auditing a 12-agent AI intelligence pipeline on [Paperclip](https://github.com/paperclipai/paperclip), refined into a project-agnostic framework.

## What it does

One command. Full analysis. Actionable output.

```
/deep-project-audit
```

The audit discovers your project structure dynamically, reads everything, queries databases, tests backup integrity, and produces a structured report covering:

- Architecture and code quality -- design patterns, MECE analysis, contradictions, scalability, test coverage
- Error handling and resilience -- crash scenarios, timeout coverage, silent failures, data integrity, edge cases
- Performance and bottleneck analysis -- timing, parallelism, scaling limits, resource waste, cost analysis
- Security and data exposure -- secrets, injection vulnerabilities, PII, supply chain, workflow security
- Logging and observability -- structured logs, traceability, alerting, monitoring
- Documentation quality -- accuracy vs codebase, completeness, onboarding readiness
- Production readiness -- 10-gate PASS/PARTIAL/FAIL checklist with a ship/no-ship verdict
- Ranked recommendations -- top 10 actions with impact, effort, and who implements

## How it works

### Phase 1: Discover
Maps the project structure dynamically. No assumptions about folder names, frameworks, or conventions. Checks git history, reads the stated project goal, and confirms scope with you before proceeding.

### Phase 2: Read (parallel)
Dispatches 4 parallel agents to read everything simultaneously:
- Agent 1: Architecture and configuration
- Agent 2: Execution logic and coordination
- Agent 3: Outputs, docs and reviews
- Agent 4: Data, infrastructure and supporting files

### Phase 3: Diagnose
Connects to databases (SQL, NoSQL, or embedded), queries operational metrics, checks agent/worker reliability, and identifies data freshness issues.

### Phase 4: Analyze
Produces the structured quality analysis: architecture review, error handling audit, performance bottleneck identification, and resource waste quantification.

### Phase 5: Assess
Security scan, PII detection, documentation quality check, goal fulfillment comparison, production readiness assessment, and the ranked recommendations.

### Phase 6: Test resilience
Validates backups actually restore (not just that they exist), traces failure modes, and assesses operational resilience.

## What happens after the audit

The report is designed to be actionable immediately. You can say:

```
Fix them all
```

And the audit findings become the implementation plan.

For larger projects, you can also:
- Pick specific recommendations to implement first
- Ask for a deeper dive into any section ("expand on the security findings")
- Schedule a follow-up audit after fixes to verify improvement
- Run partial re-audits on specific phases ("just re-run Phase 5 on security")

## Installation

### Claude Code (CLI or Desktop)

Copy the skill to your skills directory:

```bash
# Clone the repo
git clone https://github.com/belousov-petr/deep-project-audit.git

# Copy to Claude Code skills directory
mkdir -p ~/.claude/skills/deep-project-audit
cp deep-project-audit/SKILL.md ~/.claude/skills/deep-project-audit/SKILL.md
```

Or download directly:

```bash
mkdir -p ~/.claude/skills/deep-project-audit
curl -o ~/.claude/skills/deep-project-audit/SKILL.md \
  https://raw.githubusercontent.com/belousov-petr/deep-project-audit/main/SKILL.md
```

Restart Claude Code. The skill appears as `/deep-project-audit`.

### Verify installation

```
> /deep-project-audit
```

You should see Claude begin Phase 1: discovering your project structure.

## Usage

### Basic

Navigate to your project directory and run:

```
/deep-project-audit
```

Or use natural language:

```
Audit this project
How solid is this project?
Find the weak spots
Stress-test this codebase
```

### What you get

A structured markdown report with:

1. Project summary -- what it is, derived from what was read
2. Strengths -- what's genuinely good, with evidence
3. Critical issues -- what will break soon, with evidence
4. Architecture review -- structural problems, MECE gaps, contradictions
5. Error handling audit -- crash paths, silent failures, edge cases
6. Performance analysis -- bottlenecks, waste, cost
7. Security scan -- secrets, injection risks, PII exposure
8. Observability check -- logging, monitoring, alerting
9. Documentation review -- accuracy, completeness, onboarding
10. Goal fulfillment -- stated vs actual behavior
11. Blind spots -- what nobody is watching
12. Ratings table -- 8 dimensions scored 1-10
13. Overall rating -- X/10 with justification
14. Production readiness -- 10-gate PASS/PARTIAL/FAIL with ship verdict
15. Top 10 recommendations -- ranked by impact with effort estimates
16. The uncomfortable question -- the one thing you need to hear

## Works on

| Project type | What gets analyzed |
|---|---|
| Multi-agent systems (Paperclip, CrewAI, AutoGen) | Agent instructions, heartbeats, coordination, pipeline flow, signal quality |
| Web applications | Routes, API design, auth, DB schema, frontend/backend separation |
| Data pipelines | Stage flow, data integrity, scheduling, error handling, throughput |
| CLI tools | Argument handling, error messages, edge cases, documentation |
| Monorepos | Package boundaries, dependency management, build system, cross-package consistency |
| Microservices | Service boundaries, API contracts, resilience patterns, observability |

## How it thinks

The audit follows a few rules I keep coming back to when reviewing my own projects:

1. Look at the project before making assumptions about it. Map the structure first, read second.
2. Check with the user before going deep. A quick "this is what I found, this is what I'll audit -- sound right?" saves everyone's time.
3. Don't critique what you haven't read. Opinions come after evidence.
4. Put numbers on things. "23% duplicate rate" tells you something. "There are some duplicates" doesn't.
5. Compare what the docs promise against what the code actually does. The gap between those two is where most problems hide.
6. Every recommendation has to answer four things: what to fix, why it matters, how much work it is, and who should do it. Anything less is just complaining.
7. The audit should be useful right now, not next sprint. If you can say "fix them all" and start implementing in the same session, the audit did its job.
8. Actually test the safety nets. Backups exist? Restore one. Retry logic? Trace what happens when it fires. Don't report that mechanisms exist -- report whether they work.
9. Find what's wrong, not just what's right. The point is to make the project better, not to feel good about it.
10. Surface the constraints nobody talks about -- subscription limits, rate limit windows, daily budgets, peak hour pricing. These shape what's actually possible more than architecture does.

## Why this exists

I was working on a 12-agent intelligence pipeline and every time I wanted to review the whole thing properly, I'd write out a long prompt from scratch. And every time, there'd be that one check I only remembered after the review was done. Sometimes it was security. Sometimes backup validation. Sometimes I'd just forget to look at how the agents actually coordinate with each other.

It's never the obvious stuff. It's always the thing you assumed was fine until it wasn't.

So I made this into a skill. Same checklist, same sequence, every time. Now I run one command and know I'm not skipping anything. It also turned up things I wasn't even looking for, which was the part that surprised me. After running it on a few different projects I figured other people might get something out of it too.

## What it costs

A typical audit consumes **100K-300K tokens** (input + output across all 6 phases),
depending on project size. A large multi-agent system with 600+ files and a database
runs ~250K tokens. A small CLI tool with 20 files runs ~50K tokens. See
[`examples/sample-audit.md`](examples/sample-audit.md) for a full anonymized example
from a real 16-agent intelligence pipeline.

## Contributing

If you've run this audit and found gaps, I'd like to hear about it. Open an issue or PR with:

1. What kind of project you were auditing
2. What analysis you think the skill should have covered but didn't
3. What test or criteria you'd add to fill that gap

## License

This work is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

You are free to use, share, and adapt this methodology for any purpose, including commercially, as long as you give appropriate credit.

## Author

**Petr Belousov** -- AI governance by day, AI builder by night.

- GitHub: [@belousov-petr](https://github.com/belousov-petr)
- LinkedIn: [petrbelousov](https://www.linkedin.com/in/petrbelousov/)
