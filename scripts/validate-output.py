"""
Validate audit output completeness.

Checks that a deep-project-audit report contains all required sections,
tables, ratings, and structural elements. Returns pass/fail per check
with a summary score.

Usage:
    python scripts/validate-output.py path/to/audit-report.md
"""

import re
import sys
from pathlib import Path


def read_report(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def check_section(text: str, heading: str) -> dict:
    """Check that a markdown heading exists and has content below it."""
    pattern = rf"#+\s*.*{re.escape(heading)}.*"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return {"pass": False, "reason": f"Section '{heading}' not found"}
    # Check there's content between this heading and the next heading (or EOF)
    after = text[match.end():]
    next_heading = re.search(r"\n#{1,4}\s", after)
    content = after[:next_heading.start()] if next_heading else after
    content = content.strip()
    if len(content) < 20:
        return {"pass": False, "reason": f"Section '{heading}' exists but has minimal content"}
    return {"pass": True, "reason": f"Section '{heading}' found with content"}


def check_table(text: str, label: str, min_rows: int = 2) -> dict:
    """Check that a table exists near a heading and has enough data rows."""
    pattern = rf"#+\s*.*{re.escape(label)}.*"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        # Try finding the table by looking for the label anywhere
        idx = text.lower().find(label.lower())
        if idx == -1:
            return {"pass": False, "reason": f"Table '{label}' section not found"}
        after = text[idx:]
    else:
        after = text[match.end():]

    # Find the first markdown table after the heading
    table_match = re.search(r"(\|.+\|[\r\n]+\|[-:\s|]+\|[\r\n]+((?:\|.+\|[\r\n]*)+))", after[:2000])
    if not table_match:
        return {"pass": False, "reason": f"No table found near '{label}'"}

    rows = [r for r in table_match.group(2).strip().splitlines() if r.strip().startswith("|")]
    if len(rows) < min_rows:
        return {"pass": False, "reason": f"Table '{label}' has {len(rows)} data rows, expected >= {min_rows}"}

    # Check rows aren't all empty (just pipes and spaces)
    empty_rows = sum(1 for r in rows if re.match(r"^\|[\s|.]*\|$", r.strip()))
    if empty_rows == len(rows):
        return {"pass": False, "reason": f"Table '{label}' rows are all empty"}

    return {"pass": True, "reason": f"Table '{label}' found with {len(rows)} data rows"}


def check_rating(text: str) -> dict:
    """Check for an Overall Rating in X/10 format."""
    match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", text)
    if not match:
        return {"pass": False, "reason": "No X/10 rating found"}
    val = float(match.group(1))
    if val < 0 or val > 10:
        return {"pass": False, "reason": f"Rating {val}/10 is out of range"}
    return {"pass": True, "reason": f"Rating {val}/10 found"}


def check_verdict(text: str) -> dict:
    """Check for a production readiness verdict."""
    verdicts = ["ready to ship", "needs", "not production-ready", "not production ready"]
    lower = text.lower()
    for v in verdicts:
        if v in lower:
            return {"pass": True, "reason": f"Verdict found: contains '{v}'"}
    return {"pass": False, "reason": "No production readiness verdict found"}


def check_recommendations_columns(text: str) -> dict:
    """Check that the recommendations table has all 4 required columns."""
    required = ["action", "impact", "effort", "who"]
    pattern = r"#+\s*.*(?:Ranked|Recommendation).*"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return {"pass": False, "reason": "Recommendations section not found"}

    after = text[match.end():match.end() + 2000]
    header_match = re.search(r"\|(.+)\|", after)
    if not header_match:
        return {"pass": False, "reason": "No table header found in recommendations"}

    header = header_match.group(1).lower()
    missing = [col for col in required if col not in header]
    if missing:
        return {"pass": False, "reason": f"Recommendations table missing columns: {', '.join(missing)}"}
    return {"pass": True, "reason": "All required columns present in recommendations table"}


def validate(path: str) -> list:
    text = read_report(path)
    results = []

    # Required sections
    sections = [
        "What the Project Is",
        "What Works Well",
        "Critical Issues",
        "Architecture",
        "Error Handling",
        "Performance",
        "Security",
        "Logging",
        "Documentation Quality",
        "Goal Fulfillment",
        "Blind Spots",
        "Uncomfortable Question",
    ]
    for s in sections:
        results.append({"check": f"section:{s}", **check_section(text, s)})

    # Required tables
    results.append({"check": "table:Objective Clarity", **check_table(text, "Objective Clarity", min_rows=4)})
    results.append({"check": "table:Production Readiness", **check_table(text, "Production Readiness", min_rows=8)})
    results.append({"check": "table:Recommendations", **check_table(text, "Recommendation", min_rows=5)})

    # Column completeness
    results.append({"check": "columns:Recommendations", **check_recommendations_columns(text)})

    # Rating and verdict
    results.append({"check": "rating:Overall", **check_rating(text)})
    results.append({"check": "verdict:Production", **check_verdict(text)})

    return results


def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <audit-report.md>")
        sys.exit(2)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: file not found: {path}")
        sys.exit(2)

    results = validate(path)

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    print(f"\n{'='*60}")
    print(f"  Deep Project Audit — Output Validation")
    print(f"{'='*60}\n")

    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"  [{status}] {r['check']}")
        if not r["pass"]:
            print(f"         {r['reason']}")

    print(f"\n{'='*60}")
    print(f"  Score: {passed}/{total} ({100*passed//total}%)")
    pf = "PASS" if passed / total >= 0.8 else "FAIL"
    print(f"  Result: {pf} (threshold: 80%)")
    print(f"{'='*60}\n")

    sys.exit(0 if pf == "PASS" else 1)


if __name__ == "__main__":
    main()
