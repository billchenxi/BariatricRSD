# Repo Reorganization Proposal

*Created 2026-06-04. The repo top level has accumulated 18 markdown
docs + scattered source files from Paper 1 + a couple of untracked
secret files. This document proposes three reorganization options.
Read through, pick one, and I'll execute it carefully.*

---

## What's at the top level now

### Markdown docs (18)

**Paper 1 — submitted to NeurIPS 2026 (archival):**

| File | Status |
|---|---|
| `FINDINGS.md` | Paper 1 narrative findings |
| `RESULTS_AUDIT.md` | Per-result provenance map |
| `RESEARCH_PLAN.md` + `.pdf` | Original Apr 2026 plan |
| `SESSION_LOG.md` | Day-by-day development log |
| `SUBMISSION_TODO.md` | Stale Paper 1 submission todos |
| `RECONSTRUCTION_GUIDE.md` | How to rebuild from scratch |
| `REVIEW_ANONYMOUS_DEPOSIT_RUNBOOK.md` | Anon deposit runbook |
| `LAMBDA_HF_UPLOAD_RUNBOOK.md` | Lambda-side HF upload |
| `STOP_LAMBDA_NOW.md` | Lambda decommission runbook |

**Paper 2 — active planning:**

| File | Status |
|---|---|
| `NEXT_PAPER_BRIEF.md` | Current authoritative brief |
| `NEXT_PAPER_PLAN.md` | Execution plan |
| `NEXT_PAPER_PHYSICAL_AI.md` | **Superseded** by `_BRIEF.md` |
| `NEXT_PAPER_REFINEMENTS.md` | Incorporated into `_BRIEF.md` |
| `NEXT_PUBLICATIONS.md` | Long-horizon 5-paper roadmap |

**General:**

| File | Status |
|---|---|
| `README.md` | Project overview |
| `LICENSE` | License |
| `CONTRIBUTING.md` | Contribution guide |
| `INSTRUCTIONS.md` | (purpose unclear, check before moving) |
| `GPT_plan.md` | (purpose unclear, check before moving) |

### Source files scattered at top level

These should probably live inside `brsd_lib/` or a `legacy/` subdir, but
they were never moved:

```
__init__.py, config.py, evaluate.py, train.py, train_cholec80.py,
requirements.txt, pyproject.toml
training/, utils/, data/
```

### Untracked secret files (delete or move out of repo)

| File | Recommendation |
|---|---|
| `rsd.pem` | SSH private key. Move to `~/.ssh/` and `chmod 600`. NOT in repo. |
| `us-east-3-bc339d32421d4121bd8e2eb27e068fdd.txt` | AWS/Lambda cluster credential. Move to `~/.aws/` or delete. NOT in repo. |
| `lambda_setup.zip` | Large archival blob. Confirm contents are recoverable from `lambda_setup/` dir, then delete. |

Neither secret file is tracked in git — just local-disk litter.

### Directories — current categorization

**Paper 1 (archival after submission):**

```
paper/, reproducibility/, anonymous_code_submission/,
lambda_mirror/, lambda_setup/, scripts/, brsd_lib/,
models/, evaluation/, inference/, labels/, training/,
data/, utils/, tests/, notebooks/,
hf_space_demo/, hf_space_repo/, codex_workflow/, 2019/
```

**Paper 2 (active):**

```
paper2_infra/ — just created, mostly empty
docs/ — just created, empty
```

---

## Three options

### Option A — Light touch (recommended for now)

**Scope:** move only top-level markdown docs into subdirectories. Don't
touch any code directory or any artifact directory.

