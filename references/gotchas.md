# Review Gotchas - Reference

Common mistakes agents make during project reviews. These are not generic
advice - each one is a failure mode observed in real review outputs. Read
before starting Phase 4.

---

## 1. Praising by Default

**The mistake:** Opening with "this is a well-structured project" or
"the codebase is clean and well-organized" before having evidence.

**Why it happens:** Agents default to polite, constructive tone. Most
training data rewards positive framing.

**The fix:** Start neutral. Let evidence shape tone. If the project
genuinely deserves praise, the evidence will make it obvious - cite
the specific file, pattern, or decision that's good. "The retry logic
in `worker.py:84` uses exponential backoff with jitter - correct
approach for rate-limited APIs" is praise with evidence.

---

## 2. Listing Features Instead of Evaluating Them

**The mistake:** "The project has retry logic, error handling, and
logging." This tells the reader nothing about quality.

**Why it happens:** Reading a file and noting what exists is easier
than evaluating whether it works correctly.

**The fix:** Every claim needs a judgment:
- BAD: "The project has retry logic"
- GOOD: "The retry logic in `worker.py:84` retries 3 times with no
  backoff and no jitter, which will hammer a rate-limited API during
  outages. Should use exponential backoff."

---

## 3. Skipping File Reads and Guessing from Names

**The mistake:** Seeing `security.py` and writing "security handling
is implemented in `security.py`" without reading it. The file might
be empty, contain unrelated code, or have placeholder TODO comments.

**Why it happens:** File names suggest content. Agents try to be
efficient and skip reads when the name seems clear.

**The fix:** Read before judging. A file called `security.py` might
contain nothing security-related. A file called `utils.py` might
contain the entire business logic. Never reference a file you
haven't read in this session.

---

## 4. Treating README as Ground Truth

**The mistake:** Reporting features from the README as if they exist
in the codebase without verification.

**Why it happens:** README is usually the first file read. It's
written by the author. It feels authoritative.

**The fix:** README describes intent. Code describes reality. When
they disagree, the code is right. Always cross-reference README
claims against actual files. Section 5.4 (Goal Fulfillment) exists
specifically to surface these gaps.

---

## 5. Shallow Security Scanning

**The mistake:** Grepping for "password" or "secret", finding nothing,
and declaring the project secure.

**Why it happens:** Deep security analysis is hard. Surface checks
feel thorough because they produce results quickly.

**The fix:** Check for:
- Hardcoded tokens in non-.env files (API keys in config, tokens in
  source code, credentials in YAML)
- Injectable template strings (f-strings or string concatenation in
  SQL queries, shell commands, or prompt templates)
- Unvalidated user input passed to shell commands (subprocess with
  unsanitized args)
- Overly broad CORS (Access-Control-Allow-Origin: *)
- Missing authentication on endpoints
- Dependencies with known CVEs (check package versions)
- Secrets in git history (even if removed from current files)

See `references/security-checklist.md` for the full list.

---

## 6. Ignoring Cost

**The mistake:** Reviewing functionality, security, and architecture
but never asking "what does this cost to run?"

**Why it happens:** Cost isn't a code quality metric. It feels like
a business concern, not a technical one.

**The fix:** Every review should estimate operational cost:
- LLM-powered projects: token/message consumption per run, monthly
  burn rate vs subscription/API budget
- API-dependent projects: external service costs, rate limits
- Infrastructure: compute, storage, bandwidth, database hosting
- Hidden costs: manual intervention time, monitoring overhead

An architecture that works perfectly but costs 10x what it should
is still a critical finding.

---

## 7. Generic Recommendations

**The mistake:** "Add more tests." "Improve documentation." "Consider
adding monitoring." These are useless because they don't tell the
reader what specifically to do.

**Why it happens:** Being specific requires understanding the project
deeply enough to point at exact gaps. Generic advice is safe and
always technically correct.

**The fix:** Every recommendation must answer: what, where, why, and
how much effort:
- BAD: "Add more tests"
- GOOD: "Add integration tests for the payment flow in `checkout.py`
 - it has zero test coverage and handles money. Effort: 2-4 hours.
  Can be done by the system's own test agent."

---

## 8. Forgetting to Check Scale

**The mistake:** Testing behavior with current data volume and
declaring it works. Never asking "what happens with 10x or 100x?"

**Why it happens:** The project works now. Scaling concerns feel
hypothetical and speculative.

**The fix:** For every data path, ask:
- Current volume: N items. What happens at 10N? 100N? 1000N?
- Are there O(n^2) operations hidden in loops?
- Are there unbounded lists, unlimited retries, or uncapped queues?
- Is storage growing linearly or accelerating?
- Where does it break first?

This isn't speculative - it's engineering. The answer might be "it
breaks at 10x, and that's fine because 10x is 5 years away." But
the review should surface it.

---

## 9. Conflating Existence with Quality

**The mistake:** "Error handling is in place" because try/catch blocks
exist. But the catch block might swallow errors silently, retry
infinitely, or log without context.

**Why it happens:** Checking that something exists is a quick
pass/fail. Evaluating whether it works correctly requires tracing
the full behavior.

**The fix:** For every mechanism you find (error handling, retry
logic, validation, auth), trace the actual behavior:
- What triggers it?
- What happens when it triggers?
- Does the outcome match the intent?
- What's the failure mode of the mechanism itself?

---

## 10. Reporting Only What Was Asked

**The mistake:** If the user says "review the backend," only looking
at backend code - missing that the frontend exposes an admin panel
with no auth, or that the CI/CD pipeline has hardcoded secrets.

**Why it happens:** Agents follow instructions literally. Staying
in scope feels responsible.

**The fix:** Phase 1 confirms scope with the user. But within that
scope, look at everything that interacts with the target - config,
CI/CD, deployment, infrastructure, documentation, and adjacent
components. A backend review that misses the deployment pipeline
deploying to production without tests is incomplete.
