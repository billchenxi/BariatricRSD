"""
Build a standalone supplementary markdown file containing everything from
the full manuscript that is NOT in the 9-page short version.

The submit_ready.md already includes everything (main body + appendices +
references), but this script extracts only the supplementary half so it
can be uploaded as a separate document or reviewed in isolation.

Output:
  paper/submit_ready_supplementary.md
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUBMIT_MD = ROOT / "submit_ready.md"
OUT = ROOT / "submit_ready_supplementary.md"


def main():
    text = SUBMIT_MD.read_text()

    # Strip YAML frontmatter
    text = re.sub(r"^---\n.*?\n---\n+", "", text, count=1, flags=re.DOTALL)

    # Find the start of the supplementary content (References + Appendices).
    # Everything from "# References" onward is the supplementary half.
    refs_start = text.find("# References")
    if refs_start < 0:
        raise SystemExit("ERROR: could not find '# References' marker")
    supplementary = text[refs_start:]

    # Prepend a YAML + title page describing what this is.
    header = """---
title: "Supplementary Material: When Does Workflow Conditioning Help \
Remaining Surgery Duration Prediction? A Variability-Scaling Study on \
MultiBypass140 and Cholec80"
---

# Supplementary Material

This document accompanies the main 9-page paper. It contains the
references and the full appendix set:

- **Appendix A** — Implementation details (offline phase clustering, training stack, loss formulation).
- **Appendix B** — Hyperparameter sensitivity studies (cluster K, soft-cluster posterior temperature τ, Adam-style smoother).
- **Appendix C** — Per-fold and per-seed tables (5-fold × 3-seed extension under the strict prefix-only protocol; bootstrap CIs; metric reconciliation).
- **Appendix D** — Negative result: per-video overfit-residual frame filtering damages a modern ViT + HTA pipeline.
- **Appendix E** — Failure modes (qualitative video-level error analysis).
- **Appendix F** — Shuffled-token semantic control (apparatus + result that the gain reflects real workflow information).
- **Appendix Z** — Extended discussion (sections condensed or cut from the main paper for the 9-page limit, including §1.x intro material, §2 expanded related work, §3.x dataset details, §4.x method details, §5.1 hyperparameter table, §6.4/6.6/6.7/6.9/6.10 additional results, and §7/§8 expanded discussion).

No headline empirical claim from the main paper depends on material
here; this document is for reviewer-side reproducibility, ablations,
statistical-significance tests, and methodological transparency.
Section numbering and cross-references follow the main paper.

---

"""
    OUT.write_text(header + supplementary)
    n_appendices = len(re.findall(r"^# Appendix", supplementary, flags=re.MULTILINE))
    n_refs = len(re.findall(r"^\d+\.\s", supplementary, flags=re.MULTILINE))
    size_kb = OUT.stat().st_size / 1024
    print(f"Wrote {OUT}")
    print(f"  {size_kb:.1f} KB, {n_appendices} appendices, ~{n_refs} reference entries")


if __name__ == "__main__":
    main()
