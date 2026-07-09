#!/usr/bin/env python3
"""Scaffold a new ADR file with the next sequential number and MADR 4.0.0 frontmatter.

Usage:
    python3 scripts/new_adr.py "Decision Title" [--domain Architecture] [--status proposed]

Creates adr/NNNN-<slug>.md from the template, then reminds you to:
  - add a Decision entry to docs/01-facts.md
  - regenerate the index: python3 scripts/gen_adr_index.py && git add docs/adr-index.md
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADR_DIR = os.path.join(REPO, "adr")


def next_number():
    nums = []
    for fn in os.listdir(ADR_DIR):
        m = re.match(r"(\d{4})-", fn)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


def slugify(title):
    slug = re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-").lower()
    return slug or "decision"


VALID_STATUSES = {"proposed", "accepted", "deprecated", "superseded", "rejected"}


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        print('Usage: python3 scripts/new_adr.py "Decision Title" [--domain X] [--status proposed]')
        sys.exit(2)
    title = sys.argv[1]
    domain = "Architecture"
    status = "proposed"
    for i, a in enumerate(sys.argv[2:], 2):
        if a == "--domain" and i + 1 < len(sys.argv):
            domain = sys.argv[i + 1]
        if a == "--status" and i + 1 < len(sys.argv):
            status = sys.argv[i + 1].lower()
    # validate status against the MADR 4.0.0 enum — fail fast at creation time
    if status not in VALID_STATUSES:
        print(f"ERROR: invalid status '{status}'. Must be one of: {sorted(VALID_STATUSES)}", file=sys.stderr)
        sys.exit(2)

    num = next_number()
    slug = slugify(title)
    path = os.path.join(ADR_DIR, f"{num:04d}-{slug}.md")
    # escape any double-quotes in the title so the YAML string stays valid
    safe_title = title.replace('"', '\\"')

    content = f"""---
id: ADR-{num:04d}
title: "{safe_title}"
status: {status}
date: YYYY-MM-DD
deciders: ""
domain: {domain}
---

# ADR-{num:04d}: {title}

## Context

<!-- What is the issue we're facing? What are the constraints and forces? -->

## Options Considered

### Option A: ... (Chosen/Rejected)
- **Pro**:
- **Con**:

### Option B: ...
- **Pro**:
- **Con**:

## Decision

<!-- What did we decide? -->

## Rationale

<!-- Why this option over the others? -->

## Consequences

<!-- What follows from this decision — positive, negative, neutral? -->

## Linked Modules

- `docs/01-facts.md` → Decision #{num} (add me)
- `docs/03-architecture.md` → §N (add me)
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created {path}")
    print("\nNext steps:")
    print(f"  1. Edit the file (fill Context/Options/Decision/Rationale/Consequences/Linked Modules)")
    print(f"  2. Add a '### Decision #{num}: {title}' entry to docs/01-facts.md")
    print(f"  3. Regenerate index: python3 scripts/gen_adr_index.py && git add docs/adr-index.md")


if __name__ == "__main__":
    main()
