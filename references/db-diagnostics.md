# Data Store Diagnostics - Reference

Detailed guidance for Phase 3 database inspection. Adapt to whatever
data store the project uses.

**Scope boundary:** This file covers live queries against data stores
(what the data *actually* looks like). For code-level failure mode
analysis, see `error-resilience.md` (Section 4.5). For hands-on
backup restore testing, see `resilience-testing.md` (Phase 6).

## 3a. Find Connection Credentials

- Check config files, .env, source code for connection strings
- For embedded databases, trace from running processes to find binaries and auth

## 3b. Query Operational Metrics

Adapt queries to whatever database exists:

### SQL Databases (PostgreSQL, SQLite, MySQL)

```sql
-- Schema overview: what tables exist and how big are they?
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- If there are agent/run/job tables, get reliability stats:
-- Success rate, failure rate, average duration per agent/worker

-- Recent failures with error details

-- Data freshness: when was the last write to key tables?
```

### File-Based Data Stores

Count files per directory, check modification dates. Identify stale
data (last modified > expected interval). Check for schema consistency
across sample files.

### NoSQL Databases

- Collection sizes, document counts
- Index health
- Recent error logs
