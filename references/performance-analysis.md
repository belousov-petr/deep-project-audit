# Performance & Bottleneck Analysis — Reference

Detailed checks for Section 4.6. Quantify everything possible.

## Timing

- How long does each pipeline stage take? Where is time spent?
- What's the end-to-end latency from input to output?
- Are there unnecessary sequential operations that could be parallel?

## Parallelism

- What runs in parallel? What's forced sequential?
- Are there lock contention or race condition risks?
- Could throughput increase with more parallelism?

## Scaling

- What happens at 2x, 10x, 100x current data volume?
- Are there O(n^2) operations hiding in loops?
- Is storage growing linearly or accelerating?

## Resource Waste (Quantified)

- Duplicate processing across pipeline stages
- Empty/low-value items consuming processing time
- Redundant operations (same data read/written multiple times)
- Oversized storage (backups, logs, caches)
- Logic waste: unnecessary steps, over-engineered paths, actions that
  produce no value
- Token/API waste: calls that could be batched, cached, or skipped

## Cost Analysis

- What does this project cost to run per day/week/month?
- For LLM-powered: token/message consumption vs subscription/API budget
- For API-based: external service costs
- For infrastructure: compute, storage, bandwidth
- Is the cost justified by the value delivered?

## Optimization Opportunities

List with estimated impact (e.g., "batch API calls — 40% fewer requests").
