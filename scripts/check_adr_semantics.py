#!/usr/bin/env python3
"""ADR semantic consistency checker for the llm-reporting docs repo.

Pure stdlib. Runs in CI as the authoritative gate for ADR-specific invariants
that no generic tool (lychee, markdownlint, Vale) covers:

  1. ADR numbering is sequential with no gaps or duplicates.
  2. Supersede chains are bidirectionally consistent (A superseded_by B  <=>  B supersedes A).
  3. No non-status reference points at a Superseded/Deprecated/Rejected ADR as if it were active.
  4. §N section references resolve against docs/03-architecture.md's heading tree.
  5. Decision#N entries in docs/01-facts.md correspond to ADR files (count parity).
  6. Derived counts (glossary terms, ADR total) are consistent across the whole repo.
  7. Each ADR contains all MADR required sections.
  8. Each ADR's frontmatter is valid (status enum, date format, non-empty domain).

Exit 0 if all pass, 1 on any failure. Each failure prints file:line + expected vs actual.
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADR_DIR = os.path.join(REPO, "adr")
DOCS_DIR = os.path.join(REPO, "docs")

VALID_STATUSES = {"proposed", "accepted", "deprecated", "superseded", "rejected"}
MADR_SECTIONS = ["Context", "Decision", "Rationale", "Consequences", "Linked Modules"]
# "Options Considered" is commonly present but not strictly required; not enforced.

errors = []


def err(check, location, msg):
    errors.append(f"FAIL [{check}] {location} — {msg}")


# --- helpers -----------------------------------------------------------------

def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def parse_frontmatter(text):
    """Return (fm_dict, body) or ({}, text) if no frontmatter."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fm_raw = text[4:end]
    body = text[end + 5:]
    fm = {}
    for line in fm_raw.splitlines():
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"')
    return fm, body


def load_adrs():
    """Return list of dicts: {num, path, fm, body}."""
    adrs = []
    for fn in sorted(os.listdir(ADR_DIR)):
        if not re.match(r"\d{4}-.*\.md$", fn) or fn == "README.md":
            continue
        path = os.path.join(ADR_DIR, fn)
        text = read(path)
        fm, body = parse_frontmatter(text)
        m = re.match(r"(\d{4})", fn)
        if m:
            adrs.append({"num": int(m.group(1)), "path": path, "fm": fm, "body": body})
    return adrs


# --- checks ------------------------------------------------------------------

def check_numbering(adrs):
    nums = sorted(a["num"] for a in adrs)
    # gaps (missing numbers in the 1..N sequence)
    for i, n in enumerate(nums):
        if i + 1 != n:
            err("numbering", "adr/", f"gap in sequence: expected ADR-{i+1:04d}, found ADR-{n:04d}")
            break
    # duplicates
    seen = set()
    for a in adrs:
        if a["num"] in seen:
            err("numbering", os.path.basename(a["path"]), f"duplicate ADR-{a['num']:04d}")
        seen.add(a["num"])


def check_supersede_bidirectional(adrs):
    by_id = {f"ADR-{a['num']:04d}": a for a in adrs}
    for a in adrs:
        aid = f"ADR-{a['num']:04d}"
        sb = a["fm"].get("superseded_by", "")
        sp = a["fm"].get("supersedes", "")
        # forward: if A superseded_by B, then B supersedes A
        if sb:
            target = by_id.get(sb)
            if not target:
                err("supersede", os.path.basename(a["path"]),
                    f"superseded_by {sb} but no such ADR exists")
            elif target["fm"].get("supersedes") != aid:
                err("supersede", os.path.basename(target["path"]),
                    f"{sb} should have 'supersedes: {aid}' (currently '{target['fm'].get('supersedes','')}')")
        # reverse: if A supersedes B, then B superseded_by A
        if sp:
            target = by_id.get(sp)
            if not target:
                err("supersede", os.path.basename(a["path"]),
                    f"supersedes {sp} but no such ADR exists")
            elif target["fm"].get("superseded_by") != aid:
                err("supersede", os.path.basename(target["path"]),
                    f"{sp} should have 'superseded_by: {aid}' (currently '{target['fm'].get('superseded_by','')}')")