```
bariatric_rsd/
├── README.md                          ← updated to be a navigation index
├── LICENSE
├── CONTRIBUTING.md
│
├── docs/
│   ├── paper1_neurips2026/             ← all submitted-paper docs
│   │   ├── FINDINGS.md
│   │   ├── RESULTS_AUDIT.md
│   │   ├── RESEARCH_PLAN.md
│   │   ├── SESSION_LOG.md
│   │   ├── SUBMISSION_TODO.md
│   │   └── RECONSTRUCTION_GUIDE.md
│   │
│   ├── paper2_planning/                ← active Paper 2 work
│   │   ├── NEXT_PAPER_BRIEF.md
│   │   ├── NEXT_PAPER_PLAN.md
│   │   ├── NEXT_PUBLICATIONS.md
│   │   └── archive/
│   │       ├── NEXT_PAPER_PHYSICAL_AI.md     (superseded)
│   │       └── NEXT_PAPER_REFINEMENTS.md     (incorporated)
│   │
│   └── runbooks/                       ← operational runbooks
│       ├── REVIEW_ANONYMOUS_DEPOSIT_RUNBOOK.md
│       ├── LAMBDA_HF_UPLOAD_RUNBOOK.md
│       └── STOP_LAMBDA_NOW.md
│
├── paper2_infra/                      ← unchanged, active Paper 2 code
├── paper/                              ← unchanged, submitted manuscript
├── reproducibility/                    ← unchanged
├── anonymous_code_submission/          ← unchanged
├── lambda_mirror/                      ← unchanged
├── lambda_setup/, scripts/, brsd_lib/, models/, evaluation/,
    inference/, labels/, training/, data/, utils/, tests/,
    notebooks/, hf_space_demo/, hf_space_repo/, codex_workflow/,
    2019/                              ← all unchanged
│
└── (top-level loose .py / .txt files moved into a new legacy/ folder if you want)
```

**Pros:**
- Top level becomes 3 directories + `README.md` + `LICENSE` + `CONTRIBUTING.md` instead of ~40 items.
- No path breakage in reproducibility scripts, runbooks, or anonymous code zip.
- Reversible — file moves are just `git mv`, easy to undo.

**Cons:**
- Code directories still mix Paper 1 source with active work.
- `__init__.py`, `train.py`, etc. at top level remain ugly.

**Effort:** ~5 minutes, ~15 file moves.

### Option B — Medium touch (proper separation)

Everything in Option A, plus:
- Move scattered top-level Python files into a `legacy/` directory.
- Move clearly Paper-1-specific code dirs (`training/`, `data/`, `utils/`) into `legacy/` too.
- Add a top-level `archive/` for old / unclear stuff (`2019/`, `codex_workflow/`, `GPT_plan.md`, `INSTRUCTIONS.md`).

```
bariatric_rsd/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
│
├── docs/                              (as in Option A)
│
├── paper2_infra/                      ← active
├── paper/                              ← submitted paper
├── reproducibility/                    ← Paper 1 repro package
├── anonymous_code_submission/          ← Paper 1 anon zip
│
├── src/                               ← Paper 1 source code, renamed/grouped
│   ├── brsd_lib/
│   ├── models/
│   ├── evaluation/
│   ├── inference/
│   ├── training/
│   └── data/
│
├── infra/                             ← Paper 1 ops + scripts
│   ├── lambda_mirror/                  (45 GB archival)
│   ├── lambda_setup/
│   └── scripts/
│
├── assets/                            ← non-code Paper 1 stuff
│   ├── labels/
│   ├── notebooks/
│   ├── tests/
│   ├── hf_space_demo/
│   └── hf_space_repo/
│
└── archive/                           ← old/unclear
    ├── 2019/
    ├── codex_workflow/
    ├── legacy_top_level_pyfiles/      (train.py, evaluate.py, etc.)
    ├── GPT_plan.md
    └── INSTRUCTIONS.md
```

**Pros:**
- Top-level becomes 8 directories. Clear semantic split.
- Paper 1 code is grouped; Paper 2 code (`paper2_infra/`) stays at top.
- No more scattered `.py` files at root.

**Cons:**
- Breaks paths in `RESULTS_AUDIT.md`, runbooks (e.g., they reference
  `lambda_mirror/outputs/...` — would become `infra/lambda_mirror/...`).
  I'd have to update those refs.
- Breaks any external bookmarks (the anonymous code zip references
  `scripts/` etc. by relative path).

**Effort:** ~30 minutes, ~25 directory moves + path updates in docs.

