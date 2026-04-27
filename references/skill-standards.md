# Agent Skill Standards Compliance - Reference

Detailed checks for Section 4.8. Only applies when the project IS an
agent skill (SKILL.md detected in Phase 1).

Based on the open Agent Skills specification (agentskills.io/specification),
best practices (agentskills.io/skill-creation), and Anthropic's skill
guidelines (github.com/anthropics/skills).

---

## 1. Specification Conformance

### SKILL.md Structure
- [ ] SKILL.md exists in the skill root directory
- [ ] YAML frontmatter present between `---` delimiters
- [ ] Frontmatter parses as valid YAML

### Required Fields
- [ ] `name` field present
- [ ] `name` is 1-64 characters
- [ ] `name` uses only lowercase letters, numbers, hyphens
- [ ] `name` does not start or end with a hyphen
- [ ] `name` has no consecutive hyphens (`--`)
- [ ] `name` matches the parent directory name
- [ ] `description` field present and non-empty
- [ ] `description` is 1-1024 characters

### Optional Fields (if present, must conform)
- [ ] `license` - license name or reference to bundled file
- [ ] `compatibility` - 1-500 chars, environment requirements
- [ ] `metadata` - key-value map (string keys to string values only)
- [ ] `allowed-tools` - space-delimited tool list (experimental)

### Size Limits
- [ ] SKILL.md is under 500 lines
- [ ] Instruction body is under ~5000 tokens (estimate: ~4 chars/token)
- [ ] File references use relative paths from skill root
- [ ] File references are one level deep (no `references/sub/sub/file.md`)

### Directory Structure
- [ ] Standard layout follows convention:
  ```
  skill-name/
  SKILL.md # Required
  scripts/ # Optional: executable code
  references/ # Optional: documentation
  assets/ # Optional: templates, resources
  ```

---

## 2. Description Quality

- [ ] Uses imperative phrasing ("Use this skill when...")
- [ ] Describes WHAT the skill does AND WHEN to use it
- [ ] Focuses on user intent, not implementation mechanics
- [ ] Includes non-obvious trigger contexts
- [ ] Stays under 1024 characters
- [ ] Contains keywords for adjacent/implicit use cases
- [ ] Would trigger on varied phrasings (formal, casual, typos)
- [ ] Would NOT false-trigger on related but different tasks

### Red Flags in Descriptions
- Generic: "Process files" (too vague to match intent)
- Implementation-focused: "Runs 4 parallel agents to..." (user doesn't
  care how, they care when/why)
- Missing trigger contexts: only describes one use case when several apply

---

## 3. Instruction Quality

### Grounded in Real Expertise
- [ ] Instructions reflect real hands-on experience, not generic advice
- [ ] Specific to the domain/environment (not "handle errors appropriately")
- [ ] References concrete file paths, commands, or patterns from practice
- [ ] Gotchas section contains non-obvious, environment-specific facts

### Scope & Coherence
- [ ] Encapsulates a coherent unit of work (not too narrow, not too broad)
- [ ] Single activation covers the full task (no need to chain skills)
- [ ] Does not try to cover unrelated responsibilities

### Detail Calibration
- [ ] Moderate detail - not exhaustive, not skeletal
- [ ] Provides defaults, not menus (picks one approach, notes alternatives)
- [ ] Favors procedures over declarations
- [ ] Specificity matches fragility: prescriptive for critical steps,
  flexible for judgment calls

### Content Patterns (check for presence where appropriate)
- [ ] Gotchas section - concrete mistakes the agent will make
- [ ] Output templates - structured format, not prose description
- [ ] Checklists for multi-step workflows with validation gates
- [ ] Validation loops - do work, run check, fix, repeat
- [ ] Plan-validate-execute for destructive/batch operations

### Red Flags in Instructions
- "Follow best practices" (which ones?)
- "Handle errors appropriately" (how?)
- "Use the right tool" (which tool, with what flags?)
- Exhaustive coverage of every edge case (agent can judge most)
- No gotchas section (every skill has non-obvious failure modes)

---

## 4. Script Quality (if scripts/ directory exists)

