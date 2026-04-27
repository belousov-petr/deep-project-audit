# Resilience Testing - Reference

Detailed guidance for Phase 6. The goal is to verify that safety nets
work, not just that they exist.

**Scope boundary:** This file covers hands-on testing (does recovery
*actually* work). For code-level failure mode analysis, see
`error-resilience.md` (Section 4.5). For live data store queries,
see `db-diagnostics.md` (Phase 3).

## 6a. Backup Validation

**Test it. Don't just note that backups exist.**

1. Find the latest backup file
2. Check its structure (header, footer, completeness)
3. If possible: restore into a temporary location, verify data integrity,
  compare with production, clean up
4. Report: does disaster recovery actually work?

## 6b. Operational Resilience

- Is there a documented recovery procedure?
- Can the system be migrated to a different host?
- What's the recovery time objective?
- Has disaster recovery ever been tested?
