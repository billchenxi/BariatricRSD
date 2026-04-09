"""
Hierarchical Temporal Attention (HTA)
=====================================
Transformer-based temporal model inspired by Surgformer (MICCAI 2024).

Replaces the BiLSTM temporal model from the 2019 codebase with a modern
Transformer architecture that captures both local and global temporal
context at multiple resolutions.

Key design choices from Surgformer:
  - Multi-scale temporal attention (local + global context)
  - Sparse frame sampling for handling long surgical videos
  - Learnable temporal position embeddings
  - Phase-order token: a novel learnable token that encodes the surgeon's
    procedural style (one of 8 distinct RYGB phase orderings)

Reference:
    Yang et al., "Surgformer: Surgical Transformer with Hierarchical
    Temporal Attention for Surgical Phase Recognition," MICCAI 2024.

This is a clean reimplementation using standard PyTorch and einops,
with NO code copied from the Surgformer repository.
"""

import math
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    from einops import rearrange, repeat
except ImportError:
    raise ImportError("einops is required: pip install einops")


class MultiScaleTemporalAttention(nn.Module):
    """
    Multi-scale temporal attention block.

    Computes attention at multiple temporal scales by partitioning the
    sequence into windows of different sizes, allowing the model to
    capture both fine-grained local patterns and coarse global context.
    """

    def __init__(
        self,
        embed_dim: int,
        num_heads: int,
        num_scales: int = 3,
        dropout: float = 0.1,
    ):
        """
        Args:
            embed_dim: Dimension of input embeddings.
            num_heads: Number of attention heads per scale.
            num_scales: Number of temporal scales.
            dropout: Attention dropout rate.
        """
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.num_scales = num_scales
        self.head_dim = embed_dim // num_heads
        self.scale_factor = self.head_dim ** -0.5

        assert embed_dim % num_heads == 0, "embed_dim must be divisible by num_heads"

        # Per-scale Q, K, V projections
        self.qkv_projections = nn.ModuleList(
            [
                nn.Linear(embed_dim, embed_dim * 3)
                for _ in range(num_scales)
            ]
        )

        # Output projection combining all scales
        self.output_proj = nn.Linear(embed_dim * num_scales, embed_dim)
        self.attn_dropout = nn.Dropout(dropout)
        self.proj_dropout = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            x: Input tensor of shape (B, T, D).
            mask: Optional attention mask.

        Returns:
            Output tensor of shape (B, T, D).
        """
        B, T, D = x.shape
        scale_outputs = []

        for scale_idx in range(self.num_scales):
            # Determine window size for this scale
            # Scale 0: local (window=T//4), Scale 1: medium, Scale 2: global (full)
            if self.num_scales == 1 or scale_idx == self.num_scales - 1:
                window_size = T
            else:
                window_size = max(
                    4, T // (2 ** (self.num_scales - 1 - scale_idx))
                )

            qkv = self.qkv_projections[scale_idx](x)
            qkv = rearrange(
                qkv, "b t (three h d) -> three b h t d",
                three=3, h=self.num_heads, d=self.head_dim,
            )
            q, k, v = qkv[0], qkv[1], qkv[2]

            if window_size < T:
                # Windowed attention: average-pool K and V to window_size
                # This creates a coarser temporal representation
                k_pooled = F.adaptive_avg_pool1d(
                    rearrange(k, "b h t d -> (b h) d t"), window_size
                )
                k_pooled = rearrange(
                    k_pooled, "(b h) d t -> b h t d", b=B, h=self.num_heads
                )
                v_pooled = F.adaptive_avg_pool1d(
                    rearrange(v, "b h t d -> (b h) d t"), window_size
                )
                v_pooled = rearrange(
                    v_pooled, "(b h) d t -> b h t d", b=B, h=self.num_heads
                )

                attn_weights = torch.matmul(q, k_pooled.transpose(-2, -1))
                attn_weights = attn_weights * self.scale_factor
                attn_weights = F.softmax(attn_weights, dim=-1)
                attn_weights = self.attn_dropout(attn_weights)
                attn_out = torch.matmul(attn_weights, v_pooled)
            else:
                # Full attention
                attn_weights = torch.matmul(q, k.transpose(-2, -1))
                attn_weights = attn_weights * self.scale_factor
                if mask is not None:
                    attn_weights = attn_weights.masked_fill(
                        mask == 0, float("-inf")
                    )
                attn_weights = F.softmax(attn_weights, dim=-1)
                attn_weights = self.attn_dropout(attn_weights)
                attn_out = torch.matmul(attn_weights, v)

            attn_out = rearrange(attn_out, "b h t d -> b t (h d)")
            scale_outputs.append(attn_out)

        # Concatenate outputs from all scales and project
        combined = torch.cat(scale_outputs, dim=-1)  # (B, T, D * num_scales)
        output = self.output_proj(combined)  # (B, T, D)
        output = self.proj_dropout(output)

        return output


class HTABlock(nn.Module):
    """
    Single Hierarchical Temporal Attention block.

    Consists of:
      1. Multi-scale temporal attention with residual connection
      2. Feed-forward network (MLP) with residual connection
      3. Layer normalization (pre-norm style)
    """

    def __init__(
        self,
        embed_dim: int,
        num_heads: int,
        num_scales: int = 3,
        mlp_ratio: float = 4.0,
        dropout: float = 0.1,
    ):
        super().__init__()

        self.norm1 = nn.LayerNorm(embed_dim)
        self.attention = MultiScaleTemporalAttention(
            embed_dim=embed_dim,
            num_heads=num_heads,
            num_scales=num_scales,
            dropout=dropout,
        )

        self.norm2 = nn.LayerNorm(embed_dim)
        mlp_hidden = int(embed_dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(embed_dim, mlp_hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_hidden, embed_dim),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, T, D) input sequence.

        Returns:
            (B, T, D) output sequence.
        """
        x = x + self.attention(self.norm1(x))
        x = x + self.mlp(self.norm2(x))
        return x


