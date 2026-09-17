"""
Basic tests for BariatricRSD model components.

Run with: pytest tests/ -v
"""

import torch
import pytest


def test_visual_encoder_forward():
    """Test that the visual encoder produces correct output shapes."""
    from bariatric_rsd.models.visual_encoder import VisualEncoder

    encoder = VisualEncoder(model_name="resnet18", pretrained=False)
    # Single image batch
    x = torch.randn(2, 3, 224, 224)
    out = encoder(x)
    assert out.dim() == 2
    assert out.shape[0] == 2

    # Clip batch (B, T, C, H, W)
    x_clip = torch.randn(2, 8, 3, 224, 224)
    out_clip = encoder(x_clip)
    assert out_clip.dim() == 3
    assert out_clip.shape[:2] == (2, 8)


def test_temporal_model_forward():
    """Test HTA forward pass with and without phase-order tokens."""
    from bariatric_rsd.models.temporal_model import HierarchicalTemporalAttention

    hta = HierarchicalTemporalAttention(
        input_dim=512, embed_dim=256, num_heads=4, depth=2,
        num_scales=3, max_seq_len=64, num_phase_orders=8,
    )
    x = torch.randn(2, 16, 512)
    out = hta(x)
    assert out.shape == (2, 16, 256)

    # With phase-order IDs
    order_ids = torch.tensor([0, 3])
    out_cond = hta(x, order_ids)
    assert out_cond.shape == (2, 16, 256)


def test_full_model_forward():
    """Test end-to-end BariatricRSD forward pass."""
    from bariatric_rsd.models.bariatric_rsd import BariatricRSD

    model = BariatricRSD(
        encoder_name="resnet18",
        encoder_pretrained=False,
        hta_embed_dim=256,
        hta_num_heads=4,
        hta_depth=2,
        num_phase_orders=4,
        num_phases=3,
    )
    clips = torch.randn(2, 8, 3, 224, 224)
    order_ids = torch.tensor([0, 1])

    outputs = model(clips, order_ids)

    assert "rsd" in outputs
    assert "deviation" in outputs
    assert "phase" in outputs
    assert outputs["rsd"].shape[:2] == (2, 8)
    assert outputs["deviation"].shape[:2] == (2, 8)
    assert outputs["phase"].shape == (2, 8, 3)


def test_multitask_loss():
    """Test multi-task loss computation."""
    from bariatric_rsd.models.bariatric_rsd import MultiTaskLoss

    criterion = MultiTaskLoss(rsd_weight=1.0, deviation_weight=0.5, phase_weight=0.3)

    predictions = {
        "rsd": torch.randn(2, 8, 1),
        "deviation": torch.randn(2, 8, 1),
        "phase": torch.randn(2, 8, 3),
    }
    targets = {
        "rsd": torch.rand(2),
        "deviation": torch.zeros(2),
        "phase": torch.randint(0, 3, (2,)),
    }

    total_loss, loss_dict = criterion(predictions, targets)
    assert total_loss.dim() == 0  # scalar
    assert total_loss.item() > 0
    assert "loss_rsd" in loss_dict
    assert "loss_deviation" in loss_dict
    assert "loss_phase" in loss_dict


def test_operation_logger():
    """Test the operation log generator."""
    from bariatric_rsd.inference.operation_log import OperationLogger

    phase_names = ["GPC", "GJA", "JJA"]
    logger = OperationLogger(phase_names=phase_names, procedure_type="RYGB")

    # Simulate a short surgery
    for t in range(0, 60):
        phase = "GPC" if t < 20 else ("GJA" if t < 40 else "JJA")
        rsd = t / 60.0
        dev = 0.8 if 25 <= t <= 30 else 0.1
        logger.update(float(t), phase, rsd, dev)

    report = logger.generate_report()
    assert "INTRAOPERATIVE OPERATION LOG" in report
    assert "RYGB" in report

    json_report = logger.generate_json()
    assert "metadata" in json_report
    assert "phases" in json_report
    assert "events" in json_report
    assert json_report["metadata"]["procedure"] == "RYGB"

    # Repeated export should not duplicate finalized events or segments.
    phases_before = len(json_report["phases"])
    events_before = len(json_report["events"])
    json_report_again = logger.generate_json()
    assert len(json_report_again["phases"]) == phases_before
    assert len(json_report_again["events"]) == events_before


def test_parse_cholec80_annotations_normalizes_video_ids(tmp_path):
    """Cholec80 annotation stems should map to extracted frame folder names."""
    from bariatric_rsd.data.annotation_parser import parse_cholec80_annotations

    annotation_file = tmp_path / "video01-phase.txt"
    annotation_file.write_text(
        "Frame Phase\n"
        "0 Preparation\n"
        "25 Preparation\n"
        "50 CalotTriangleDissection\n"
    )

    annotations = parse_cholec80_annotations(str(tmp_path), fps=25.0)

    assert "video01" in annotations
    assert "Preparation" in annotations["video01"]


def test_config_dataclasses():
    """Test configuration dataclass defaults."""
    from bariatric_rsd.config import DataConfig, ModelConfig, TrainingConfig

    dc = DataConfig()
    assert dc.image_size == 224
    assert dc.random_seed == 444
    assert len(dc.phase_names) == 3

    mc = ModelConfig()
    assert mc.encoder_name == "resnet50"
    assert mc.hta_embed_dim == 512

    tc = TrainingConfig()
    assert tc.learning_rate == 1e-4
    assert tc.mixed_precision is True
