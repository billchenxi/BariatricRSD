"""
BariatricRSD Model
==================
Multi-task Transformer framework for joint:
  1. Remaining Surgery Duration (RSD) regression
  2. Intraoperative deviation detection (binary classification)
  3. Surgical phase recognition (multi-class classification)

Architecture:
  Visual Encoder (timm / HecVL) -> Surgformer HTA -> 3 MTL Heads

This is the core model described in the NeurIPS 2026 paper. It replaces the
separate CNN+LSTM models and post-hoc LOWESS deviation detection from the
2019 codebase with a unified end-to-end architecture.
"""

import torch
import torch.nn as nn
from typing import Dict, Optional, Tuple

from bariatric_rsd.models.visual_encoder import VisualEncoder
from bariatric_rsd.models.temporal_model import HierarchicalTemporalAttention


class RSDHead(nn.Module):
    """
    Regression head for Remaining Surgery Duration prediction.
    Predicts a normalized RSD value in [0, 1] for each frame.
    """

    def __init__(self, embed_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.head = nn.Sequential(
            nn.Linear(embed_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, T, D) or (B, D) temporal features.

        Returns:
            (B, T, 1) or (B, 1) RSD predictions.
        """
        return self.head(x)


class DeviationHead(nn.Module):
    """
    Binary classification head for intraoperative deviation detection.
    Predicts deviation probability for each frame.
    """

    def __init__(self, embed_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.head = nn.Sequential(
            nn.Linear(embed_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, T, D) or (B, D) temporal features.

        Returns:
            (B, T, 1) or (B, 1) deviation logits (pre-sigmoid).
        """
        return self.head(x)


class PhaseHead(nn.Module):
    """
    Multi-class classification head for surgical phase recognition.
    This is an auxiliary task that aids feature learning.
    """

    def __init__(self, embed_dim: int, num_phases: int, hidden_dim: int = 256):
        super().__init__()
        self.head = nn.Sequential(
            nn.Linear(embed_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, num_phases),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, T, D) or (B, D) temporal features.

        Returns:
            (B, T, num_phases) or (B, num_phases) phase logits.
        """
        return self.head(x)


class BariatricRSD(nn.Module):
    """
    BariatricRSD: Multi-task Transformer for Surgical Video Analysis.

    End-to-end model combining:
      - HecVL / ResNet visual encoder for per-frame feature extraction
      - Surgformer HTA for temporal modeling with phase-order conditioning
      - Three jointly-trained output heads (RSD, deviation, phase)

    The phase-order token is a learnable embedding that encodes the
    surgeon's procedural style (one of 8 RYGB phase orderings),
    prepended to the temporal sequence as a conditioning signal.
    """

    def __init__(
        self,
        # Visual encoder
        encoder_name: str = "resnet50",
        encoder_pretrained: bool = True,
        encoder_feature_dim: int = 2048,
        freeze_encoder_stages: int = 3,
        # Temporal model
        hta_embed_dim: int = 512,
        hta_num_heads: int = 8,
        hta_depth: int = 4,
        hta_num_scales: int = 3,
        hta_mlp_ratio: float = 4.0,
        hta_dropout: float = 0.1,
        max_seq_len: int = 512,
        # Phase-order embedding
        num_phase_orders: int = 8,
        # Task heads
        rsd_hidden_dim: int = 256,
        deviation_hidden_dim: int = 256,
        num_phases: int = 3,
    ):
        super().__init__()

        # Visual encoder
        self.visual_encoder = VisualEncoder(
            model_name=encoder_name,
            pretrained=encoder_pretrained,
            feature_dim=None,  # use native dim, project in HTA
            freeze_stages=freeze_encoder_stages,
        )
        visual_dim = self.visual_encoder.output_dim

        # Temporal model with hierarchical attention
        self.temporal_model = HierarchicalTemporalAttention(
            input_dim=visual_dim,
            embed_dim=hta_embed_dim,
            num_heads=hta_num_heads,
            depth=hta_depth,
            num_scales=hta_num_scales,
            mlp_ratio=hta_mlp_ratio,
            dropout=hta_dropout,
            max_seq_len=max_seq_len,
            num_phase_orders=num_phase_orders,
        )

        # Multi-task prediction heads
        self.rsd_head = RSDHead(hta_embed_dim, rsd_hidden_dim)
        self.deviation_head = DeviationHead(hta_embed_dim, deviation_hidden_dim)
        self.phase_head = PhaseHead(hta_embed_dim, num_phases)

    def forward(
        self,
        clips: torch.Tensor,
        phase_order_ids: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Full forward pass through the BariatricRSD model.

        Args:
            clips: Video clip tensor of shape (B, T, C, H, W).
            phase_order_ids: Phase-order cluster IDs of shape (B,).

        Returns:
            Dictionary with keys:
              - "rsd": (B, T, 1) normalized RSD predictions
              - "deviation": (B, T, 1) deviation logits
              - "phase": (B, T, num_phases) phase classification logits
        """
        # Extract per-frame visual features
        visual_features = self.visual_encoder(clips)  # (B, T, D)

        # Temporal modeling with phase-order conditioning
        temporal_features = self.temporal_model(
            visual_features, phase_order_ids
        )  # (B, T, embed_dim)

        # Multi-task predictions
        rsd_pred = self.rsd_head(temporal_features)
        deviation_pred = self.deviation_head(temporal_features)
        phase_pred = self.phase_head(temporal_features)

        return {
            "rsd": rsd_pred,
            "deviation": deviation_pred,
            "phase": phase_pred,
        }

    def forward_single_frame(
        self,
        images: torch.Tensor,
        phase_order_ids: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass for single-frame prediction (no temporal context).
        Useful for frame-level evaluation or when temporal context is unavailable.

        Args:
            images: Image tensor of shape (B, C, H, W).
            phase_order_ids: Phase-order cluster IDs of shape (B,).

        Returns:
            Dictionary with single-frame predictions.
        """
        # Add temporal dimension
        clips = images.unsqueeze(1)  # (B, 1, C, H, W)
        outputs = self.forward(clips, phase_order_ids)

        # Remove temporal dimension
        return {k: v.squeeze(1) for k, v in outputs.items()}

    @classmethod
    def from_config(cls, config) -> "BariatricRSD":
        """Create a BariatricRSD model from a configuration object."""
        return cls(
            encoder_name=config.encoder_name,
            encoder_pretrained=config.encoder_pretrained,
            encoder_feature_dim=config.encoder_feature_dim,
            freeze_encoder_stages=config.freeze_encoder_stages,
            hta_embed_dim=config.hta_embed_dim,
            hta_num_heads=config.hta_num_heads,
            hta_depth=config.hta_depth,
            hta_num_scales=config.hta_num_temporal_scales,
            hta_mlp_ratio=config.hta_mlp_ratio,
            hta_dropout=config.hta_dropout,
            num_phase_orders=config.num_phase_orders,
            rsd_hidden_dim=config.rsd_hidden_dim,
            deviation_hidden_dim=config.deviation_hidden_dim,
            num_phases=config.num_phases,
        )


class MultiTaskLoss(nn.Module):
    """
    Combined multi-task loss for BariatricRSD.

    L_total = w_rsd * L_rsd + w_dev * L_deviation + w_phase * L_phase

    Uses:
      - MSE loss for RSD regression
      - Binary cross-entropy with logits for deviation detection
        (with class weighting for imbalance)
      - Cross-entropy for phase recognition
    """

    def __init__(
        self,
        rsd_weight: float = 1.0,
        deviation_weight: float = 0.5,
        phase_weight: float = 0.3,
        deviation_pos_weight: float = 5.0,
    ):
        super().__init__()
        self.rsd_weight = rsd_weight
        self.deviation_weight = deviation_weight
        self.phase_weight = phase_weight

        self.rsd_criterion = nn.MSELoss()
        self.deviation_criterion = nn.BCEWithLogitsLoss(
            pos_weight=torch.tensor([deviation_pos_weight])
        )
        self.phase_criterion = nn.CrossEntropyLoss()

    def forward(
        self,
        predictions: Dict[str, torch.Tensor],
        targets: Dict[str, torch.Tensor],
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Compute multi-task loss.

        Args:
            predictions: Dict with keys "rsd", "deviation", "phase".
            targets: Dict with keys "rsd", "deviation", "phase".

        Returns:
            Tuple of (total_loss, loss_dict) where loss_dict contains
            individual task losses for logging.
        """
        # RSD regression loss. The dataset currently provides a single
        # supervision target per clip, corresponding to the last frame.
        # If frame-wise targets are later provided, use them as-is.
        rsd_pred = predictions["rsd"].squeeze(-1)
        rsd_target = targets["rsd"]
        if rsd_pred.dim() == 2 and rsd_target.dim() == 1:
            rsd_pred = rsd_pred[:, -1]
        loss_rsd = self.rsd_criterion(rsd_pred, rsd_target)

        # Deviation detection loss: mirror the clip-vs-frame handling above.
        dev_pred = predictions["deviation"].squeeze(-1)
        dev_target = targets["deviation"]
        if dev_pred.dim() == 2 and dev_target.dim() == 1:
            dev_pred = dev_pred[:, -1]
        # Move pos_weight to the right device
        self.deviation_criterion.pos_weight = (
            self.deviation_criterion.pos_weight.to(dev_pred.device)
        )
        loss_dev = self.deviation_criterion(dev_pred, dev_target)

        # Phase recognition loss
        phase_pred = predictions["phase"]
        phase_target = targets["phase"]
        if phase_pred.dim() == 3 and phase_target.dim() == 1:
            phase_pred = phase_pred[:, -1, :]
        elif phase_pred.dim() == 3 and phase_target.dim() == 2:
            # (B, T, num_phases) -> (B*T, num_phases)
            B, T, C = phase_pred.shape
            phase_pred = phase_pred.reshape(B * T, C)
            phase_target = phase_target.reshape(B * T)
        loss_phase = self.phase_criterion(phase_pred, phase_target)

        # Weighted total
        total_loss = (
            self.rsd_weight * loss_rsd
            + self.deviation_weight * loss_dev
            + self.phase_weight * loss_phase
        )

        loss_dict = {
            "loss_total": total_loss.item(),
            "loss_rsd": loss_rsd.item(),
            "loss_deviation": loss_dev.item(),
            "loss_phase": loss_phase.item(),
        }

        return total_loss, loss_dict
