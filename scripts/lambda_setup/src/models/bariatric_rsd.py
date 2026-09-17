"""
src/models/bariatric_rsd.py

BariatricRSD: the full multi-task model.

Architecture:
  1. Visual encoder  — HecVL ViT-B (or fallback: timm ViT-B/16)
  2. Phase-order token — learnable embedding prepended to temporal sequence
  3. Temporal model  — Surgformer HTA (Hierarchical Temporal Attention)
  4. Output heads:
       a. RSD regression          → normalized RSD ∈ [0, 1]
       b. Deviation classification → binary probability
       c. Phase recognition       → multi-class logits
"""

import sys
import math
from pathlib import Path
from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
import timm
from einops import rearrange


NUM_PHASE_ORDER_CLUSTERS = 8


# ── 1. Visual Encoder ─────────────────────────────────────────────────────────

class VisualEncoder(nn.Module):
    """
    ViT-B/16 visual encoder.
    Defaults to timm's ImageNet pretrained ViT; swap checkpoint for HecVL weights.
    
    Input:  [B*T, C, H, W]
    Output: [B*T, embed_dim]  (CLS token representation)
    """

    def __init__(
        self,
        model_name: str = "vit_base_patch16_224",
        pretrained: bool = True,
        checkpoint_path: Optional[str] = None,
        freeze_layers: int = 0,        # freeze first N transformer blocks (0 = train all)
        embed_dim: int = 768,
    ):
        super().__init__()
        self.embed_dim = embed_dim

        # Load base ViT
        self.vit = timm.create_model(
            model_name,
            pretrained=pretrained and checkpoint_path is None,
            num_classes=0,    # remove classification head, get CLS embedding
        )

        # Load custom checkpoint (HecVL or Surgformer's encoder)
        if checkpoint_path and Path(checkpoint_path).exists():
            state = torch.load(checkpoint_path, map_location="cpu")
            # Handle different checkpoint formats
            if "model" in state:
                state = state["model"]
            elif "state_dict" in state:
                state = state["state_dict"]
            # Strip 'visual_encoder.' prefix if present (HecVL format)
            state = {k.replace("visual_encoder.", "").replace("encoder.", ""): v
                     for k, v in state.items()}
            missing, unexpected = self.vit.load_state_dict(state, strict=False)
            print(f"[VisualEncoder] Loaded {checkpoint_path}")
            print(f"  Missing keys: {len(missing)}, Unexpected: {len(unexpected)}")
        elif checkpoint_path:
            print(f"[VisualEncoder] WARNING: checkpoint not found at {checkpoint_path}, using pretrained weights")

        # Optionally freeze early layers to save compute
        if freeze_layers > 0:
            # Freeze patch embedding and first N blocks
            for param in self.vit.patch_embed.parameters():
                param.requires_grad = False
            for i, block in enumerate(self.vit.blocks):
                if i < freeze_layers:
                    for param in block.parameters():
                        param.requires_grad = False
            print(f"[VisualEncoder] Froze patch_embed + first {freeze_layers} blocks")

        # Projection to a common feature dimension
        vit_out_dim = self.vit.embed_dim
        self.proj = nn.Linear(vit_out_dim, embed_dim) if vit_out_dim != embed_dim else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: [B*T, C, H, W] → [B*T, embed_dim]"""
        feats = self.vit(x)    # [B*T, vit_out_dim] — CLS token
        return self.proj(feats)


# ── 2. Phase-Order Token ──────────────────────────────────────────────────────

class PhaseOrderEmbedding(nn.Module):
    """
    Learnable token encoding the surgeon's phase-order style.
    This is the key novel component — no prior RSD paper does this.
    
    Prepended to the temporal sequence as an extra 'context' token.
    """

    def __init__(self, num_clusters: int = NUM_PHASE_ORDER_CLUSTERS, embed_dim: int = 768):
        super().__init__()
        self.embedding = nn.Embedding(num_clusters, embed_dim)
        nn.init.normal_(self.embedding.weight, std=0.02)

    def forward(self, cluster_ids: torch.Tensor) -> torch.Tensor:
        """cluster_ids: [B] → [B, 1, embed_dim]"""
        return self.embedding(cluster_ids).unsqueeze(1)


# ── 3. Hierarchical Temporal Attention (simplified HTA) ───────────────────────
# This is inspired by Surgformer's HTA block.
# For production, swap in the full Surgformer implementation.

class HTABlock(nn.Module):
    """
    Hierarchical Temporal Attention block.
    Captures temporal information at multiple resolutions.
    """

    def __init__(self, embed_dim: int = 768, num_heads: int = 12, dropout: float = 0.1):
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)

        # Short-range attention (local temporal context)
        self.short_attn = nn.MultiheadAttention(embed_dim, num_heads, dropout=dropout, batch_first=True)
        # Long-range attention (global temporal context)
        self.long_attn = nn.MultiheadAttention(embed_dim, num_heads, dropout=dropout, batch_first=True)
        # Fusion of short + long range
        self.fusion = nn.Linear(embed_dim * 2, embed_dim)
        # FFN
        self.ffn = nn.Sequential(
            nn.Linear(embed_dim, embed_dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(embed_dim * 4, embed_dim),
            nn.Dropout(dropout),
        )
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: [B, T+1, embed_dim]  (T frames + 1 phase-order token)"""
        residual = x
        x = self.norm1(x)

        # Short-range: attend within a window of half the sequence
        T = x.shape[1]
        half = max(T // 2, 1)
        short_out, _ = self.short_attn(x[:, :half], x[:, :half], x[:, :half])
        # Pad to full length
        short_out = F.pad(short_out, (0, 0, 0, T - half))

        # Long-range: attend across the full sequence
        long_out, _ = self.long_attn(x, x, x)

        # Fuse
        fused = self.fusion(torch.cat([short_out, long_out], dim=-1))
        x = residual + self.dropout(fused)

        # FFN
        x = x + self.dropout(self.ffn(self.norm2(x)))
        return x


class TemporalTransformer(nn.Module):
    """
    Stack of HTA blocks operating on the frame sequence.
    Input: frame embeddings + phase-order token
    Output: sequence representation (CLS = phase-order token position)
    """

    def __init__(
        self,
        embed_dim: int = 768,
        num_layers: int = 6,
        num_heads: int = 12,
        dropout: float = 0.1,
        max_seq_len: int = 64,
    ):
        super().__init__()
        self.positional_encoding = nn.Parameter(
            torch.zeros(1, max_seq_len + 1, embed_dim)  # +1 for phase-order token
        )
        nn.init.trunc_normal_(self.positional_encoding, std=0.02)

        self.blocks = nn.ModuleList([
            HTABlock(embed_dim, num_heads, dropout)
            for _ in range(num_layers)
        ])
        self.norm = nn.LayerNorm(embed_dim)
        self.embed_dim = embed_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: [B, T+1, embed_dim]  (T+1 because phase-order token is prepended)
        Returns: [B, T+1, embed_dim]
        """
        T = x.shape[1]
        x = x + self.positional_encoding[:, :T, :]
        for block in self.blocks:
            x = block(x)
        return self.norm(x)


# ── 4. Output Heads ───────────────────────────────────────────────────────────

class RSDHead(nn.Module):
    """Regresses normalized RSD ∈ [0, 1]."""
    def __init__(self, embed_dim: int = 768):
        super().__init__()
        self.head = nn.Sequential(
            nn.Linear(embed_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 1),
            nn.Sigmoid(),  # output in [0, 1]
        )
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: [B, embed_dim] → [B]"""
        return self.head(x).squeeze(-1)


class DeviationHead(nn.Module):
    """Binary classifier: is this moment a deviation from normal workflow?"""
    def __init__(self, embed_dim: int = 768):
        super().__init__()
        self.head = nn.Sequential(
            nn.Linear(embed_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1),
        )
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: [B, embed_dim] → [B]  (logits, apply sigmoid externally)"""
        return self.head(x).squeeze(-1)


class PhaseHead(nn.Module):
    """Multi-class phase classifier (auxiliary task)."""
    def __init__(self, embed_dim: int = 768, num_phases: int = 12):
        super().__init__()
        self.head = nn.Linear(embed_dim, num_phases)
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: [B, embed_dim] → [B, num_phases]"""
        return self.head(x)


# ── 5. Full BariatricRSD Model ────────────────────────────────────────────────

class BariatricRSD(nn.Module):
    """
    The full multi-task model.

    Forward pass:
      frames:               [B, T, C, H, W]
      phase_order_cluster:  [B]     — int cluster ID [0..7]

    Returns dict:
      rsd:       [B]   — normalized RSD prediction [0, 1]
      deviation: [B]   — deviation logits
      phase:     [B, num_phases]  — phase logits
    """

    def __init__(
        self,
        encoder_checkpoint: Optional[str] = None,
        encoder_freeze_layers: int = 6,
        embed_dim: int = 768,
        temporal_layers: int = 6,
        temporal_heads: int = 12,
        dropout: float = 0.1,
        num_phases: int = 12,
        num_phase_order_clusters: int = NUM_PHASE_ORDER_CLUSTERS,
        decouple_phase_head: bool = False,
    ):
        super().__init__()

        self.decouple_phase_head = decouple_phase_head
        self.encoder = VisualEncoder(
            checkpoint_path=encoder_checkpoint,
            freeze_layers=encoder_freeze_layers,
            embed_dim=embed_dim,
        )
        self.phase_order_embed = PhaseOrderEmbedding(num_phase_order_clusters, embed_dim)
        self.temporal = TemporalTransformer(
            embed_dim=embed_dim,
            num_layers=temporal_layers,
            num_heads=temporal_heads,
            dropout=dropout,
        )
        self.rsd_head = RSDHead(embed_dim)
        self.deviation_head = DeviationHead(embed_dim)
        self.phase_head = PhaseHead(embed_dim, num_phases)

        self._init_weights()
        self._log_param_count()

    def _init_weights(self):
        for name, m in self.named_modules():
            if "encoder" in name:
                continue  # skip — pretrained
            if isinstance(m, nn.Linear):
                nn.init.trunc_normal_(m.weight, std=0.02)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.LayerNorm):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

    def _log_param_count(self):
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        print(f"[BariatricRSD] Total params: {total/1e6:.1f}M  |  Trainable: {trainable/1e6:.1f}M")

    def encode_frames(self, frames: torch.Tensor) -> torch.Tensor:
        """frames: [B, T, C, H, W] → [B, T, embed_dim]"""
        B, T, C, H, W = frames.shape
        flat = rearrange(frames, "b t c h w -> (b t) c h w")
        feats = self.encoder(flat)               # [B*T, embed_dim]
        return rearrange(feats, "(b t) d -> b t d", b=B, t=T)

    def forward(
        self,
        frames: torch.Tensor,
        phase_order_cluster: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:

        # 1. Extract per-frame visual features
        frame_feats = self.encode_frames(frames)       # [B, T, D]

        # 2. Prepend phase-order token
        order_token = self.phase_order_embed(phase_order_cluster)  # [B, 1, D]
        seq = torch.cat([order_token, frame_feats], dim=1)          # [B, T+1, D]

        # 3. Temporal Transformer
        out = self.temporal(seq)                       # [B, T+1, D]

        # 4. Use phase-order token position (index 0) as the global representation
        # This aggregates information from the whole sequence via attention
        global_feat = out[:, 0, :]                    # [B, D]

        # 5. Task heads. In the decoupled variant, the phase head reads visual
        # features before workflow-token mixing so the causal evaluator is not
        # circular with respect to the supplied cluster token.
        if self.decouple_phase_head:
            phase_feat = frame_feats.mean(dim=1)
        else:
            phase_feat = global_feat
        return {
            "rsd": self.rsd_head(global_feat),             # [B]
            "deviation": self.deviation_head(global_feat), # [B]  (logits)
            "phase": self.phase_head(phase_feat),          # [B, num_phases]
        }


# ── Multi-task loss ───────────────────────────────────────────────────────────

class BariatricRSDLoss(nn.Module):
    """
    Weighted multi-task loss:
      L = w_rsd * L_rsd  +  w_dev * L_deviation  +  w_phase * L_phase

    Weights are initialized with uncertainty-based automatic weighting
    (Kendall et al. 2018) and learned jointly.
    """

    def __init__(
        self,
        rsd_weight: float = 1.0,
        deviation_weight: float = 2.0,   # upweight — deviation is rare
        phase_weight: float = 0.5,       # auxiliary task
        pos_weight_deviation: float = 5.0,  # class imbalance: deviations are rare
        learn_weights: bool = True,
    ):
        super().__init__()

        if learn_weights:
            # Log-variance parameterization for uncertainty weighting
            self.log_var_rsd = nn.Parameter(torch.tensor(0.0))
            self.log_var_dev = nn.Parameter(torch.tensor(0.0))
            self.log_var_phase = nn.Parameter(torch.tensor(0.0))
        else:
            self.register_buffer("log_var_rsd", torch.tensor(0.0))
            self.register_buffer("log_var_dev", torch.tensor(0.0))
            self.register_buffer("log_var_phase", torch.tensor(0.0))
            self.rsd_weight = rsd_weight
            self.deviation_weight = deviation_weight
            self.phase_weight = phase_weight

        self.learn_weights = learn_weights
        self.bce = nn.BCEWithLogitsLoss(
            pos_weight=torch.tensor([pos_weight_deviation])
        )
        self.ce = nn.CrossEntropyLoss(label_smoothing=0.1)

    def forward(
        self,
        preds: Dict[str, torch.Tensor],
        targets: Dict[str, torch.Tensor],
    ) -> Dict[str, torch.Tensor]:

        rsd_pred = preds["rsd"]
        rsd_target = targets["rsd_normalized"]
        dev_pred = preds["deviation"]
        dev_target = targets["is_deviation"]
        phase_pred = preds["phase"]
        phase_target = targets["phase_label"]

        # Task losses
        l_rsd = F.mse_loss(rsd_pred, rsd_target)
        l_dev = self.bce(dev_pred, dev_target)
        l_phase = self.ce(phase_pred, phase_target)

        if self.learn_weights:
            # Uncertainty weighting: L = exp(-log_var) * task_loss + log_var
            w_rsd = torch.exp(-self.log_var_rsd)
            w_dev = torch.exp(-self.log_var_dev)
            w_phase = torch.exp(-self.log_var_phase)
            total = (w_rsd * l_rsd + self.log_var_rsd +
                     w_dev * l_dev + self.log_var_dev +
                     w_phase * l_phase + self.log_var_phase)
        else:
            total = (self.rsd_weight * l_rsd +
                     self.deviation_weight * l_dev +
                     self.phase_weight * l_phase)

        return {
            "loss": total,
            "loss_rsd": l_rsd,
            "loss_deviation": l_dev,
            "loss_phase": l_phase,
        }
