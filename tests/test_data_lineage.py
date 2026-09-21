"""Tests for brsd_lib.data_lineage.

The lineage document is a provenance record that a diligence process may lean
on, so the properties that matter most are the conservative ones: a lineage
must never be *under*-stated. A checkpoint that touched a NonCommercial
dataset has to come back as research-lineage even when the evidence is partial.
"""

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from brsd_lib.data_lineage import (  # noqa: E402
    DATASETS,
    PRODUCT_SAFE,
    RESEARCH_ONLY,
    UNKNOWN,
    build_lineage,
    classify_datasets,
    lineage_of,
    render_markdown,
    scan_checkpoints,
    scan_labels,
    sha256_file,
)

REPO = Path(__file__).resolve().parents[1]


# ── dataset registry ────────────────────────────────────────────────────────

def test_every_registered_dataset_is_noncommercial():
    """If this ever fails, the lineage rule in STRATEGY.md III.1 has changed."""
    for key, ds in DATASETS.items():
        assert ds.commercial_use is False, f"{key} is now marked commercial-usable"


def test_registry_keys_match_their_dataclass_key():
    for key, ds in DATASETS.items():
        assert ds.key == key


# ── classification ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    ("labels/mb140_fold0_labels.json", ["mb140"]),
    ("labels/cholec80_labels.json", ["cholec80"]),
    ("MultiBypass140 fold 3", ["mb140"]),
    ("weights/endoscapes_probe.pth", ["endoscapes2023"]),
    ("something_unrelated.pth", []),
])
def test_classify_single_dataset(text, expected):
    assert classify_datasets(text) == expected


def test_transfer_checkpoint_claims_both_datasets():
    """Run 018 is Cholec80 fine-tuned from an MB140 initialisation."""
    got = classify_datasets(
        "run018_cholec80_transfer_from_mb140_seed42/best_model.pth",
        "Run 018 transfer-from-MB140 -> Cholec80, seed 42",
    )
    assert got == ["cholec80", "mb140"]


def test_classification_searches_every_field():
    # The path alone says nothing; the manifest text carries the provenance.
    assert classify_datasets("outputs/best_model.pth", None, "MB140 fold 4 strict") == ["mb140"]


# ── lineage rule ────────────────────────────────────────────────────────────

def test_unknown_when_no_dataset_identified():
    assert lineage_of([]) == UNKNOWN


def test_any_noncommercial_dataset_forces_research_lineage():
    assert lineage_of(["mb140"]) == RESEARCH_ONLY
    assert lineage_of(["cholec80", "mb140"]) == RESEARCH_ONLY


def test_product_lineage_requires_all_datasets_commercial(monkeypatch):
    import brsd_lib.data_lineage as dl
    clean = dl.Dataset(key="own", name="Customer video", licence="commercial DUA",
                       commercial_use=True, share_alike=False, source="-", verified="-")
    monkeypatch.setitem(dl.DATASETS, "own", clean)
    assert dl.lineage_of(["own"]) == PRODUCT_SAFE
    # Mixing one NonCommercial dataset in contaminates the whole lineage.
    assert dl.lineage_of(["own", "mb140"]) == RESEARCH_ONLY


# ── hashing ─────────────────────────────────────────────────────────────────

def test_sha256_matches_hashlib(tmp_path):
    f = tmp_path / "blob.bin"
    payload = b"surgical phase transition" * 5000
    f.write_bytes(payload)
    assert sha256_file(f) == hashlib.sha256(payload).hexdigest()


def test_sha256_handles_file_larger_than_one_chunk(tmp_path):
    f = tmp_path / "big.bin"
    payload = b"\xa5" * (3 * (1 << 20) + 17)   # spans several 1 MiB reads
    f.write_bytes(payload)
    assert sha256_file(f, chunk=1 << 20) == hashlib.sha256(payload).hexdigest()


# ── label scanning ──────────────────────────────────────────────────────────

def _write_labels(d: Path):
    d.mkdir(parents=True, exist_ok=True)
    (d / "mb140_fold0_labels_kmeans.json").write_text(json.dumps([
        {"video_id": "BBP01", "split": "train", "phase_sequence": ["a", "b"]},
        {"video_id": "BBP02", "split": "test", "phase_sequence": ["a"]},
        {"video_id": "SBP01", "split": "train", "phase_sequence": ["b"]},
    ]))
    (d / "mb140_fold0_kmeans_artifacts.json").write_text(json.dumps(
        {"K": 6, "seed": 42, "n_features": 63, "n_components": 16,
         "source_labels": "labels/mb140_fold0_labels.json"}))


