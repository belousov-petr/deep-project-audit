# Security & Data Exposure — Reference

Detailed checks for Section 5.1. Run all that apply to the project.

## Secrets & Credentials

- Scan for hardcoded API keys, tokens, passwords, connection strings
- Check .gitignore — are .env, credentials, key files excluded?
- Check git history for accidentally committed secrets
- Are secrets in plaintext or encrypted/vault store?

## Injection Vulnerabilities

- **SQL injection**: user input parameterized or string-concatenated?
- **Prompt injection**: can external data influence LLM system prompts?
- **Command injection**: does any code pass user input to shell commands?
- **Path traversal**: can file paths be manipulated?

## Privacy & PII

- Scan data files and database for PII (names, emails, phone numbers,
  addresses, IPs, financial data, government IDs)
- How is PII stored? Encrypted at rest? Access-controlled?
- Data retention policy? Are old records purged?
- GDPR: right to deletion, portability, consent tracking
- Are logs sanitized or do they contain sensitive data?

## Supply Chain

- Dependencies from trusted sources? Lock files committed?
- Known CVEs? (`npm audit`, `pip audit`, `cargo audit`)
- CI/CD actions pinned to specific versions?

## Workflow Security

- Who can trigger runs? Is there authentication?
- Can a worker escalate privileges or access other workers' data?
- Are webhook endpoints authenticated?

## Network & Infrastructure

- What ports are open? Localhost only or publicly accessible?
- TLS/SSL where needed?
- Rate limits on external services (LLM providers, APIs)
- Peak hour pricing or throttling
