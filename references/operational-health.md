# Operational Health - Reference

Detailed checks for Sections 5.2, 5.3, and 5.5. Evaluates whether the
project can be operated, monitored, and maintained by someone other than
the original author.

---

## Logging & Observability (Section 5.2)

### Log Existence & Location
- Do logs exist? Where are they written? (file, stdout, external service)
- Are all components logging or are some silent?
- Is there a single log aggregation point or scattered across locations?

### Log Quality
- Are logs structured (JSON with fields) or unstructured (free text)?
- Do log entries include: timestamp, severity level, component name,
  correlation/request ID?
- Are errors logged with enough context to diagnose without reproducing?
- Are sensitive values (tokens, PII, passwords) excluded from logs?

### Traceability
- Can you trace a request/signal end-to-end through the system?
- Is there a correlation ID that follows a unit of work across components?
- Can you reconstruct what happened from logs alone after an incident?

### Log Lifecycle
- Is there log rotation? Are old logs purged or do they grow forever?
- What's the retention period? Is it appropriate for debugging needs?
- How much disk space do logs consume? Is it monitored?

### Monitoring & Alerting
- Is there any monitoring dashboard (Grafana, CloudWatch, custom)?
- Are there alerts for critical failures? Who receives them?
- Is there a health check endpoint or heartbeat?
- Can you tell the system is degraded before users report it?
- Are there SLO/SLA metrics being tracked?

---

## Documentation Quality (Section 5.3)

### Accuracy
- Does the README/docs describe what the system actually does today,
  or a past/aspirational version?
- Are code examples in docs still working? (run them to verify)
- Do architecture diagrams match the current codebase?
- Are version numbers, URLs, and commands up to date?

### Completeness
- Could someone else set up this system from the docs alone?
- Could someone else operate it (run, monitor, troubleshoot) from docs?
- Are all configuration options documented?
- Are all environment variables listed with descriptions and defaults?
- Are all external dependencies (APIs, services, databases) documented?

### Maintenance
- When was documentation last updated vs last code change?
- Is there a process for keeping docs in sync? (CI check, review gate)
- Are there docs that reference deleted features or old APIs?

### Onboarding
- Is there a quickstart? Could a new team member get productive in < 1 hour?
- Are prerequisites clearly listed (runtime versions, tools, accounts)?
- Is there a "common problems" or troubleshooting section?
- Are there example commands that can be copy-pasted?

### Stated vs. Actual
- Flag: any doc that describes features that don't exist
- Flag: any implemented feature missing from docs
- Flag: any misleading performance or capability claims

---

## Blind Spots (Section 5.5)

Things nobody is monitoring - the silent risks that accumulate until
they become incidents.

### Feedback & Quality Loops
- Does anyone evaluate the output quality? (human review, automated checks)
- Is there a feedback mechanism? Are feedback results acted on?
- Is output quality degrading over time? Would anyone notice?

### Cost & Resource Tracking
- Is there any cost tracking? (API spend, compute, storage growth)
- Are there budget alerts or spending caps?
- Is resource consumption growing faster than value delivered?
- Are there unused resources still running and costing money?

### SLA & Performance Monitoring
- Are there defined SLAs or targets? Are they being met?
- Is latency/throughput being tracked over time?
- Would anyone notice a 2x slowdown? A 10x slowdown?

### Input Health
- Are data sources reliable? Is freshness monitored?
- What happens when an input source changes format or goes stale?
- Are there integrity checks on incoming data?

### Error Visibility
- Do failures surface to operators or stay silent in logs?
- Is there an error budget? (acceptable failure rate)
- Are recurring errors tracked and prioritized?
- How long between "error occurs" and "human notices"?

### Graceful Degradation
- What happens when one component fails? Does the rest continue?
- Are there fallback paths for non-critical features?
- Does the system communicate its degraded state to users?

### Drift & Rot
- Is configuration drift monitored? (dev vs prod divergence)
- Are dependencies auto-updated or frozen and rotting?
- Is there tech debt tracking? Is it growing or shrinking?
- When was the last time someone reviewed the full system end-to-end?

---

## AI Governance & Compliance Posture (Section 5.6+)

**Conditional - only evaluate if the project uses AI/LLM components.**

_[Ref: OWASP LLM Applications Cybersecurity and Governance Checklist v1.1;
OWASP LLM & GenAI Security Center of Excellence Guide v1.0;
OWASP GenAI Data Security 2026]_

### AI Governance Structure
- Is there an AI RACI chart (responsible, accountable, consulted, informed)?
  _[Ref: OWASP Governance Checklist Section 3.6]_
- Is there an AI policy supported by established organizational policies?
- Is there an acceptable use matrix for GenAI tools?
- Are data management policies enforced technically (not just on paper)?
- Is there a formal AI solution onboarding process?
  _[Ref: OWASP Governance Checklist Section 3.3]_

### AI-Specific Observability
- Are LLM inputs/outputs logged (with PII redaction)?
- Is there monitoring for model performance degradation over time?
- Are token/API consumption metrics tracked and alerting configured?
- Is there anomaly detection on LLM usage patterns (potential abuse)?
- Are AI-specific SLOs defined (latency, accuracy, hallucination rate)?
  _[Ref: OWASP GenAI Red Teaming Guide - Runtime Analysis]_

### AI Risk Management
- Is there an AI asset inventory (models, tools, data sources, owners)?
  _[Ref: OWASP Governance Checklist Section 3.3]_
- Has threat modeling been conducted for AI components?
  _[Ref: OWASP Governance Checklist Section 3.2; Red Teaming Guide Section 4]_
- Are AI-specific incident response playbooks defined?
  _[Ref: OWASP Governance Checklist Section 3.1]_
- Is there a process for AI security training for developers and operators?
  _[Ref: OWASP Governance Checklist Section 3.4]_

### Shadow AI Detection
- Are employees using unapproved AI tools, browser plugins, or
  third-party LLM services?
  _[Ref: OWASP Governance Checklist Section 2 - "Shadow AI" is the
  most pressing non-adversary threat; OWASP GenAI Data Security DSGAI03]_
- Is there technical enforcement preventing data from flowing to
  unapproved AI services?
- Is there visibility into which AI tools are being used across the org?