def test_scan_labels_records_splits_and_centres(tmp_path):
    _write_labels(tmp_path / "labels")
    arts = scan_labels(tmp_path / "labels", tmp_path)
    by = {Path(a.path).name: a for a in arts}

    lab = by["mb140_fold0_labels_kmeans.json"]
    assert lab.kind == "label"
    assert lab.datasets == ["mb140"]
    assert lab.lineage == RESEARCH_ONLY
    assert lab.provenance["n_videos"] == 3
    assert lab.provenance["splits"] == {"test": 1, "train": 2}
    assert lab.provenance["video_id_prefixes"] == {"BBP": 2, "SBP": 1}
    assert lab.sha256 and lab.sha256_source == "computed"


def test_scan_labels_flags_missing_min_df(tmp_path):
    """STRATEGY.md V.3: no stored artifact records min_df."""
    _write_labels(tmp_path / "labels")
    arts = scan_labels(tmp_path / "labels", tmp_path)
    clust = next(a for a in arts if a.kind == "cluster-artifact")
    assert clust.provenance["min_df_recorded"] is False
    assert clust.provenance["K"] == 6
    assert clust.provenance["source_labels"] == "labels/mb140_fold0_labels.json"


def test_scan_labels_survives_corrupt_json(tmp_path):
    d = tmp_path / "labels"
    d.mkdir()
    (d / "mb140_broken.json").write_text("{not json")
    arts = scan_labels(d, tmp_path)
    assert len(arts) == 1
    assert "unreadable" in arts[0].note
    assert arts[0].datasets == ["mb140"]      # still classified from the name


def test_scan_labels_on_missing_directory_is_empty(tmp_path):
    assert scan_labels(tmp_path / "nope", tmp_path) == []


# ── checkpoint scanning ─────────────────────────────────────────────────────

def _write_ckpt(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def test_checkpoint_hash_verified_against_manifest(tmp_path):
    w = tmp_path / "weights"
    digest = _write_ckpt(w / "mb140" / "run033_no_token_seed42.pth", b"weights-a")
    manifest = w / "manifest.json"
    manifest.write_text(json.dumps({
        "mb140_no_token_seed42": {
            "logical_name": "Run 033 strict no-token, fold 0, seed 42",
            "hf_path": "mb140/run033_no_token_seed42.pth",
            "sha256": digest, "produces": 13.17,
            "trained_on": "MB140 fold 0 strict prefix-only protocol",
        }
    }))
    arts = scan_checkpoints([w], tmp_path, manifest, hash_mode="manifest")
    assert len(arts) == 1
    assert arts[0].integrity == "ok"
    assert arts[0].provenance["reported_mae_min"] == 13.17
    assert arts[0].datasets == ["mb140"]


def test_checkpoint_hash_mismatch_is_reported(tmp_path):
    w = tmp_path / "weights"
    _write_ckpt(w / "mb140" / "run033_no_token_seed42.pth", b"weights-a")
    (w / "manifest.json").write_text(json.dumps({
        "k": {"hf_path": "mb140/run033_no_token_seed42.pth", "sha256": "0" * 64,
              "trained_on": "MB140 fold 0"}
    }))
    arts = scan_checkpoints([w], tmp_path, w / "manifest.json", hash_mode="manifest")
    assert arts[0].integrity == "MISMATCH"


def test_raw_training_output_matches_manifest_by_run_directory(tmp_path):
    """Deposit copies are <run>.pth; raw outputs are <run>/best_model.pth."""
    out = tmp_path / "outputs"
    digest = _write_ckpt(out / "run040_strict_decoupled_fold4_seed42" / "best_model.pth", b"w")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "mb140_fold4": {"hf_path": "mb140/run040_strict_decoupled_fold4_seed42.pth",
                        "sha256": digest, "trained_on": "MB140 fold 4"}
    }))
    arts = scan_checkpoints([out], tmp_path, manifest, hash_mode="manifest")
    assert arts[0].provenance["manifest_key"] == "mb140_fold4"
    assert arts[0].integrity == "ok"


