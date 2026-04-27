# Code & Storage Efficiency - Reference

Detailed checks for Section 4.7. Quantify everything - counts and bytes.

## Empty Files (0 bytes)

```bash
# Find all zero-byte files (adapt to platform):
find . -type f -empty -not -path './.git/*'
```

- Count total empty files
- Categorize: placeholder `__init__.py` (acceptable) vs forgotten output
  files, broken generation artifacts, empty configs (not acceptable)
- Flag any empty file that has a non-placeholder name

## Duplicate Files

```bash
# Find files with identical content (by hash):
find . -type f -not -path './.git/*' -exec md5sum {} + | sort | uniq -w32 -dD
```

- Count duplicate groups and total wasted bytes
- Check for: same file copied across directories, vendored code that
  should be a dependency, config files with identical content
- Exclude legitimate duplicates (lock files, generated hashes)

## Excessive/Unnecessary Files

Check for files that should not be in the repository:

| Pattern | What it indicates |
|---------|-------------------|
| `*.pyc`, `__pycache__/` | Python bytecode (should be gitignored) |
| `node_modules/` | npm dependencies (should be gitignored) |
| `dist/`, `build/`, `out/` | Build artifacts (should be gitignored) |
| `.DS_Store`, `Thumbs.db` | OS metadata (should be gitignored) |
| `*.tmp`, `*.bak`, `*.swp` | Temporary/backup files |
| `*.log` (large) | Log files that grew unchecked |
| `.env.local`, `.env.*.bak` | Environment file copies |

Check `.gitignore` completeness - are the patterns above covered?

## Code Duplication

- Search for functions/blocks that appear in multiple files with
  minor variations (same logic, different variable names)
- Check for configuration files that are near-identical (e.g.,
  `config.dev.json` vs `config.prod.json` with 95% overlap)
- Look for repeated boilerplate that could be a shared utility

Quantify: estimated lines of duplicated code, number of duplicate groups.

## Dead Dependencies

```bash
# Python: compare requirements vs imports
pip-audit # or: grep -r "import " src/ | sort -u vs requirements.txt

# Node.js: use depcheck or compare package.json vs actual imports
npx depcheck
```

- List declared but unused dependencies
- List imported but undeclared dependencies (implicit/transitive)
- Check for multiple package managers (both `requirements.txt` AND
  `pyproject.toml` with different deps)

## Storage Bloat

```bash
# Large files in repo:
find . -type f -not -path './.git/*' -size +1M -exec ls -lh {} +

# Large files in git history:
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  sort -k3 -n -r | head -20
```

- Flag binary files > 1MB in the repo (images, databases, archives)
- Flag files that should be in LFS or external storage
- Check git history for large objects that inflate clone size
- Check if `.gitattributes` uses LFS where appropriate

## Summary Template

```
Storage Efficiency Summary:
- Empty files: {N} files ({list or "none"})
- Duplicate files: {N} groups, ~{KB/MB} wasted
- Unnecessary files: {N} files that should be gitignored
- Code duplication: ~{N} lines across {N} groups
- Dead dependencies: {N} unused, {N} undeclared
- Storage bloat: {N} files > 1MB, {total size}
- .gitignore completeness: {complete / has gaps}
```
