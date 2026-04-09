"""
BariatricRSD Configuration
==========================
Central configuration for the BariatricRSD project.
All hyperparameters, paths, and model settings are defined here.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class DataConfig:
    """Dataset and data loading configuration."""
    video_root: str = ""
    annotation_json: str = ""
    frame_extension: str = "jpg"
    image_size: int = 224
    frames_per_clip: int = 16
    frame_sampling_rate: int = 4  # sample every Nth frame
    train_ratio: float = 0.8
    val_ratio: float = 0.1
    random_seed: int = 444
    num_workers: int = 8
    batch_size: int = 16

    # RYGB surgical phases
    phase_names: List[str] = field(default_factory=lambda: [
        "Gastric pouch creation",
        "Gastro-jejunal anastomosis",
        "Jejuno-jejunal anastomosis",
    ])

    # 8 distinct phase orderings discovered in the 2019 data
    phase_order_clusters: int = 8

    # Whether to remove out-of-body frames
    remove_out_of_body: bool = True


@dataclass
class ModelConfig:
    """Model architecture configuration."""
    # Visual encoder
    encoder_name: str = "resnet50"  # or "hecvl" when weights available
    encoder_pretrained: bool = True
    encoder_feature_dim: int = 2048  # ResNet50 output dim
    freeze_encoder_stages: int = 3  # freeze first N stages

    # Temporal model (Hierarchical Temporal Attention)
    hta_embed_dim: int = 512
    hta_num_heads: int = 8
    hta_depth: int = 4
    hta_mlp_ratio: float = 4.0
    hta_dropout: float = 0.1
    hta_num_temporal_scales: int = 3  # multi-scale temporal attention

    # Phase-order embedding
    num_phase_orders: int = 8
    phase_order_embed_dim: int = 512  # matches hta_embed_dim

    # Multi-task heads
    rsd_hidden_dim: int = 256
    deviation_hidden_dim: int = 256
    num_phases: int = 3  # GPC, GJA, JJA
    deviation_classes: int = 2  # normal / deviation


@dataclass
class TrainingConfig:
    """Training configuration."""
    max_epochs: int = 100
    learning_rate: float = 1e-4
    weight_decay: float = 1e-4
    warmup_epochs: int = 5
    lr_scheduler: str = "cosine"  # cosine, step
    step_size: int = 30
    step_gamma: float = 0.1
    early_stopping_patience: int = 15
    gradient_clip_val: float = 1.0

    # Multi-task loss weights
    rsd_loss_weight: float = 1.0
    deviation_loss_weight: float = 0.5
    phase_loss_weight: float = 0.3

    # Deviation class weights (imbalanced: deviations are rare)
    deviation_pos_weight: float = 5.0

    # Checkpointing
    checkpoint_dir: str = "checkpoints"
    save_every_n_epochs: int = 5
    log_every_n_steps: int = 50

    # Device
    device: str = "cuda"
    mixed_precision: bool = True


@dataclass
class EvalConfig:
    """Evaluation configuration."""
    output_dir: str = "results"
    deviation_threshold: float = 0.5
    smoothing_window: int = 15  # median filter window for deviation smoothing
    min_deviation_duration: int = 30  # minimum frames for a valid deviation segment
