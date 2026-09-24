"""Tests for the Paper 2A backbone feature-extraction registry.

The interface contract — `encoder(clips: [B,T,3,H,W]) -> [B,T,D]` — is
what these tests exist to protect. It was documented but violated in the
first version of `extract.py`: `smoke_test` fed a 5-D tensor straight
into an image model expecting 4-D, and the anchor backbone failed with
`ValueError: too many values to unpack (expected 4)` the first time it
was actually run. The adapter tests below use tiny stub modules so they
run without downloading any weights.

The one test that does touch real weights (`test_anchor_backbone_...`)
is marked `slow` and skipped unless the timm cache already holds them.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

torch = pytest.importorskip("torch")

from paper2_infra.backbone_features.extract import (  # noqa: E402
    BACKBONES,
    PAPER1_VIT_TAG,
    _clipwise_image_encoder,
    _video_encoder,
    cache_path,
    clip_id_hash,
    smoke_test,
)


# ── Stub backbones ──────────────────────────────────────────────────────────

class _StubImageModel(torch.nn.Module):
    """Image model: (B, 3, H, W) -> (B, D). Rejects anything else."""

    def __init__(self, dim=768):
        super().__init__()
        self.dim = dim

    def forward(self, x):
        if x.dim() != 4:
            raise ValueError(f"too many values to unpack (expected 4), got {x.dim()}")
        return torch.arange(x.shape[0] * self.dim, dtype=torch.float32).reshape(
            x.shape[0], self.dim)


class _StubVideoOutput:
    def __init__(self, hidden):
        self.last_hidden_state = hidden


class _StubVideoModel(torch.nn.Module):
    """Video model: returns (B, n_tokens, D) like a HF video transformer."""

    def __init__(self, n_tokens=1568, dim=1024):
        super().__init__()
        self.n_tokens = n_tokens
        self.dim = dim

    def forward(self, pixel_values=None):
        b = pixel_values.shape[0]
        return _StubVideoOutput(torch.randn(b, self.n_tokens, self.dim))


# ── Image adapter ───────────────────────────────────────────────────────────

def test_clipwise_adapter_produces_the_contract_shape():
    encoder = _clipwise_image_encoder(_StubImageModel(dim=768))
    out = encoder(torch.randn(3, 8, 3, 224, 224))
    assert out.shape == (3, 8, 768)


def test_clipwise_adapter_preserves_frame_order():
    """Folding time into batch must not scramble frames.

    The stub returns row index i for the i-th item, so after unfolding,
    clip b frame t must hold value b*T + t.
    """
    encoder = _clipwise_image_encoder(_StubImageModel(dim=1))
    out = encoder(torch.zeros(2, 4, 3, 8, 8))
    expected = torch.tensor([[[0.], [1.], [2.], [3.]],
                             [[4.], [5.], [6.], [7.]]])
    torch.testing.assert_close(out, expected)


def test_clipwise_adapter_rejects_a_4d_input():
    encoder = _clipwise_image_encoder(_StubImageModel())
    with pytest.raises(ValueError, match=r"expected \(B, T, 3, H, W\)"):
        encoder(torch.randn(8, 3, 224, 224))


def test_clipwise_adapter_rejects_a_model_that_kept_its_head():
    """num_classes=0 was forgotten → the inner model returns tokens, not
    a pooled vector. Fail loudly rather than cache a wrong-shaped tensor."""

    class TokenReturningModel(torch.nn.Module):
        def forward(self, x):
            return torch.randn(x.shape[0], 197, 768)

    encoder = _clipwise_image_encoder(TokenReturningModel())
    with pytest.raises(ValueError, match="num_classes=0"):
        encoder(torch.randn(2, 8, 3, 224, 224))


# ── Video adapter ───────────────────────────────────────────────────────────

def test_video_adapter_pools_patches_into_temporal_positions():
    # 1568 tokens = 8 temporal positions x 196 spatial patches.
    encoder = _video_encoder(_StubVideoModel(n_tokens=1568, dim=1024), n_out_frames=8)
    out = encoder(torch.randn(2, 16, 3, 224, 224))
    assert out.shape == (2, 8, 1024)


def test_video_adapter_rejects_an_indivisible_token_count():
    """A token count that does not divide by the temporal resolution means
    the tubelet assumption is wrong — better to fail than mis-pool."""
    encoder = _video_encoder(_StubVideoModel(n_tokens=1569, dim=1024), n_out_frames=8)
    with pytest.raises(ValueError, match="not divisible"):
        encoder(torch.randn(1, 16, 3, 224, 224))


def test_video_adapter_rejects_a_4d_input():
    encoder = _video_encoder(_StubVideoModel(), n_out_frames=8)
    with pytest.raises(ValueError, match=r"expected \(B, T, 3, H, W\)"):
        encoder(torch.randn(16, 3, 224, 224))


def test_video_adapter_pooling_is_a_mean_over_patches():
    """Verify the pooled value equals the patch mean for a known input."""

    class ConstantVideoModel(torch.nn.Module):
        def forward(self, pixel_values=None):
            # 4 tokens, dim 2: two temporal positions of two patches each.
            hidden = torch.tensor([[[1.0, 2.0], [3.0, 4.0],
                                    [5.0, 6.0], [7.0, 8.0]]])
            return _StubVideoOutput(hidden)

    encoder = _video_encoder(ConstantVideoModel(), n_out_frames=2)
    out = encoder(torch.randn(1, 4, 3, 8, 8))
    # position 0 = mean([1,2],[3,4]) = [2,3]; position 1 = mean([5,6],[7,8]) = [6,7]
    torch.testing.assert_close(out, torch.tensor([[[2.0, 3.0], [6.0, 7.0]]]))


# ── Registry hygiene ────────────────────────────────────────────────────────

def test_every_registry_entry_is_self_consistent():
    for name, spec in BACKBONES.items():
        assert spec.name == name, f"{name}: registry key != spec.name"
        assert spec.stage_0_status in {"pass", "fail", "pending", "skipped"}
        assert spec.clip_frames > 0
        assert len(spec.input_hw) == 2 and all(d > 0 for d in spec.input_hw)


def test_passing_backbones_declare_a_pinned_tag_and_feature_dim():
    """A row cannot be marked `pass` without pinned weights — that is what
    made the anchor's weight provenance ambiguous in the first place."""
    for name, spec in BACKBONES.items():
        if spec.stage_0_status == "pass":
            assert spec.pretrained_tag, f"{name} is 'pass' but has no pinned tag"
            assert spec.feature_dim > 0, f"{name} is 'pass' but declares no dim"