class HierarchicalTemporalAttention(nn.Module):
    """
    Full Hierarchical Temporal Attention model for surgical video
    temporal modeling.

    Takes a sequence of visual features (from VisualEncoder) and produces
    temporally-contextualized representations suitable for downstream
    multi-task prediction heads.

    Includes:
      - Learnable temporal position embeddings
      - Phase-order token: conditions the model on the surgeon's procedural style
      - Stack of HTA blocks with multi-scale temporal attention
    """

    def __init__(
        self,
        input_dim: int,
        embed_dim: int = 512,
        num_heads: int = 8,
        depth: int = 4,
        num_scales: int = 3,
        mlp_ratio: float = 4.0,
        dropout: float = 0.1,
        max_seq_len: int = 512,
        num_phase_orders: int = 8,
    ):
        """
        Args:
            input_dim: Dimension of input visual features.
            embed_dim: Transformer embedding dimension.
            num_heads: Number of attention heads.
            depth: Number of HTA blocks.
            num_scales: Number of temporal attention scales.
            mlp_ratio: MLP hidden dim ratio.
            dropout: Dropout rate.
            max_seq_len: Maximum sequence length for position embeddings.
            num_phase_orders: Number of distinct phase ordering clusters.
        """
        super().__init__()

        self.embed_dim = embed_dim

        # Input projection
        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, embed_dim),
            nn.LayerNorm(embed_dim),
        )

        # Learnable temporal position embeddings
        self.pos_embed = nn.Parameter(
            torch.randn(1, max_seq_len, embed_dim) * 0.02
        )

        # Phase-order token: learnable embedding conditioned on the
        # surgeon's procedural style (8 clusters from the 2019 data)
        # This is prepended to the sequence, similar to a CLS token.
        self.phase_order_embed = nn.Embedding(num_phase_orders, embed_dim)

        # Dropout after embeddings
        self.embed_dropout = nn.Dropout(dropout)

        # Stack of HTA blocks
        self.blocks = nn.ModuleList(
            [
                HTABlock(
                    embed_dim=embed_dim,
                    num_heads=num_heads,
                    num_scales=num_scales,
                    mlp_ratio=mlp_ratio,
                    dropout=dropout,
                )
                for _ in range(depth)
            ]
        )

        # Final layer norm
        self.norm = nn.LayerNorm(embed_dim)

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize weights with truncated normal and zeros."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.trunc_normal_(m.weight, std=0.02)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.LayerNorm):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(
        self,
        x: torch.Tensor,
        phase_order_ids: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            x: Visual features of shape (B, T, input_dim).
            phase_order_ids: Phase-order cluster IDs of shape (B,).
                            If None, a default cluster (0) is used.

        Returns:
            Temporally-contextualized features of shape (B, T, embed_dim).
            The first token position contains the phase-order token output.
        """
        B, T, _ = x.shape

        # Project input features to embedding dimension
        x = self.input_proj(x)  # (B, T, embed_dim)

        # Add temporal position embeddings
        x = x + self.pos_embed[:, :T, :]

        # Prepend phase-order token
        if phase_order_ids is None:
            phase_order_ids = torch.zeros(B, dtype=torch.long, device=x.device)

        order_tokens = self.phase_order_embed(phase_order_ids)  # (B, embed_dim)
        order_tokens = order_tokens.unsqueeze(1)  # (B, 1, embed_dim)
        x = torch.cat([order_tokens, x], dim=1)  # (B, 1+T, embed_dim)

        x = self.embed_dropout(x)

        # Pass through HTA blocks
        for block in self.blocks:
            x = block(x)

        x = self.norm(x)

        # Remove the phase-order token, return only temporal features
        # The phase-order token's information has been mixed into all positions
        temporal_features = x[:, 1:, :]  # (B, T, embed_dim)

        return temporal_features

    def forward_with_order_token(
        self,
        x: torch.Tensor,
        phase_order_ids: Optional[torch.Tensor] = None,
    ) -> tuple:
        """
        Same as forward, but also returns the phase-order token output.

        Returns:
            Tuple of:
              - temporal_features: (B, T, embed_dim)
              - order_token_output: (B, embed_dim) - the processed phase-order token
        """
        B, T, _ = x.shape
        x = self.input_proj(x)
        x = x + self.pos_embed[:, :T, :]

        if phase_order_ids is None:
            phase_order_ids = torch.zeros(B, dtype=torch.long, device=x.device)

        order_tokens = self.phase_order_embed(phase_order_ids).unsqueeze(1)
        x = torch.cat([order_tokens, x], dim=1)
        x = self.embed_dropout(x)

        for block in self.blocks:
            x = block(x)

        x = self.norm(x)

        order_token_output = x[:, 0, :]  # (B, embed_dim)
        temporal_features = x[:, 1:, :]  # (B, T, embed_dim)

        return temporal_features, order_token_output
