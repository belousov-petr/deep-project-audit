# Evals

Test cases for measuring whether `deep-project-audit` adds value over a bare "audit this project" prompt.

## How it works

Each eval in `evals.json` defines:
- **Project characteristics** — what kind of project to test against
- **Prompt** — the user instruction
- **Assertions** — what the output must contain to pass

## Running evals

1. Pick a real project matching the eval's `project_characteristics`
2. Run the audit **with** the skill active: `/deep-project-audit`
3. Run the same prompt **without** the skill (bare): "Audit this project — find what's broken and what to fix first"
4. Grade each output against the assertions
5. Compare pass rates

## Grading

- Each assertion is binary: pass or fail
- An eval passes if >= 80% of its assertions pass
- The skill proves value if with-skill pass rate is significantly higher than without-skill (target: >30% delta)

## Test cases

| ID | Name | Tests |
|----|------|-------|
| 1 | small-cli-tool | Minimal project handling, DB skip, missing test detection |
| 2 | medium-web-app-with-db | DB diagnostics, doc-vs-reality, security checks |
| 3 | large-agent-system | Parallel reads, sampling, agent coordination analysis |
| 4 | outdated-docs-project | Stated-vs-actual detection, doc discrepancy flagging |
| 5 | no-tests-production-claim | Production readiness gating on test coverage |
