#!/usr/bin/env python3
"""One-time migration: prepend MADR 4.0.0 YAML frontmatter to each ADR.

Reads existing inline metadata (`- **Status**:`, `- **Date**:`, `- **Deciders**:`,
optional `- **Domain**:`, optional `- **Supersedes**:`) plus the Domain backfill
from adr/README.md, and writes a frontmatter block above the existing `# ADR-NNNN:`
H1. The decision body is left byte-for-byte unchanged.

Run once, then delete this file (or keep it as a reference). Idempotent: re-running
on an already-migrated file is a no-op (detects leading `---` and skips).

Usage:
    python3 scripts/migrate_adr_frontmatter.py [--apply]
Without --apply it prints a dry-run diff for each file.
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADR_DIR = os.path.join(REPO, "adr")

# Domain backfill source: parse adr/README.md status table once.
def read_domain_map():
    """Return {number_int: domain_str} from the README index table."""
    path = os.path.join(ADR_DIR, "README.md")
    domains = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\|\s*(\d{4})\s*\|[^|]*\|\s*([^|]+?)\s*\|", line)
            if m:
                num = int(m.group(1))
                domain = m.group(2).strip()
                domains[num] = domain
    return domains


def parse_adr(path):
    """Extract (number, title, status, date, deciders, domain, supersedes) from inline metadata."""
    with open(path, encoding="utf-8") as f:
        text = f.read()

    # Title from H1
    m = re.search(r"^#\s*ADR-(\d{4}):\s*(.+)$", text, re.MULTILINE)
    if not m:
        return None
    number = int(m.group(1))
    title = m.group(2).strip()

    status, date, deciders, domain, supersedes = "accepted", "", "", "", ""

    m = re.search(r"\*\*Status\*\*:\s*(.+)$", text, re.MULTILINE)
    if m:
        raw = m.group(1).strip()
        low = raw.lower()
        if low.startswith("accepted"):
            status = "accepted"
        elif low.startswith("superseded"):
            status = "superseded"
        elif low.startswith("deprecated"):
            status = "deprecated"
        elif low.startswith("rejected"):
            status = "rejected"
        elif low.startswith("proposed"):
            status = "proposed"

    m = re.search(r"\*\*Date\*\*:\s*(\d{4}-\d{2}-\d{2})", text)
    if m:
        date = m.group(1)

    m = re.search(r"\*\*Deciders\*\*:\s*(.+)$", text, re.MULTILINE)
    if m:
        deciders = m.group(1).strip()

    m = re.search(r"\*\*Domain\*\*:\s*(.+)$", text, re.MULTILINE)
    if m:
        domain = m.group(1).strip()

    m = re.search(r"\*\*Supersedes\*\*:\s*\[?ADR-(\d{4})", text)
    if m:
        supersedes = "ADR-" + m.group(1)

    # superseded_by from a Superseded status line: "Superseded by [ADR-0012](...)"
    superseded_by = ""
    m = re.search(r"\*\*Status\*\*:\s*Superseded by\s*\[?ADR-(\d{4})", text)
    if m:
        superseded_by = "ADR-" + m.group(1)

    return {
        "number": number,
        "title": title,
        "status": status,
        "date": date,
        "deciders": deciders,
        "domain": domain,
        "supersedes": supersedes,
        "superseded_by": superseded_by,
    }


def build_frontmatter(meta, domain_fallback):
    domain = meta["domain"] or domain_fallback.get(meta["number"], "Uncategorized")
    lines = ["---"]
    lines.append(f"id: ADR-{meta['number']:04d}")
    # Escape any quotes in title/deciders
    title = meta["title"].replace('"', '\\"')
    deciders = meta["deciders"].replace('"', '\\"')
    lines.append(f'title: "{title}"')
    lines.append(f"status: {meta['status']}")
    lines.append(f"date: {meta['date']}")
    lines.append(f'deciders: "{deciders}"')
    lines.append(f"domain: {domain}")
    if meta["supersedes"]:
        lines.append(f"supersedes: {meta['supersedes']}")
    if meta["superseded_by"]:
        lines.append(f"superseded_by: {meta['superseded_by']}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def main():
    apply = "--apply" in sys.argv
    domain_map = read_domain_map()
    files = sorted(
        os.path.join(ADR_DIR, f)
        for f in os.listdir(ADR_DIR)
        if re.match(r"\d{4}-.*\.md$", f)
    )
    migrated = 0
    skipped = 0
    for path in files:
        with open(path, encoding="utf-8") as f:
            original = f.read()
        if original.startswith("---"):
            skipped += 1
            continue
        meta = parse_adr(path)
        if not meta:
            print(f"WARN: could not parse {path}", file=sys.stderr)
            continue
        fm = build_frontmatter(meta, domain_map)
        new_text = fm + "\n" + original
        if apply:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_text)
            migrated += 1
            print(f"  migrated: {os.path.basename(path)}")
        else:
            migrated += 1
            print(f"\n=== {os.path.basename(path)} (dry-run) ===")
            print(fm)
    action = "Migrated" if apply else "Would migrate"
    print(f"\n{action} {migrated} ADR(s); skipped {skipped} already-migrated.")


if __name__ == "__main__":
    main()
