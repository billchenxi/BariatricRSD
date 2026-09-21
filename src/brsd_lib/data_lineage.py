"""Checkpoint- and label-level data provenance for BariatricRSD.

Implements the first deliverable in ``plans/STRATEGY.md`` §III.1 / §VII.3:

    "add a DATA_LINEAGE.md to the repo recording which checkpoints touched
    which datasets, with hashes. It costs an hour now and is the document
    that makes a future diligence process survivable."

Why this exists
---------------
Every dataset this project trains on is **CC BY-NC-SA 4.0** — NonCommercial
*and* ShareAlike. A model derived from them cannot ship in a product, and
whether trained weights count as an "adaptation" under ShareAlike is legally
unsettled. That does not need to be settled against us to matter: it only has
to be an open question for an acquirer's counsel to flag.

So the repository has to be able to answer, per checkpoint, "what did this
touch?" — and answer it from evidence rather than memory. Reconstructing that
after the fact is close to impossible, which is why the lineage is generated
from the artifacts themselves and re-verifiable at any time.

This module is descriptive, not prescriptive. It records what an artifact was
built from; it does not decide whether a given use is lawful. It is not legal
advice.

Usage
-----
    python -m brsd_lib.data_lineage                      # regenerate DATA_LINEAGE.md
    python -m brsd_lib.data_lineage --verify             # integrity check, non-zero exit on drift
    python -m brsd_lib.data_lineage --hash all           # hash every checkpoint (slow, ~60 GB read)
    python -m brsd_lib.data_lineage --json-out lin.json  # machine-readable alongside the markdown
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

# ── Dataset registry ────────────────────────────────────────────────────────
# Licence terms verified at source on 2026-09-17. Re-verify before relying on
# them: dataset licences do change, and the whole point of this file is that it
# is checkable.

RESEARCH_ONLY = "research"   # lineage touched a NonCommercial dataset
PRODUCT_SAFE = "product"     # lineage is clean of NonCommercial data
UNKNOWN = "unknown"          # provenance could not be established


@dataclass(frozen=True)
class Dataset:
    key: str
    name: str
    licence: str
    commercial_use: bool
    share_alike: bool
    source: str
    verified: str
    note: str = ""

    @property
    def lineage(self) -> str:
        return PRODUCT_SAFE if self.commercial_use else RESEARCH_ONLY


DATASETS: dict[str, Dataset] = {
    d.key: d
    for d in [
        Dataset(
            key="mb140",
            name="MultiBypass140",
            licence="CC BY-NC-SA 4.0",
            commercial_use=False,
            share_alike=True,
            source="https://github.com/CAMMA-public/MultiBypass140",
            verified="2026-09-17",
            note="140 RYGB videos, two centres (Bern BBP / Strasbourg SBP). "
            "Repository states: available for non-commercial scientific "
            "research purposes as defined in the CC BY-NC-SA 4.0.",
        ),
        Dataset(
            key="cholec80",
            name="Cholec80",
            licence="CC BY-NC-SA 4.0",
            commercial_use=False,
            share_alike=True,
            source="http://camma.u-strasbg.fr/datasets/",
            verified="2026-09-17",
            note="80 laparoscopic cholecystectomy videos; 72 carry the public "
            "phase labels used here. Requires a CAMMA data-use agreement.",
        ),
        Dataset(
            key="cholect50",
            name="CholecT50",
            licence="CC BY-NC-SA 4.0",
            commercial_use=False,
            share_alike=True,
            source="https://github.com/CAMMA-public/cholect50",
            verified="2026-09-17",
            note="50 videos, 45 of them drawn from Cholec80 — additional "
            "annotation, not an independent cohort. Not currently used by any "
            "artifact in this repository.",
        ),
        Dataset(
            key="endoscapes2023",
            name="Endoscapes2023",
            licence="PhysioNet credentialed access + DUA",
            commercial_use=False,
            share_alike=False,
            source="https://physionet.org/content/endoscapes-2023/1.0.0/",
            verified="2026-09-17",
            note="Terms must be read in full before any product use. Not "
            "currently used by any artifact in this repository.",
        ),
    ]
}

# Substrings in an artifact path or manifest entry that identify its dataset.
# Order matters: the first match wins, so put the more specific keys first.
_DATASET_MARKERS: list[tuple[str, str]] = [
    ("cholect50", "cholect50"),
    ("cholec80", "cholec80"),
    ("endoscapes", "endoscapes2023"),
    ("mb140", "mb140"),
    ("multibypass", "mb140"),
    ("bypass140", "mb140"),
]


def classify_datasets(*texts: Optional[str]) -> list[str]:
    """Return every dataset key implied by ``texts``.

    Deliberately multi-valued: a transfer checkpoint (Cholec80 fine-tuned from
    an MB140 initialisation) has touched both, and for licence purposes both
    count. Collapsing that to a single "primary" dataset would understate the
    lineage, which is the one direction this file must never err in.
    """
    blob = " ".join(t for t in texts if t).lower()
    found = [key for marker, key in _DATASET_MARKERS if marker in blob]
    return sorted(set(found))


def lineage_of(dataset_keys: Iterable[str]) -> str:
    keys = list(dataset_keys)
    if not keys:
        return UNKNOWN
    return PRODUCT_SAFE if all(DATASETS[k].commercial_use for k in keys) else RESEARCH_ONLY


# ── Artifact records ────────────────────────────────────────────────────────


@dataclass
class Artifact:
    path: str
    kind: str                       # "label" | "cluster-artifact" | "checkpoint"
    datasets: list[str]
    lineage: str
    size_bytes: int
    sha256: Optional[str] = None
    sha256_source: str = "not-computed"   # "computed" | "manifest" | "not-computed"
    integrity: Optional[str] = None       # "ok" | "MISMATCH" | "file-missing" | None
    aliases: list[str] = field(default_factory=list)
    symlink_aliases: list[str] = field(default_factory=list)
    provenance: dict = field(default_factory=dict)
    note: str = ""


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


# ── Scanners ────────────────────────────────────────────────────────────────


def scan_labels(labels_dir: Path, root: Path, do_hash: bool = True) -> list[Artifact]:
    """Record every label / cluster artifact, with the provenance it declares."""
    out: list[Artifact] = []
    if not labels_dir.is_dir():
        return out

    for path in sorted(labels_dir.glob("*.json")):
        datasets = classify_datasets(path.name)
        is_cluster = "artifacts" in path.name or "clusters" in path.name
        prov: dict = {}
        note = ""

        try:
            payload = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            note = f"unreadable: {type(exc).__name__}"
            payload = None

        if isinstance(payload, dict):
            # k-means / cluster artifact: carries its own fitting provenance.
            for key in ("source_labels", "seed", "K", "n_features", "n_components"):
                if key in payload:
                    prov[key] = payload[key]
            # STRATEGY.md §V.3: min_df was never recorded, so a matched-config
            # comparison across datasets cannot be reconstructed from these files.
            prov["min_df_recorded"] = "min_df" in payload
        elif isinstance(payload, list):
            prov["n_videos"] = len(payload)
            splits: dict[str, int] = {}
            centres: dict[str, int] = {}
            for rec in payload:
                if not isinstance(rec, dict):
                    continue
                if (s := rec.get("split")) is not None:
                    splits[str(s)] = splits.get(str(s), 0) + 1
                if vid := rec.get("video_id"):
                    centres[str(vid)[:3]] = centres.get(str(vid)[:3], 0) + 1
            if splits:
                prov["splits"] = dict(sorted(splits.items()))
            if centres and len(centres) <= 4:
                prov["video_id_prefixes"] = dict(sorted(centres.items()))

        art = Artifact(
            path=_rel(path, root),
            kind="cluster-artifact" if is_cluster else "label",
            datasets=datasets,
            lineage=lineage_of(datasets),
            size_bytes=path.stat().st_size,
            provenance=prov,
            note=note,
        )
        if do_hash:
            art.sha256 = sha256_file(path)
            art.sha256_source = "computed"
        out.append(art)
    return out


def scan_checkpoints(
    weights_dirs: Iterable[Path],
    root: Path,
    manifest_path: Optional[Path] = None,
    hash_mode: str = "manifest",
) -> list[Artifact]:
    """Record every checkpoint, cross-checked against the weight manifest.

    ``hash_mode`` is one of:
      ``none``      never hash (fast; integrity unverified)
      ``manifest``  verify files the manifest claims a hash for (default)
      ``all``       additionally hash checkpoints the manifest does not list
    """
    if hash_mode not in {"none", "manifest", "all"}:
        raise ValueError(f"hash_mode must be none|manifest|all, got {hash_mode!r}")

    manifest: dict = {}
    if manifest_path and manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text())
        except (json.JSONDecodeError, OSError):
            manifest = {}

    # Index manifest entries two ways, because the same checkpoint appears on
    # disk under two naming conventions: the deposit copies it to
    # <run>.pth, while the original training output is <run>/best_model.pth.
    by_name: dict[str, tuple[str, dict]] = {}    # "run033_oracle_seed42.pth"
    by_stem: dict[str, tuple[str, dict]] = {}    # "run033_oracle_seed42"
    for key, entry in manifest.items():
        if key.startswith("_") or not isinstance(entry, dict):
            continue
        hf_path = entry.get("hf_path")
        if hf_path:
            by_name[Path(hf_path).name] = (key, entry)
            by_stem[Path(hf_path).stem] = (key, entry)

    # Group by resolved target: part of the deposit is symlinked into
    # lambda_mirror rather than copied, so several paths can name one file.
    # Hash it once, but keep every path that points at it — "the deposit entry
    # is a link into a 45 GB gitignored mirror" is exactly the kind of fact
    # this document exists to surface.
    groups: dict[Path, list[Path]] = {}
    for weights_dir in weights_dirs:
        if not weights_dir.is_dir():
            continue
        for path in sorted(weights_dir.rglob("*.pth")):
            groups.setdefault(path.resolve(), []).append(path)

    out: list[Artifact] = []
    for resolved, paths in sorted(groups.items()):
        # Prefer a real file as the canonical path; fall back to the first.
        canonical = next((p for p in paths if not p.is_symlink()), paths[0])
        art = _checkpoint_artifact(canonical, root, by_name, by_stem, hash_mode)

        aliases = [p for p in paths if p != canonical]
        if aliases:
            art.aliases = [_rel(p, root) for p in aliases]
            # A manifest match may only be reachable through the alias name.
            if not art.provenance.get("manifest_key"):
                for alias in aliases:
                    hit = by_name.get(alias.name) or by_stem.get(alias.parent.name)
                    if hit:
                        art.provenance["manifest_key"] = hit[0]
                        for src, dst in (("logical_name", "logical_name"),
                                         ("trained_on", "trained_on"),
                                         ("produces", "reported_mae_min"),
                                         ("notes", "notes")):
                            if src in hit[1]:
                                art.provenance.setdefault(dst, hit[1][src])
                        declared = hit[1].get("sha256")
                        if declared and art.sha256_source == "computed":
                            art.integrity = "ok" if art.sha256 == declared else "MISMATCH"
                        elif declared and art.sha256 is None:
                            art.sha256, art.sha256_source = declared, "manifest"
                        art.note = ""
                        break
            # Detect the link structurally rather than by path substring: a
            # renamed deposit directory must not silently drop the warning.
            sym = [p for p in aliases if p.is_symlink()]
            if sym:
                art.symlink_aliases = [_rel(p, root) for p in sym]
                art.note = (art.note + " " if art.note else "") + (
                    f"{len(sym)} path(s) pointing here are symlinks, not "
                    f"independent copies")
        out.append(art)

    # Manifest entries with no file anywhere on disk are themselves a fact.
    matched = {a.provenance.get("manifest_key") for a in out}
    for _, (manifest_key, entry) in sorted(by_name.items()):
        if manifest_key in matched:
            continue
        datasets = classify_datasets(manifest_key, entry.get("trained_on"),
                                     entry.get("logical_name"))
        out.append(Artifact(
            path=f"(absent) {entry.get('hf_path', manifest_key)}",
            kind="checkpoint",
            datasets=datasets,
            lineage=lineage_of(datasets),
            size_bytes=0,
            sha256=entry.get("sha256"),
            sha256_source="manifest",
            integrity="file-missing",
            provenance={"manifest_key": manifest_key,
                        **({"logical_name": entry["logical_name"]}
                           if "logical_name" in entry else {})},
            note="declared in manifest, not present in this checkout",
        ))
    return out


def _checkpoint_artifact(
    path: Path,
    root: Path,
    by_name: dict[str, tuple[str, dict]],
    by_stem: dict[str, tuple[str, dict]],
    hash_mode: str,
) -> Artifact:
    """Build one checkpoint record, matched against the manifest if possible."""
    # A deposit copy matches on its own filename; a raw training output is
    # always called best_model.pth, so it matches on its run directory instead.
    key_entry = by_name.get(path.name) or by_stem.get(path.parent.name)
    manifest_key, entry = key_entry if key_entry else (None, {})

    datasets = classify_datasets(
        _rel(path, root), manifest_key, entry.get("trained_on"), entry.get("logical_name")
    )
    prov: dict = {}
    if manifest_key:
        prov["manifest_key"] = manifest_key
    for src, dst in (("logical_name", "logical_name"),
                     ("trained_on", "trained_on"),
                     ("produces", "reported_mae_min"),
                     ("produces_with_isotonic_only", "reported_mae_min_isotonic"),
                     ("notes", "notes")):
        if src in entry:
            prov[dst] = entry[src]

    declared = entry.get("sha256")
    art = Artifact(
        path=_rel(path, root),
        kind="checkpoint",
        datasets=datasets,
        lineage=lineage_of(datasets),
        size_bytes=path.stat().st_size,
        provenance=prov,
        note="" if manifest_key else "not listed in weights manifest",
    )

    should_hash = hash_mode == "all" or (hash_mode == "manifest" and declared)
    if should_hash:
        art.sha256 = sha256_file(path)
        art.sha256_source = "computed"
        if declared:
            art.integrity = "ok" if art.sha256 == declared else "MISMATCH"
    elif declared:
        art.sha256 = declared
        art.sha256_source = "manifest"
    return art


# ── Report ──────────────────────────────────────────────────────────────────


def git_commit(root: Path) -> str:
    try:
        res = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        return res.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _human_bytes(n: int) -> str:
    if n <= 0:
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} TB"


def build_lineage(root: Path, hash_mode: str = "manifest", hash_labels: bool = True) -> dict:
    labels = scan_labels(root / "labels", root, do_hash=hash_labels)
    ckpts = scan_checkpoints(
        [root / "papers/paper1_neurips2026/reproducibility/weights",
         root / "lambda_mirror/outputs"],
        root,
        manifest_path=root / "papers/paper1_neurips2026/reproducibility/weights/manifest.json",
        hash_mode=hash_mode,
    )
    artifacts = labels + ckpts
    datasets_used = sorted({k for a in artifacts for k in a.datasets})
    return {
        "generated": date.today().isoformat(),
        "commit": git_commit(root),
        "hash_mode": hash_mode,
        "datasets": {k: asdict(DATASETS[k]) for k in DATASETS},
        "datasets_in_use": datasets_used,
        "counts": {
            "labels": sum(1 for a in artifacts if a.kind in ("label", "cluster-artifact")),
            "checkpoints": sum(1 for a in artifacts if a.kind == "checkpoint"),
            "research_lineage": sum(1 for a in artifacts if a.lineage == RESEARCH_ONLY),
            "product_lineage": sum(1 for a in artifacts if a.lineage == PRODUCT_SAFE),
            "unknown_lineage": sum(1 for a in artifacts if a.lineage == UNKNOWN),
        },
        "integrity": {
            "verified": sum(1 for a in artifacts if a.integrity == "ok"),
            "mismatched": [a.path for a in artifacts if a.integrity == "MISMATCH"],
            "missing": [a.path for a in artifacts if a.integrity == "file-missing"],
        },
        "artifacts": [asdict(a) for a in artifacts],
    }


def render_markdown(lin: dict) -> str:
    L: list[str] = []
    w = L.append

    w("# Data lineage")
    w("")
    w(f"*Generated {lin['generated']} at commit `{lin['commit']}` by "
      "`python -m brsd_lib.data_lineage`. Do not edit by hand — regenerate it.*")
    w("")
    w("This file records what every trained checkpoint and label artifact in this")
    w("repository was derived from. It exists because the licence position below")
    w("makes that question load-bearing, and because reconstructing it after the")
    w("fact is close to impossible.")
    w("")
    w("**It is descriptive, not permissive.** It records provenance; it does not")
    w("establish that any particular use is lawful. Not legal advice.")
    w("")

    # ── licences ──
    w("## 1. Dataset licences — the governing constraint")
    w("")
    w("| Dataset | Licence | Commercial use | ShareAlike | Verified |")
    w("|---|---|---|---|---|")
    for key in sorted(lin["datasets"]):
        d = lin["datasets"][key]
        in_use = " *(in use)*" if key in lin["datasets_in_use"] else ""
        w(f"| [{d['name']}]({d['source']}){in_use} | {d['licence']} | "
          f"{'yes' if d['commercial_use'] else '**no**'} | "
          f"{'yes' if d['share_alike'] else 'no'} | {d['verified']} |")
    w("")
    for key in sorted(lin["datasets"]):
        d = lin["datasets"][key]
        if d["note"]:
            w(f"- **{d['name']}** — {d['note']}")
    w("")
    w("Two distinct problems, and the second is the worse one:")
    w("")
    w("1. **NonCommercial** forbids commercial use outright — no shipped model, no")
    w("   investor demo, no paid pilot.")
    w("2. **ShareAlike** requires adaptations to carry the same licence. Whether")
    w("   trained weights are an \"adaptation\" is legally unsettled, and that is")
    w("   precisely the difficulty: it does not have to be settled against us to")
    w("   cost us a diligence review.")
    w("")

    # ── the rule ──
    w("## 2. The lineage rule")
    w("")
    w("```")
    w("  RESEARCH LINEAGE                      PRODUCT LINEAGE")
    w("  MB140, Cholec80, CholecT50            data owned or licensed commercially")
    w("  -> papers, benchmarks, methods        -> shipped weights")
    w("  -> credibility, citations             -> revenue")
    w("  never ships                           never needs the academic data")
    w("      +---- crosses over: the METHOD, the Apache-2.0 CODE,")
    w("            the EVALUATION PROTOCOL, and reputation ----+")
    w("```")
    w("")
    c = lin["counts"]
    w(f"Of the {c['labels'] + c['checkpoints']} artifacts recorded below, "
      f"**{c['research_lineage']} are research-lineage** "
      f"(they touched a NonCommercial dataset), {c['product_lineage']} are "
      f"product-lineage, and {c['unknown_lineage']} could not be classified.")
    w("")
    if c["product_lineage"] == 0:
        w("> **No artifact in this repository is currently product-lineage.** A")
        w("> shippable model has to be trained on data owned or licensed")
        w("> commercially — in practice, a customer's own video under a commercial")
        w("> data-use agreement. Plan for the first paying pilot to be the first")
        w("> training set.")
        w("")

    # ── integrity ──
    integ = lin["integrity"]
    w("## 3. Integrity")
    w("")
    w(f"- Hash mode: `{lin['hash_mode']}`")
    w(f"- Checkpoints re-hashed and matching their manifest entry: **{integ['verified']}**")
    w(f"- Hash mismatches: **{len(integ['mismatched'])}**"
      + ("" if not integ["mismatched"] else " — " + ", ".join(f"`{p}`" for p in integ["mismatched"])))
    w(f"- Declared in the manifest but absent from this checkout: "
      f"**{len(integ['missing'])}**")
    if integ["missing"]:
        w("")
        for p in integ["missing"]:
            w(f"  - `{p}`")
    w("")
    linked = [a for a in lin["artifacts"] if a.get("symlink_aliases")]
    if linked:
        w("")
        w(f"> **{len(linked)} of the reproducibility-deposit checkpoints are symlinks")
        w("> into `lambda_mirror/`, not independent copies.** `lambda_mirror/` is")
        w("> gitignored and holds 45 GB of archived run outputs; if it is pruned or")
        w("> the checkout is moved without it, these deposit entries break. Resolve")
        w("> them to real files before any external deposit or release:")
        w(">")
        for a in linked:
            for dep in a["symlink_aliases"]:
                w(f"> - `{dep}`")
                w(f">   → `{a['path']}`")
    w("")
    w("Re-check at any time with `python -m brsd_lib.data_lineage --verify`, which")
    w("exits non-zero on drift.")
    w("")

    # ── checkpoints ──
    ckpts = [a for a in lin["artifacts"] if a["kind"] == "checkpoint"]
    w("## 4. Checkpoints")
    w("")
    w("| Checkpoint | Dataset | Lineage | SHA256 | Size | Reported MAE |")
    w("|---|---|---|---|---|---|")
    for a in ckpts:
        sha = a["sha256"]
        sha_cell = f"`{sha[:12]}`" if sha else "—"
        if a["sha256_source"] == "manifest":
            sha_cell += " ᵐ"
        if a["integrity"] == "MISMATCH":
            sha_cell += " ⚠︎"
        ds = " + ".join(DATASETS[k].name for k in a["datasets"]) or "—"
        mae = a["provenance"].get("reported_mae_min",
                                  a["provenance"].get("reported_mae_min_isotonic"))
        name = f"`{a['path']}`"
        if a.get("aliases"):
            name += f"<br><small>↳ also at `{a['aliases'][0]}`</small>"
        w(f"| {name} | {ds} | {a['lineage']} | {sha_cell} | "
          f"{_human_bytes(a['size_bytes'])} | {mae if mae is not None else '—'} |")
    w("")
    w("ᵐ hash taken from the manifest rather than recomputed; "
      "⚠︎ recomputed hash disagrees with the manifest.")
    w("")

    # ── labels ──
    labs = [a for a in lin["artifacts"] if a["kind"] in ("label", "cluster-artifact")]
    w("## 5. Label and cluster artifacts")
    w("")
    w("| Artifact | Dataset | Kind | SHA256 | Declared provenance |")
    w("|---|---|---|---|---|")
    for a in labs:
        sha = a["sha256"]
        prov = a["provenance"]
        bits = []
        for k in ("n_videos", "splits", "video_id_prefixes", "K", "seed",
                  "n_features", "n_components", "source_labels"):
            if k in prov:
                v = prov[k]
                bits.append(f"{k}={json.dumps(v) if isinstance(v, dict) else v}")
        if prov.get("min_df_recorded") is False:
            bits.append("**min_df not recorded**")
        ds = " + ".join(DATASETS[k].name for k in a["datasets"]) or "—"
        w(f"| `{Path(a['path']).name}` | {ds} | {a['kind']} | "
          f"{'`' + sha[:12] + '`' if sha else '—'} | {'; '.join(bits) or '—'} |")
    w("")
    if any(a["provenance"].get("min_df_recorded") is False for a in labs):
        w("> **`min_df` is not recorded in any cluster artifact.** As noted in")
        w("> `plans/STRATEGY.md` §V.3, the stored artifacts therefore do not")
        w("> establish a matched-K/`min_df` comparison across datasets. Run a")
        w("> train-only matched-configuration control before interpreting")
        w("> cross-dataset representation differences.")
        w("")

    w("## 6. Regenerating")
    w("")
    w("```bash")
    w("python -m brsd_lib.data_lineage              # rewrite this file")
    w("python -m brsd_lib.data_lineage --hash all   # also hash unlisted checkpoints")
    w("python -m brsd_lib.data_lineage --verify     # integrity check only")
    w("```")
    w("")
    w("Regenerate before any release, any external deposit, and after any training")
    w("run that produces a new checkpoint.")
    return "\n".join(L) + "\n"


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv: Optional[Iterable[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m brsd_lib.data_lineage",
        description="Generate or verify DATA_LINEAGE.md from the artifacts on disk.",
    )
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2],
                    help="Repository root (default: inferred from this file).")
    ap.add_argument("--out", type=Path, default=None,
                    help="Markdown output path (default: <root>/DATA_LINEAGE.md).")
    ap.add_argument("--json-out", type=Path, default=None,
                    help="Also write the machine-readable lineage here.")
    ap.add_argument("--hash", dest="hash_mode", default="manifest",
                    choices=["none", "manifest", "all"],
                    help="Which checkpoints to hash. 'all' reads every file (slow).")
    ap.add_argument("--no-hash-labels", action="store_true",
                    help="Skip hashing label artifacts.")
    ap.add_argument("--verify", action="store_true",
                    help="Check integrity and report drift; do not rewrite the markdown. "
                         "Exits 1 if any hash mismatches.")
    args = ap.parse_args(list(argv) if argv is not None else None)

    root: Path = args.root.resolve()
    lin = build_lineage(root, hash_mode=args.hash_mode, hash_labels=not args.no_hash_labels)
    integ = lin["integrity"]

    if args.verify:
        print(f"lineage verify @ {lin['commit']}  (hash mode: {lin['hash_mode']})")
        print(f"  artifacts        : {len(lin['artifacts'])}")
        print(f"  research lineage : {lin['counts']['research_lineage']}")
        print(f"  product lineage  : {lin['counts']['product_lineage']}")
        print(f"  hashes verified  : {integ['verified']}")
        print(f"  mismatches       : {len(integ['mismatched'])}")
        for p in integ["mismatched"]:
            print(f"      MISMATCH  {p}")
        linked = [a for a in lin["artifacts"] if a.get("symlink_aliases")]
        print(f"  symlinked copies : {len(linked)}"
              + ("  (deposit is not self-contained)" if linked else ""))
        print(f"  declared-but-absent: {len(integ['missing'])}")
        for p in integ["missing"]:
            print(f"      MISSING   {p}")
        return 1 if integ["mismatched"] else 0

    out = args.out or (root / "DATA_LINEAGE.md")
    out.write_text(render_markdown(lin))
    print(f"wrote {out}  ({len(lin['artifacts'])} artifacts, "
          f"{lin['counts']['research_lineage']} research-lineage, "
          f"{integ['verified']} hashes verified)")

    if args.json_out:
        args.json_out.write_text(json.dumps(lin, indent=2, sort_keys=False))
        print(f"wrote {args.json_out}")

    if integ["mismatched"]:
        print(f"WARNING: {len(integ['mismatched'])} checkpoint hash mismatch(es)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
