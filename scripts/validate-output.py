"""
Validate shakedown review output completeness.

Checks that a shakedown report contains all required sections,
tables, ratings, and structural elements. Returns pass/fail per check
with a summary score.

Usage:
    python scripts/validate-output.py path/to/review-report.md
"""

import re
import sys
from pathlib import Path


def read_report(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def check_section(text: str, heading: str) -> dict:
    """Check that a markdown heading exists and has content below it."""
    pattern = rf"#+\s*.*{re.escape(heading)}.*"
    # Find ALL matches - some headings are umbrella sections with subsections
    for match in re.finditer(pattern, text, re.IGNORECASE):
        after = text[match.end():]
        next_heading = re.search(r"\n#{1,4}\s", after)
        content = after[:next_heading.start()] if next_heading else after
        content = content.strip()
        if len(content) >= 20:
            return {"pass": True, "reason": f"Section '{heading}' found with content"}
    # Check if any match was found at all
    if re.search(pattern, text, re.IGNORECASE):
        return {"pass": False, "reason": f"Section '{heading}' exists but has minimal content"}
    return {"pass": False, "reason": f"Section '{heading}' not found"}


def check_table(text: str, label: str, min_rows: int = 2) -> dict:
    """Check that a table exists near a heading and has enough data rows."""
    pattern = rf"#+\s*.*{re.escape(label)}.*"
    best_result = None

    # Try all heading matches - skip umbrella headings that have the wrong table
    for match in re.finditer(pattern, text, re.IGNORECASE):
        after = text[match.end():]
        table_match = re.search(r"(\|.+\|[\r\n]+\|[-:\s|]+\|[\r\n]+((?:\|.+\|[\r\n]*)+))", after[:4000])
        if not table_match:
            continue

        rows = [r for r in table_match.group(2).strip().splitlines() if r.strip().startswith("|")]
        empty_rows = sum(1 for r in rows if re.match(r"^\|[\s|.]*\|$", r.strip()))
        if empty_rows == len(rows):
            continue

        if len(rows) >= min_rows:
            return {"pass": True, "reason": f"Table '{label}' found with {len(rows)} data rows"}

        # Track best result in case no match meets min_rows
        if not best_result or len(rows) > best_result[0]:
            best_result = (len(rows), rows)

    if best_result:
        return {"pass": False, "reason": f"Table '{label}' has {best_result[0]} data rows, expected >= {min_rows}"}

    # Fallback: search for label anywhere
    idx = text.lower().find(label.lower())
    if idx == -1:
        return {"pass": False, "reason": f"Table '{label}' section not found"}
    return {"pass": False, "reason": f"No table found near '{label}'"}


def check_rating(text: str) -> dict:
    """Check for an Overall Rating in X/10 format."""
    match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", text)
    if not match:
        return {"pass": False, "reason": "No X/10 rating found"}
    val = float(match.group(1))
    if val < 0 or val > 10:
        return {"pass": False, "reason": f"Rating {val}/10 is out of range"}
    return {"pass": True, "reason": f"Rating {val}/10 found"}


def check_readiness_summary(text: str) -> dict:
    """Check that the Production Readiness section uses PASS/PARTIAL/FAIL status markers.

    The skill no longer issues a ship/no-ship verdict (that call is the user's),
    so we verify the structural signal instead: the readiness section should
    contain at least two of PASS/PARTIAL/FAIL to show gate-by-gate assessment.
    """
    pattern = r"#+\s*.*Production Readiness.*"
    for match in re.finditer(pattern, text, re.IGNORECASE):
        after = text[match.end():match.end() + 6000]
        statuses = ["PASS", "PARTIAL", "FAIL"]
        found = [s for s in statuses if s in after]
        if len(found) >= 2:
            return {"pass": True, "reason": f"Readiness section uses status markers: {', '.join(found)}"}
    return {"pass": False, "reason": "No PASS/PARTIAL/FAIL summary found in Production Readiness section"}


def check_recommendations_columns(text: str) -> dict:
    """Check that the recommendations table has all 4 required columns."""
    required = ["action", "impact", "effort", "who"]
    pattern = r"#+\s*.*(?:Ranked|Recommendation).*"
    # Find the match closest to an actual table (skip umbrella headings)
    for match in re.finditer(pattern, text, re.IGNORECASE):
        after = text[match.end():match.end() + 4000]
        if re.search(r"\|.+\|", after[:500]):
            break
    else:
        return {"pass": False, "reason": "Recommendations section not found"}
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

    # Required sections (present in every review)
    sections = [
        "What the Project Is",
        "What Works Well",
        "Critical Issues",
        "Architecture",
        "Error Handling",
        "Performance",
        "Storage Efficiency",
        "Security",
        "Logging",
        "Documentation Quality",
        "Goal Fulfillment",
        "Blind Spots",
        "Value Assessment",
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

    # Value Assessment table (6 dimensions)
    results.append({"check": "table:Value Assessment", **check_table(text, "Value Assessment", min_rows=4)})

    # Skill Standards table (conditional - only if report covers a skill)
    if re.search(r"(?:skill standards|agent skill|SKILL\.md)", text, re.IGNORECASE):
        results.append({"check": "table:Skill Standards", **check_table(text, "Skill Standards", min_rows=3)})

    # Rating and readiness summary
    results.append({"check": "rating:Overall", **check_rating(text)})
    results.append({"check": "readiness:summary", **check_readiness_summary(text)})

    return results


def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <review-report.md>")
        sys.exit(2)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: file not found: {path}")
        sys.exit(2)

    results = validate(path)

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    print(f"\n{'='*60}")
    print(f"  Shakedown - Output Validation")
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