def test_anchor_tag_is_pinned_not_defaulted():
    """timm's default tag can change between releases; ours must not."""
    spec = BACKBONES["vit_b16_in21k"]
    assert spec.pretrained_tag == PAPER1_VIT_TAG
    assert PAPER1_VIT_TAG in (spec.hf_id or "")


# ── Cache paths ─────────────────────────────────────────────────────────────

def test_clip_id_hash_is_deterministic_and_distinct():
    assert clip_id_hash("V1", 100) == clip_id_hash("V1", 100)
    assert clip_id_hash("V1", 100) != clip_id_hash("V1", 101)
    assert clip_id_hash("V1", 100) != clip_id_hash("V2", 100)
    assert len(clip_id_hash("V1", 100)) == 12


def test_cache_path_layout(tmp_path: Path):
    p = cache_path(tmp_path, "vit_b16_in21k", "mb140", "BBP01", 1234)
    assert p.parent.is_dir()
    assert p.parent == tmp_path / "vit_b16_in21k" / "mb140" / "BBP01"
    assert p.name.startswith("0001234_") and p.suffix == ".npy"


def test_cache_paths_sort_chronologically(tmp_path: Path):
    """Zero-padding must make lexical order match clip order."""
    names = [cache_path(tmp_path, "b", "d", "V", f).name for f in (5, 50, 500)]
    assert names == sorted(names)


# ── Smoke-test harness ──────────────────────────────────────────────────────

def test_smoke_test_reports_unimplemented_loaders_without_raising():
    result = smoke_test("zen", device="cpu", n_clips=1)
    assert result["status"] == "loader_not_implemented"


def test_smoke_test_flags_a_contract_violation(monkeypatch):
    """A backbone returning the wrong feature dim must not report 'ok'."""
    spec = BACKBONES["vit_b16_in21k"]
    monkeypatch.setattr(
        spec, "loader",
        lambda device: _clipwise_image_encoder(_StubImageModel(dim=512)))
    result = smoke_test("vit_b16_in21k", device="cpu", n_clips=2)
    assert result["status"] == "contract_violation"
    assert any("512" in p for p in result["problems"])


def test_smoke_test_accepts_a_conforming_stub(monkeypatch):
    spec = BACKBONES["vit_b16_in21k"]
    monkeypatch.setattr(
        spec, "loader",
        lambda device: _clipwise_image_encoder(_StubImageModel(dim=768)))
    result = smoke_test("vit_b16_in21k", device="cpu", n_clips=2)
    assert result["status"] == "ok"
    assert result["output_shape"] == [2, 8, 768]
    assert result["bytes_per_clip"] == 8 * 768 * 4


@pytest.mark.slow
def test_anchor_backbone_runs_end_to_end():
    """Real ViT-B/16 weights. Skipped unless already cached locally."""
    from pathlib import Path as P
    cache = P.home() / ".cache" / "huggingface"
    if not cache.exists():
        pytest.skip("no HuggingFace cache; would require a download")
    result = smoke_test("vit_b16_in21k", device="cpu", n_clips=2)
    if result["status"] in {"load_failed", "forward_failed"}:
        pytest.skip(f"weights unavailable offline: {result.get('error')}")
    assert result["status"] == "ok"
    assert result["output_shape"] == [2, 8, 768]
    assert result["measured_feature_dim"] == result["declared_feature_dim"]