- [ ] No interactive prompts (`input()`, `Read-Host`, etc.)
- [ ] `--help` flag with description, available flags, usage examples
- [ ] Helpful error messages (what went wrong, expected, what to try)
- [ ] Structured output (JSON/CSV on stdout, diagnostics on stderr)
- [ ] Idempotent operations (safe to re-run)
- [ ] Rejects ambiguous input with clear errors
- [ ] `--dry-run` support for destructive operations
- [ ] Meaningful, documented exit codes
- [ ] Safe defaults (destructive ops require explicit flags)
- [ ] Predictable output size (default limit, `--offset` for pagination)
- [ ] Pinned dependency versions
- [ ] Self-contained (inline dependencies, no separate install step)

---

## 5. Evaluation Framework

### Test Cases
- [ ] Eval file exists (e.g., `evals/evals.json`)
- [ ] At least 2-3 test cases defined
- [ ] Test cases vary in phrasing, detail, and complexity
- [ ] Edge cases covered (malformed input, unusual requests, ambiguity)
- [ ] Realistic context in test prompts (not "do the thing")

### Assertions
- [ ] Assertions are specific, observable, and countable
- [ ] No vague assertions ("output is good")
- [ ] No brittle assertions (exact string matches)
- [ ] Grading includes concrete evidence for PASS/FAIL
- [ ] Clear pass threshold defined

### Baseline Comparison
- [ ] With-skill vs without-skill comparison methodology
- [ ] Expected delta documented
- [ ] Assertions that always pass in both configs identified and removed

### Iteration History
- [ ] Multiple refinement rounds completed (or documented plan for them)
- [ ] Changes generalize from feedback (not narrow patches)
- [ ] Human review feedback recorded

---

## 6. Progressive Disclosure

### Token Budget
- [ ] Tier 1 (metadata): ~100 tokens - name + description loaded at startup
- [ ] Tier 2 (instructions): <5000 tokens - SKILL.md body loaded on activation
- [ ] Tier 3 (resources): loaded on demand - reference files, scripts, assets

### Reference Architecture
- [ ] Detailed checklists/guides in `references/`, not inline in SKILL.md
- [ ] SKILL.md references files with clear trigger conditions
  ("See [X] for Y" with context for when to load)
- [ ] Resources listed but NOT eagerly loaded
- [ ] No deeply nested reference chains (reference → reference → reference)

---

## 7. Security Posture (if skill uses tools, MCP, or external data)

_[Ref: OWASP Practical Guide for Secure MCP Server Development v1.0;
OWASP Cheatsheet for Securely Using Third-Party MCP Servers v1.0;
OWASP Top 10 for Agentic Applications 2026]_

### Tool & MCP Safety
- [ ] Tools follow least privilege (no unnecessary file system, network,
  or process access)
- [ ] Tool inputs are validated against schemas before execution
- [ ] No hardcoded secrets or credentials in skill files
- [ ] External data is treated as untrusted (sanitized before use)
- [ ] Destructive operations require explicit user confirmation
- [ ] Shell commands use parameterized inputs (no injection via f-strings
  or string concatenation)
- [ ] Error messages don't expose internal paths, tokens, or stack traces
  _[Ref: OWASP Secure MCP Server Development, Section 6]_

### Agent Behavior Safety
- [ ] Skill instructions constrain agent scope (no open-ended "do anything")
- [ ] High-risk actions are gated behind human approval
  _[Ref: OWASP LLM Top 10 LLM06 - Excessive Agency]_
- [ ] Output is validated before being passed to downstream tools
  _[Ref: OWASP LLM Top 10 LLM05 - Improper Output Handling]_
- [ ] Skill does not instruct the agent to ignore safety guidelines
- [ ] Rate limiting or bounded execution is considered for loops/retries

---

## Compliance Summary Template

| Category | Status | Issues |
|----------|--------|--------|
| Spec conformance (frontmatter, naming, limits) | PASS/PARTIAL/FAIL | {specific issues} |
| Description quality (triggers, intent, keywords) | PASS/PARTIAL/FAIL | {specific issues} |
| Instruction quality (grounded, scoped, calibrated) | PASS/PARTIAL/FAIL | {specific issues} |
| Script quality (if scripts/ exists) | PASS/PARTIAL/FAIL/N/A | {specific issues} |
| Evaluation framework (evals, assertions, baseline) | PASS/PARTIAL/FAIL | {specific issues} |
| Progressive disclosure (tier budget, reference depth) | PASS/PARTIAL/FAIL | {specific issues} |
| Security posture (if tools/MCP/external data) | PASS/PARTIAL/FAIL/N/A | {specific issues} |