### Option C — Heavy lift (two paper-trees)

Split everything into `paper1_submitted/` and `paper2_active/` trees.

```
bariatric_rsd/
├── README.md                          ← navigation hub
├── LICENSE
├── CONTRIBUTING.md
│
├── paper1_submitted/                  ← frozen Paper 1 world
│   ├── manuscript/                     (was paper/)
│   ├── reproducibility/                (was reproducibility/)
│   ├── anonymous_code/                 (was anonymous_code_submission/)
│   ├── lambda_mirror/                  (was lambda_mirror/, 45 GB)
│   ├── src/                            (brsd_lib + models + ...)
│   ├── infra/                          (lambda_setup + scripts)
│   ├── docs/                           (Paper 1 docs)
│   └── README.md                        (Paper 1 specific)
│
├── paper2_active/                     ← active Paper 2 world
│   ├── infra/                          (was paper2_infra/)
│   ├── docs/                           (planning + brief + plan)
│   └── README.md
│
└── archive/                           (old/unclear stuff)
```

**Pros:**
- Maximum clarity. Paper 1 is one self-contained tree; Paper 2 is another.
- Easy to delete the `paper1_submitted/` tree later when you don't need
  the bulk anymore.

**Cons:**
- Every internal path reference breaks. Several days of update work
  across reproducibility scripts, runbooks, anonymous code zip.
- The 4open.science deposit references the old `anonymous_code_submission/`
  layout — that anonymous deposit was uploaded and now points at a fixed
  snapshot, so the moves don't propagate there anyway. But any *future*
  pull of code from this repo for that deposit would need re-mapping.
- 45 GB `lambda_mirror/` move is a real disk shuffle.

**Effort:** ~2–4 hours, lots of path fixes.

---

## My recommendation

**Option A — light touch.** Three reasons:

1. **Paper 1 is submitted.** Its docs and code shouldn't be moved
   around now — anonymous code zip + reproducibility package + runbooks
   all reference current paths. Breaking them risks anonymity / repro
   for short-term tidiness.

2. **Top-level clutter is mostly the 18 markdown docs**, not the
   directories. Moving the docs alone gets you 80% of the visual
   cleanup with 5% of the effort.

3. **You can still upgrade to Option B or C later** once Paper 1 is
   accepted/rejected and the archival pressure relaxes. Option A
   doesn't lock anything in.

The one nontrivial thing Option A doesn't fix: the loose `__init__.py`,
`config.py`, `train.py`, `train_cholec80.py`, `evaluate.py` at top
level. If you want, I can move just those 5 files into `legacy/` or
similar as an Option A+ — that's a 30-second extra step.

---

## Security cleanup (do regardless of which option)

Move these out of the repo entirely:

```bash
# SSH key — move to standard location
mv rsd.pem ~/.ssh/lambda_rsd.pem
chmod 600 ~/.ssh/lambda_rsd.pem

# Lambda cluster credential — move to standard location or delete
mv us-east-3-bc339d32421d4121bd8e2eb27e068fdd.txt ~/.aws/  # or rm

# Large archival blob — confirm contents are in lambda_setup/, then delete
unzip -l lambda_setup.zip | head  # inspect first
# if redundant with lambda_setup/ directory:
# rm lambda_setup.zip
```

None of these are in git, so no rewrite-history needed.

---

## What I'll do once you pick

For **Option A**:
1. Create `docs/{paper1_neurips2026,paper2_planning,runbooks}` and `docs/paper2_planning/archive/`.
2. `git mv` each markdown into its destination — git preserves history.
3. Update `README.md` to be a top-level navigation index pointing at the new docs structure.
4. Resume Phase 0 (backbone feasibility audit + infrastructure work).

For **Option B**: same as A, plus 4 more dir moves (`src/`, `infra/`, `assets/`, `archive/`) and path updates in the affected runbooks/audit files.

For **Option C**: same as B, but everything Paper-1 goes under `paper1_submitted/`.

In all three cases I'll print exact paths before moving anything, so you can veto specific items.

— *Pick A, B, or C and I'll proceed.*
