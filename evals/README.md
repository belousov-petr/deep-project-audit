# Evals

Test cases for measuring whether `shakedown` adds value over a bare "review this project" prompt. Follows the [agentskills.io eval methodology](https://agentskills.io/skill-creation/evaluating-skills).

## How it works

Each eval in `evals.json` defines:
- **Project characteristics** - what kind of project to test against
- **Prompt** - the user instruction
- **Assertions** - what the output must contain to pass

## Running evals

1. Pick a real project matching the eval's `project_characteristics`
2. Run the review **with** the skill active: `/shakedown`
3. Run the same prompt **without** the skill (bare): "Review this project - find what's broken and what to fix first"
4. Save outputs to the workspace structure below
5. Grade each output against the assertions
6. Compare pass rates

## Workspace structure

```
shakedown-workspace/
  iteration-1/
  eval-small-cli-tool/
  with_skill/
  outputs/ # Review report output
  timing.json # {"total_tokens": N, "duration_ms": N}
  grading.json # {"assertion_results": [...], "summary": {...}}
  without_skill/
  outputs/
  timing.json
  grading.json
  eval-medium-web-app-with-db/
  ...
  benchmark.json # Aggregated pass rates and deltas
```

### timing.json format

```json
{
  "total_tokens": 145000,
  "duration_ms": 180000
}
```

### grading.json format

```json
{
  "assertion_results": [
  {"id": "1.1", "text": "contains 'What the Project Is' section", "passed": true, "evidence": "Found at line 45 of output"},
  {"id": "1.2", "text": "contains production readiness table", "passed": true, "evidence": "10-gate table at line 120"}
  ],
  "summary": {
  "passed": 7,
  "failed": 0,
  "total": 7,
  "pass_rate": 1.0
  }
}
```

### benchmark.json format

```json
{
  "with_skill": {"pass_rate": {"mean": 1.0, "stddev": 0.0}, "tokens": {"mean": 145000, "stddev": 30000}},
  "without_skill": {"pass_rate": {"mean": 0.11, "stddev": 0.05}, "tokens": {"mean": 25000, "stddev": 8000}},
  "delta": {"pass_rate": 0.89, "tokens": 120000}
}
```

## Grading

- Each assertion is PASS or FAIL with specific evidence (quote or reference the output)
- Require concrete evidence for PASS - no benefit of the doubt
- An eval passes if >= 80% of its assertions pass
- The skill proves value if with-skill pass rate is significantly higher than without-skill (target: >30% delta)

## Iteration

After grading, analyze patterns:
- Assertions that always pass in both configs - remove (inflate scores)
- Assertions that always fail in both - investigate (assertion or test broken)
- Assertions that pass with skill but fail without - this is where the skill adds value
- High stddev - skill instructions may be ambiguous; tighten them

## Test cases

| ID | Name | Assertions | Tests |
|----|------|------------|-------|
| 1 | small-cli-tool | 7 | Minimal project handling, DB skip, missing test detection |
| 2 | medium-web-app-with-db | 8 | DB diagnostics, doc-vs-reality, security checks |
| 3 | large-agent-system | 8 | Parallel reads, sampling, agent coordination analysis |
| 4 | outdated-docs-project | 6 | Stated-vs-actual detection, doc discrepancy flagging |
| 5 | no-tests-production-claim | 6 | Production readiness gating on test coverage |
| 6 | agent-skill-project | 9 | Skill detection, spec compliance, description/instruction quality, value assessment |
| 7 | bloated-storage-project | 7 | Storage waste detection, quantified findings, gitignore gaps |
