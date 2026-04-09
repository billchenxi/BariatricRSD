"""
Visual Encoder
==============
Visual feature extraction backbone for surgical video frames.

Replaces the proprietary transfer_model.py initialize_model() and
PostProcess1D from the 2019 codebase. Uses the `timm` library for
modern, well-maintained pretrained models.

Supports:
  - ResNet variants (ResNet18/50/101) as baseline encoders
  - Any timm-supported model for plug-and-play experimentation
  - Placeholder for HecVL surgical foundation model weights

When HecVL pretrained weights become available, load them via:
    encoder = VisualEncoder(model_name="resnet50")
    encoder.load_hecvl_weights("path/to/hecvl_checkpoint.pth")
"""

import torch
import torch.nn as nn
from typing import Optional, Tuple

try:
    import timm
except ImportError:
    raise ImportError("timm is required: pip install timm")


class VisualEncoder(nn.Module):
    """
    Visual feature extractor using pretrained CNN/ViT backbones from timm.

    Outputs a fixed-dimensional feature vector per input frame.
    The final classification head is removed, leaving only the
    feature extraction layers.
    """

    def __init__(
        self,
        model_name: str = "resnet50",
        pretrained: bool = True,
        feature_dim: Optional[int] = None,
        freeze_stages: int = 0,
        drop_rate: float = 0.0,
    ):
        """
        Args:
            model_name: Name of the timm model (e.g., "resnet50", "resnet18",
                        "efficientnet_b0", "swin_tiny_patch4_window7_224").
            pretrained: Whether to load ImageNet pretrained weights.
            feature_dim: If specified, project features to this dimension.
                         If None, use the model's native output dimension.
            freeze_stages: Number of stages to freeze (0 = train all).
                          For ResNet: stages are [conv1+bn1, layer1, layer2, layer3, layer4]
            drop_rate: Dropout rate before the projection layer.
        """
        super().__init__()

        # Create model without classification head
        self.backbone = timm.create_model(
            model_name,
            pretrained=pretrained,
            num_classes=0,  # removes the classification head
            drop_rate=drop_rate,
        )

        # Get the native feature dimension
        self.native_dim = self.backbone.num_features

        # Optional projection to a target feature dimension
        self.projection = None
        if feature_dim is not None and feature_dim != self.native_dim:
            self.projection = nn.Sequential(
                nn.Linear(self.native_dim, feature_dim),
                nn.LayerNorm(feature_dim),
                nn.GELU(),
            )
            self.output_dim = feature_dim
        else:
            self.output_dim = self.native_dim

        # Freeze early stages
        if freeze_stages > 0:
            self._freeze_stages(freeze_stages)

    def _freeze_stages(self, num_stages: int):
        """Freeze the first `num_stages` of the backbone."""
        # For ResNet-family models
        if hasattr(self.backbone, "conv1"):
            frozen_modules = []
            if num_stages >= 1:
                frozen_modules.extend([self.backbone.conv1, self.backbone.bn1])
            if num_stages >= 2 and hasattr(self.backbone, "layer1"):
                frozen_modules.append(self.backbone.layer1)
            if num_stages >= 3 and hasattr(self.backbone, "layer2"):
                frozen_modules.append(self.backbone.layer2)
            if num_stages >= 4 and hasattr(self.backbone, "layer3"):
                frozen_modules.append(self.backbone.layer3)

            for module in frozen_modules:
                for param in module.parameters():
                    param.requires_grad = False

        # For ViT/Swin-family models
        elif hasattr(self.backbone, "patch_embed"):
            # Freeze patch embedding
            if num_stages >= 1:
                for param in self.backbone.patch_embed.parameters():
                    param.requires_grad = False
            # Freeze transformer blocks
            if hasattr(self.backbone, "blocks"):
                total_blocks = len(self.backbone.blocks)
                blocks_to_freeze = min(
                    int(total_blocks * num_stages / 5), total_blocks
                )
                for i in range(blocks_to_freeze):
                    for param in self.backbone.blocks[i].parameters():
                        param.requires_grad = False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extract visual features from input images.

        Args:
            x: Image tensor of shape (B, C, H, W) or (B, T, C, H, W).
               If 5D, frames are processed independently then reshaped.

        Returns:
            Feature tensor of shape (B, D) or (B, T, D).
        """
        is_temporal = x.dim() == 5
        if is_temporal:
            B, T, C, H, W = x.shape
            x = x.reshape(B * T, C, H, W)

        features = self.backbone(x)  # (B*T, native_dim)

        if self.projection is not None:
            features = self.projection(features)  # (B*T, output_dim)

        if is_temporal:
            features = features.reshape(B, T, -1)

        return features

    def load_hecvl_weights(self, checkpoint_path: str):
        """
        Load HecVL surgical foundation model weights.

        HecVL (MICCAI 2024) provides a visual encoder pre-trained on 300 hours
        of surgical lecture videos. When available, these weights provide
        better surgical visual representations than ImageNet initialization.

        Args:
            checkpoint_path: Path to the HecVL checkpoint file.
        """
        checkpoint = torch.load(checkpoint_path, map_location="cpu")

        # HecVL typically saves the visual encoder under a specific key
        if "visual_encoder" in checkpoint:
            state_dict = checkpoint["visual_encoder"]
        elif "model" in checkpoint:
            state_dict = checkpoint["model"]
        elif "state_dict" in checkpoint:
            state_dict = checkpoint["state_dict"]
        else:
            state_dict = checkpoint

        # Filter out classification head weights
        state_dict = {
            k: v
            for k, v in state_dict.items()
            if not k.startswith("head") and not k.startswith("fc")
        }

        # Load with strict=False to allow missing projection layers
        missing, unexpected = self.backbone.load_state_dict(
            state_dict, strict=False
        )
        if missing:
            print(f"HecVL loading - missing keys: {missing[:5]}...")
        if unexpected:
            print(f"HecVL loading - unexpected keys: {unexpected[:5]}...")

        print(f"Loaded HecVL weights from {checkpoint_path}")


class TemporalConv1DPostProcessor(nn.Module):
    """
    1D convolutional post-processor for smoothing frame-level features
    over time. Replaces the proprietary PostProcess1D.

    This is provided as a lightweight temporal baseline alternative
    to the full Surgformer HTA model.
    """

    def __init__(
        self,
        in_features: int,
        out_features: int = 1,
        kernel_size: int = 5,
        hidden_dim: int = 128,
    ):
        super().__init__()
        padding = (kernel_size - 1) // 2  # same padding

        self.temporal_conv = nn.Sequential(
            nn.BatchNorm1d(in_features),
            nn.GELU(),
            nn.Dropout(0.3),
            nn.Conv1d(in_features, hidden_dim, kernel_size, padding=padding),
            nn.GELU(),
            nn.Conv1d(hidden_dim, out_features, kernel_size=1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, T, C) temporal feature sequence.

        Returns:
            (B, T, out_features) temporally smoothed predictions.
        """
        x = x.permute(0, 2, 1)  # (B, C, T)
        x = self.temporal_conv(x)  # (B, out, T)
        return x.permute(0, 2, 1)  # (B, T, out)