def check_reverse_refs(adrs):
    """Flag non-status references to superseded/deprecated/rejected ADRs.

    A 'non-status reference' is a prose mention that treats the retired ADR as a
    live decision — e.g. "per ADR-0004, the structure is...". We exclude:
      - the retired ADR's own file (it legitimately describes itself)
      - the supersession partner's file (0012 must reference 0004)
      - lines containing status/supersede vocabulary
      - the ADR index (adr/README.md, docs/adr-index.md) which lists statuses
    """
    retired = {a["num"]: a for a in adrs if a["fm"].get("status") in {"superseded", "deprecated", "rejected"}}
    if not retired:
        return
    # map: which files are "involved" in each retired ADR and thus exempt
    involved = {}  # adr_num -> set of paths allowed to reference it
    for a in adrs:
        sb = a["fm"].get("superseded_by", "")
        sp = a["fm"].get("supersedes", "")
        if a["fm"].get("status") in {"superseded", "deprecated", "rejected"}:
            involved.setdefault(a["num"], set()).add(a["path"])
        if sb:
            tnum = int(sb.split("-")[1])
            involved.setdefault(tnum, set()).add(a["path"])
        if sp:
            tnum = int(sp.split("-")[1])
            involved.setdefault(tnum, set()).add(a["path"])
    index_files = {
        os.path.join(ADR_DIR, "README.md"),
        os.path.join(DOCS_DIR, "adr-index.md"),
        os.path.join(DOCS_DIR, "cross-reference-checklist.md"),
    }
    scan_files = []
    for root, _, files in os.walk(DOCS_DIR):
        for f in files:
            if f.endswith(".md"):
                scan_files.append(os.path.join(root, f))
    scan_files.append(os.path.join(REPO, "README.md"))
    scan_files.append(os.path.join(ADR_DIR, "README.md"))
    for a in adrs:
        scan_files.append(a["path"])
    for sf in scan_files:
        if sf in index_files:
            continue
        try:
            text = read(sf)
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            if any(k in low for k in ("superseded", "supersedes", "status", "retired", "deprecated", "replaced by")):
                continue
            for num, retired_adr in retired.items():
                tag = f"ADR-{num:04d}"
                if tag in line and sf not in involved.get(num, set()):
                    err("reverse-ref", f"{sf}:{i}",
                        f"references retired {tag} (status={retired_adr['fm'].get('status')}) as if active")


def check_section_refs(adrs):
    """Resolve §N refs against docs/03-architecture.md heading tree.

    Scoped: only validate §N tokens that appear to be architecture cross-refs.
    Regulatory clauses (HIPAA 45 CFR §164, SOX §302/§404), cost-doc self-refs
    (§2.2.1), and similar are excluded via context heuristics:
      - skip lines mentioning regulatory/law vocab (HIPAA, SOX, GDPR, CFR, GDPR)
      - skip §N inside docs that have their own numbering (cost/timeline/glossary
        cross-ref their own sections) — only ADR files and docs/01-facts.md,
        docs/03-architecture.md index pointers are checked.
    """
    arch_path = os.path.join(DOCS_DIR, "03-architecture.md")
    try:
        arch = read(arch_path)
    except OSError:
        err("section-ref", arch_path, "03-architecture.md not found")
        return
    valid = set()
    for m in re.finditer(r"^#{2,4}\s+([0-9]+[A-Z]?(?:\.[0-9]+)*)", arch, re.MULTILINE):
        valid.add(m.group(1))
    valid |= {v.split(".")[0].rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for v in valid}

    # Only check files whose §N refs target the architecture doc:
    # ADRs (Linked Modules), 01-facts.md (decision pointers). Cost/timeline/
    # glossary use §N for their OWN sections or regulatory clauses — skip them.
    scan = [a["path"] for a in adrs]
    scan.append(os.path.join(DOCS_DIR, "01-facts.md"))
    scan.append(os.path.join(ADR_DIR, "README.md"))
    regulatory = ("hipaa", "sox", "gdpr", "ccpa", "cfr", "european union", "regulation")
    ref_re = re.compile(r"§([0-9]+[A-Z]?(?:\.[0-9]+)*)")
    for sf in scan:
        try:
            text = read(sf)
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            if any(k in low for k in regulatory):
                continue
            for m in ref_re.finditer(line):
                token = m.group(1)
                if token in valid:
                    continue
                if any(v == token or v.startswith(token + ".") for v in valid):
                    continue
                # §22X-style refs: allow if the top section exists (22) and it's a lettered sub
                err("section-ref", f"{sf}:{i}",
                    f"§{token} does not resolve to any heading in 03-architecture.md")