def test_symlinked_deposit_is_one_artifact_with_an_alias(tmp_path):
    out = tmp_path / "outputs"
    dep = tmp_path / "weights" / "mb140"
    real = out / "run040_strict_decoupled_fold4_seed42" / "best_model.pth"
    digest = _write_ckpt(real, b"shared-bytes")
    dep.mkdir(parents=True)
    link = dep / "run040_strict_decoupled_fold4_seed42.pth"
    link.symlink_to(real)

    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "mb140_fold4": {"hf_path": "mb140/run040_strict_decoupled_fold4_seed42.pth",
                        "sha256": digest, "trained_on": "MB140 fold 4"}
    }))
    arts = scan_checkpoints([dep.parent, out], tmp_path, manifest, hash_mode="manifest")

    assert len(arts) == 1, "the same bytes must not be counted twice"
    art = arts[0]
    assert art.path.startswith("outputs/"), "canonical path should be the real file"
    assert any("weights/" in a for a in art.aliases)
    assert art.integrity == "ok", "manifest match must survive via the alias name"
    assert "symlink" in art.note


def test_manifest_entry_with_no_file_is_recorded_as_missing(tmp_path):
    w = tmp_path / "weights"
    w.mkdir()
    (w / "manifest.json").write_text(json.dumps({
        "gone": {"hf_path": "mb140/run999_absent.pth", "sha256": "a" * 64,
                 "logical_name": "Run 999", "trained_on": "MB140 fold 0"}
    }))
    arts = scan_checkpoints([w], tmp_path, w / "manifest.json", hash_mode="manifest")
    assert len(arts) == 1
    assert arts[0].integrity == "file-missing"
    assert arts[0].lineage == RESEARCH_ONLY


def test_hash_mode_none_skips_hashing(tmp_path):
    w = tmp_path / "weights"
    _write_ckpt(w / "mb140" / "run033_x.pth", b"w")
    arts = scan_checkpoints([w], tmp_path, None, hash_mode="none")
    assert arts[0].sha256 is None
    assert arts[0].sha256_source == "not-computed"


def test_hash_mode_all_hashes_unlisted_checkpoints(tmp_path):
    w = tmp_path / "weights"
    digest = _write_ckpt(w / "mb140" / "run999_unlisted.pth", b"orphan")
    arts = scan_checkpoints([w], tmp_path, None, hash_mode="all")
    assert arts[0].sha256 == digest
    assert "not listed in weights manifest" in arts[0].note


def test_invalid_hash_mode_rejected(tmp_path):
    with pytest.raises(ValueError, match="none|manifest|all"):
        scan_checkpoints([tmp_path], tmp_path, None, hash_mode="sometimes")


# ── report ──────────────────────────────────────────────────────────────────

def test_markdown_states_the_licence_position(tmp_path):
    _write_labels(tmp_path / "labels")
    md = render_markdown(build_lineage(tmp_path, hash_mode="none"))
    assert "CC BY-NC-SA 4.0" in md
    assert "ShareAlike" in md
    assert "not legal advice" in md.lower()
    # With no commercially-licensed data present, the warning must appear.
    assert "No artifact in this repository is currently product-lineage" in md


def test_build_lineage_counts_are_self_consistent(tmp_path):
    _write_labels(tmp_path / "labels")
    lin = build_lineage(tmp_path, hash_mode="none")
    c = lin["counts"]
    assert c["labels"] + c["checkpoints"] == len(lin["artifacts"])
    assert c["research_lineage"] + c["product_lineage"] + c["unknown_lineage"] \
        == len(lin["artifacts"])


# ── against the real repository ─────────────────────────────────────────────

@pytest.mark.skipif(not (REPO / "labels").is_dir(),
                    reason="label artifacts not present in this checkout")
def test_real_repo_has_no_product_lineage_artifact():
    """The headline claim of DATA_LINEAGE.md, checked against the real tree."""
    lin = build_lineage(REPO, hash_mode="none", hash_labels=False)
    assert lin["counts"]["product_lineage"] == 0
    assert lin["counts"]["unknown_lineage"] == 0, \
        "every artifact should classify; an unknown means the markers need updating"
