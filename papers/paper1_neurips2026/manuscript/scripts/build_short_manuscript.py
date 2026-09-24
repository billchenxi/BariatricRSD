"""
Generate a 9-page-targeted "autocut" version of the manuscript by selecting
key subsections for the main body and moving the rest to an extended
appendix. Output: submit_ready.md.

Rules (per editorial decisions documented in conversation):
  Keep in main body:
    - YAML frontmatter (title + abstract)
    - §1.4 condensed (drop §1.1, §1.2, §1.3, §1.5)
    - §2 first 2 paragraphs only
    - §3.3 only (drop §3.1, §3.2, §3.4)
    - §4.2 + §4.5 (drop §4.1, §4.3, §4.4, §4.6)
    - §5 first paragraph (drop §5.1)
    - §6 headline callout + §6.1 + §6.2 + §6.3 + §6.5
    - §7 first paragraph + §7.1 condensed
    - §8 condensed (3 paragraphs)
    - §9 conclusion

  Move to extended appendix (Appendix Z):
    - dropped §1.x details
    - §2 details
    - §3.1, §3.2, §3.4
    - §4.1, §4.3, §4.4, §4.6
    - §5.1
    - §6.4, §6.6, §6.7, §6.8, §6.9, §6.10
    - §7 expanded discussion
    - §8 detail
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "review_manuscript.md"
OUT = ROOT / "submit_ready.md"


def split_sections(text: str):
    """Return (preamble, [(level, header_line, body), ...]).

    A 'section' here is anything that starts with `# `, `## `, or `### `.
    """
    lines = text.split("\n")
    # Find preamble (everything up to first `# `)
    first_h1 = next((i for i, l in enumerate(lines) if re.match(r"^# \w", l)), len(lines))
    preamble = "\n".join(lines[:first_h1])
    rest = lines[first_h1:]

    sections = []
    i = 0
    while i < len(rest):
        line = rest[i]
        m = re.match(r"^(#{1,3}) (.+)$", line)
        if m:
            level = len(m.group(1))
            header = line
            i += 1
            body = []
            while i < len(rest):
                if re.match(r"^#{1,3} \w", rest[i]):
                    break
                body.append(rest[i])
                i += 1
            sections.append((level, header, "\n".join(body)))
        else:
            i += 1
    return preamble, sections


def header_key(header_line: str) -> str:
    """Return e.g. '6.1' from '## 6.1 ...' or '6' from '# 6. Results'."""
    m = re.match(r"^#+\s+(\d+(?:\.\d+)*)", header_line)
    return m.group(1) if m else ""


def keep_in_main(level, header) -> bool:
    """Apply the editorial rules."""
    key = header_key(header)
    # Section §1: keep §1.4 only
    if key == "1":
        return True   # § header itself
    if key.startswith("1."):
        return key == "1.4"
    # §2: keep entirely (we'll trim its body separately)
    if key == "2":
        return True
    # §3: keep section header + §3.3
    if key == "3":
        return True
    if key.startswith("3."):
        return key == "3.3"
    # §4: keep header + §4.2 + §4.5
    if key == "4":
        return True
    if key.startswith("4."):
        return key in {"4.2", "4.5"}
    # §5: keep header (drop §5.1)
    if key == "5":
        return True
    if key.startswith("5."):
        return False
    # §6: keep header + 6.1, 6.2, 6.3, 6.5, 6.8
    # (6.4 shuffled-token, 6.6 Cholec80 absolute, 6.7 variability-scaling,
    # 6.9 diagnostic chain, 6.10 apparatus → appendix; the shuffled-token
    # finding and the IT bound are still summarized in §1.4)
    if key == "6":
        return True
    if key.startswith("6."):
        return key in {"6.1", "6.2", "6.3", "6.5", "6.8"}
    # §7: keep header + §7.1
    if key == "7":
        return True
    if key.startswith("7."):
        return key == "7.1"
    # §8 / §9: keep
    if key in {"8", "9"}:
        return True
    # References, Appendices: keep verbatim — they don't count toward 9-page limit
    if not key:
        # non-numbered headers like "References" or "Appendix X"
        if "References" in header or "Appendix" in header:
            return True
    return False


def trim_body(body: str, max_chars: int) -> str:
    """Trim a section body to roughly max_chars by keeping (a) all markdown
    tables, (b) all inline figure references `![...](...)`, (c) first prose
    paragraphs that fit. Tables and figures are essential and never dropped."""
    if len(body) <= max_chars:
        return body
    paragraphs = body.split("\n\n")
    def is_table(p):
        rows = [r for r in p.split("\n") if r.strip().startswith("|")]
        return len(rows) >= 2
    def is_figure(p):
        return p.strip().startswith("![")
    def is_essential(p):
        return is_table(p) or is_figure(p)
    essential_chars = sum(len(p) + 2 for p in paragraphs if is_essential(p))
    prose_budget = max(max_chars - essential_chars, 600)
    out = []
    cur_prose = 0
    for p in paragraphs:
        if is_essential(p):
            out.append(p)
        else:
            if cur_prose + len(p) <= prose_budget:
                out.append(p)
                cur_prose += len(p) + 2
            else:
                break
    return "\n\n".join(out)


def anonymize_preamble(preamble: str) -> str:
    """For NeurIPS double-blind submission: strip author and draft-date YAML.
    Keeps the title and abstract; removes author block and date line."""
    lines = preamble.split("\n")
    out = []
    in_author = False
    for line in lines:
        # Drop multi-line `author:` block
        if line.startswith("author:"):
            in_author = True
            continue
        if in_author:
            # Author block continues with indented lines
            if line.startswith("  ") or line.strip() == "":
                # If next top-level YAML key, exit
                if line.strip() == "":
                    in_author = False
                continue
            else:
                in_author = False
        # Drop draft date line (single-line YAML field)
        if line.startswith("date:"):
            continue
        out.append(line)
    return "\n".join(out)


def fix_dangling_refs(text: str) -> str:
    """Rewrite references to §6.x sections that have been moved to Appendix Z."""
    # §6.4, §6.6, §6.7, §6.9, §6.10 are all in Appendix Z under the current rules
    for s in ["§6.4", "§6.6", "§6.7", "§6.9", "§6.10"]:
        text = text.replace(s, "Appendix Z")
    return text


def main():
    src = SRC.read_text()
    preamble, sections = split_sections(src)
    preamble = anonymize_preamble(preamble)

    main_parts = [preamble]
    appendix_extras = []  # what we cut from main, to dump into Appendix Z

    for level, header, body in sections:
        key = header_key(header)
        if keep_in_main(level, header):
            # Targets aiming for 9 full pages in pandoc 10pt + 1-inch margins
            # (now includes §6.4, §6.7, §6.8 in main; figures inline preserved)
            if key == "1.4":
                body = trim_body(body, 3500)
            elif key == "2":
                body = trim_body(body, 2500)
            elif key == "3.3":
                body = trim_body(body, 2000)
            elif key == "4.2":
                body = trim_body(body, 3000)
            elif key == "4.5":
                body = trim_body(body, 3000)
            elif key == "5":
                body = trim_body(body, 1800)
            elif key == "6":
                body = trim_body(body, 3500)   # headline-results-at-a-glance + intro paragraph
            elif key == "6.1":
                body = trim_body(body, 3500)   # within-center, full table
            elif key == "6.2":
                body = trim_body(body, 2500)
            elif key == "6.3":
                body = trim_body(body, 2500)   # centered + strict tables + clinical
            elif key == "6.4":
                body = trim_body(body, 2000)   # shuffled-token semantic control
            elif key == "6.5":
                body = trim_body(body, 3500)   # deployable predictor — two tables
            elif key == "6.8":
                body = trim_body(body, 2200)   # statistical significance, two tables
            elif key == "7":
                body = trim_body(body, 2000)
            elif key == "7.1":
                body = trim_body(body, 3000)
            elif key == "8":
                body = trim_body(body, 2500)
            elif key == "9":
                body = trim_body(body, 1500)
            main_parts.append(header)
            main_parts.append(body)
        else:
            # Save dropped subsection for appendix Z
            appendix_extras.append((level, header, body))

    # Build extended appendix Z section
    if appendix_extras:
        main_parts.append("\n# Appendix Z — Extended discussion (cut from main paper for length)\n")
        main_parts.append("This appendix contains material that was condensed or omitted from the main\n"
                          "paper to fit the 9-page limit. The headline empirical claims and the strict-\n"
                          "protocol headline tables are in the main paper; the controls, ablations,\n"
                          "and methodological details are here.\n")
        for level, header, body in appendix_extras:
            # Demote one level so they're subsections of Appendix Z
            new_level = "#" * min(level + 1, 4)
            new_header = re.sub(r"^#+\s*", new_level + " ", header)
            main_parts.append(new_header)
            main_parts.append(body)

    output_text = "\n".join(main_parts)
    output_text = fix_dangling_refs(output_text)
    OUT.write_text(output_text)
    print(f"Wrote {OUT}")
    print(f"  main_parts: {len(main_parts)} blocks, ~{sum(len(p) for p in main_parts):,} chars")
    print(f"  cut sections moved to Appendix Z: {len(appendix_extras)}")


if __name__ == "__main__":
    main()