def check_decision_parity(adrs):
    """Decision #N entries in 01-facts.md must match ADR file count.

    Decision numbers are a narrative sequence (NOT 1:1 with ADR numbers), so we
    enforce count parity + unique-ascending-integer numbering. A `#7b`-style
    suffix is a legacy wart that should not recur.
    """
    facts_path = os.path.join(DOCS_DIR, "01-facts.md")
    try:
        text = read(facts_path)
    except OSError:
        err("decision-parity", facts_path, "01-facts.md not found")
        return
    raw_tokens = re.findall(r"^###\s+Decision\s+#(\w+)", text, re.MULTILINE)
    # every token must be a plain integer (no '7b', '3a', etc.)
    for tok in raw_tokens:
        if not re.fullmatch(r"\d+", tok):
            err("decision-parity", facts_path,
                f"Decision #{tok} has a non-integer suffix — use a plain integer (legacy wart); add a properly numbered entry instead")
    int_tokens = [int(t) for t in raw_tokens if re.fullmatch(r"\d+", t)]
    # uniqueness
    if len(int_tokens) != len(set(int_tokens)):
        dups = sorted({n for n in int_tokens if int_tokens.count(n) > 1})
        err("decision-parity", facts_path,
            f"duplicate Decision numbers: {dups} — numbers must be unique")
    adr_count = len(adrs)
    if len(raw_tokens) != adr_count:
        err("decision-parity", facts_path,
            f"{len(raw_tokens)} Decision entries vs {adr_count} ADRs — count must match")


def check_readme_index(adrs):
    """adr/README.md index table rows must equal ADR files on disk.

    Prevents silent drift: if someone adds an ADR and regenerates
    docs/adr-index.md but forgets adr/README.md, this catches it.
    """
    readme_path = os.path.join(ADR_DIR, "README.md")
    try:
        text = read(readme_path)
    except OSError:
        return  # README absence is not itself an error
    # table rows look like: | 0001 | [Title](./0001-...md) | ...
    readme_nums = set()
    for m in re.finditer(r"^\|\s*(\d{4})\s*\|", text, re.MULTILINE):
        readme_nums.add(int(m.group(1)))
    disk_nums = {a["num"] for a in adrs}
    missing_in_readme = disk_nums - readme_nums
    extra_in_readme = readme_nums - disk_nums
    if missing_in_readme:
        err("readme-index", readme_path,
            f"ADRs on disk but missing from README table: {sorted(missing_in_readme)}")
    if extra_in_readme:
        err("readme-index", readme_path,
            f"ADRs in README table but no file on disk: {sorted(extra_in_readme)}")


def check_counts(adrs):
    """Derived counts consistent across repo (active mentions only).

    We only flag claims that are clearly *total* counts, not per-domain sub-totals,
    skill IDs (S16 ADRGenerator), historical changelog entries, or years (2011 ADR).
    A claim qualifies when it reads like "N ADRs (summary)" / "(N records)" /
    "Total Terms: N" / "complete glossary (N terms)" — i.e. with a total-qualifier.
    """
    # --- glossary term count ---
    gloss_path = os.path.join(DOCS_DIR, "glossary.md")
    gloss = read(gloss_path)
    rows = [l for l in gloss.splitlines() if l.startswith("| ")]
    terms = [r for r in rows if not re.match(r"\|\s*Term\s*\|", r) and not re.match(r"\|\s*-+", r)]
    true_term_count = len(terms)
    # only "complete/total glossary (N terms)" or "Total Terms: N" qualify as totals
    total_term_re = re.compile(r"(?:complete glossary|Total Terms)\s*\(?\s*(\d+)\s+terms\)?|Total Terms:\s*(\d+)")
    for root, _, files in os.walk(DOCS_DIR):
        for f in files:
            if not f.endswith(".md"):
                continue
            p = os.path.join(root, f)
            t = read(p)
            for i, line in enumerate(t.splitlines(), 1):
                for m in total_term_re.finditer(line):
                    claimed = int(m.group(1) or m.group(2))
                    if claimed != true_term_count:
                        err("count-glossary", f"{p}:{i}",
                            f"claims {claimed} terms, actual is {true_term_count}")
    # also the header banner "(N terms)" in 01-facts.md line 7
    for root, _, files in os.walk(DOCS_DIR):
        for f in files:
            if f != "01-facts.md":
                continue
            p = os.path.join(root, f)
            t = read(p)
            for i, line in enumerate(t.splitlines(), 1):
                if "glossary.md" in line and "(N terms)" not in line:
                    m = re.search(r"\((\d+)\s+terms\)", line)
                    if m and int(m.group(1)) != true_term_count:
                        err("count-glossary", f"{p}:{i}",
                            f"claims {m.group(1)} terms, actual is {true_term_count}")

    # --- ADR total count ---
    # Only "N ADRs (summary)", "(N records)", or "all N ADRs" qualify as total claims.
    true_adr = len(adrs)
    total_adr_re = re.compile(
        r"(\d+)\s+ADRs?\s+\(summary\)"           # "24 ADRs (summary)"
        r"|\((\d+)\s+records\)"                    # "(24 records)"
        r"|all\s+(\d+)\s+ADRs"                     # "all 24 ADRs"
        r"|ADR.*\((\d+)\s+records\)"               # "ADR → adr/ (24 records)"
    )
    for root, _, files in os.walk(DOCS_DIR):
        for f in files:
            if not f.endswith(".md"):
                continue
            p = os.path.join(root, f)
            t = read(p)
            for i, line in enumerate(t.splitlines(), 1):
                for m in total_adr_re.finditer(line):
                    claimed = int(next(g for g in m.groups() if g))
                    if claimed != true_adr:
                        err("count-adr", f"{p}:{i}",
                            f"claims {claimed} ADRs, actual is {true_adr}")


def check_madr_sections(adrs):
    for a in adrs:
        for sec in MADR_SECTIONS:
            if not re.search(rf"^##\s+{re.escape(sec)}", a["body"], re.MULTILINE):
                err("madr-sections", os.path.basename(a["path"]),
                    f"missing required section '## {sec}'")


def check_frontmatter_validity(adrs):
    for a in adrs:
        fm = a["fm"]
        loc = os.path.basename(a["path"])
        if not fm:
            err("frontmatter", loc, "no frontmatter found")
            continue
        status = fm.get("status", "")
        if status not in VALID_STATUSES:
            err("frontmatter", loc, f"invalid status '{status}' (not in {sorted(VALID_STATUSES)})")
        if not re.match(r"\d{4}-\d{2}-\d{2}$", fm.get("date", "")):
            err("frontmatter", loc, f"invalid/missing date '{fm.get('date','')}'")
        if not fm.get("domain"):
            err("frontmatter", loc, "missing domain")
        if not fm.get("title"):
            err("frontmatter", loc, "missing title")


def main():
    adrs = load_adrs()
    check_numbering(adrs)
    check_supersede_bidirectional(adrs)
    check_reverse_refs(adrs)
    check_section_refs(adrs)
    check_decision_parity(adrs)
    check_readme_index(adrs)
    check_counts(adrs)
    check_madr_sections(adrs)
    check_frontmatter_validity(adrs)

    if errors:
        print(f"\n{'='*60}")
        print(f"FAIL — {len(errors)} problem(s) found:\n")
        for e in errors:
            print(f"  {e}")
        print(f"\n{'='*60}")
        sys.exit(1)
    print("OK — all ADR semantic checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
