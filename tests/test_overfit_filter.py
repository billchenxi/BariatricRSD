import json

import pytest

pd = pytest.importorskip("pandas")

from brsd_lib.overfit_filter import (
    assert_all_train_videos_have_selection,
    estimate_sequence_samples,
    select_by_overfit_residuals,
    standardize_residual_table,
    summarize_manifest_after_selection,
    write_filtered_manifest,
)


def test_standardize_residual_table_aliases_and_abs_residual():
    df = pd.DataFrame(
        {
            "video_name": ["A", "A"],
            "img_path": ["a/0001.jpg", "a/0002.jpg"],
            "pred": [0.2, 0.8],
            "actual": [0.1, 0.5],
        }
    )

    out = standardize_residual_table(df)

    assert {"video_id", "frame_path", "prediction", "target", "abs_residual"} <= set(out.columns)
    assert out["video_id"].tolist() == ["A", "A"]
    assert out["frame_path"].tolist() == ["a/0001.jpg", "a/0002.jpg"]
    assert out["abs_residual"].tolist() == pytest.approx([0.1, 0.3])


def test_select_by_overfit_residuals_uses_per_video_std_threshold():
    residual_df = pd.DataFrame(
        {
            "video_id": ["A", "A", "A", "A", "B", "B"],
            "frame_path": ["a1", "a2", "a3", "a4", "b1", "b2"],
            "abs_residual": [0.0, 0.1, 0.5, 1.0, 0.2, 0.2],
        }
    )

    selected_df, stats_df = select_by_overfit_residuals(residual_df, k=1.0)

    assert selected_df["frame_path"].tolist() == ["a1", "a2", "b1", "b2"]
    assert selected_df["selection_reason"].tolist() == [
        "std_threshold",
        "std_threshold",
        "degenerate_scale_keep_all",
        "degenerate_scale_keep_all",
    ]

    stats_by_video = stats_df.set_index("video_id")
    assert stats_by_video.loc["A", "n_kept"] == 2
    assert stats_by_video.loc["B", "n_kept"] == 2
    assert stats_by_video.loc["B", "reason"] == "degenerate_scale_keep_all"


def test_select_by_overfit_residuals_can_fallback_to_quantile():
    residual_df = pd.DataFrame(
        {
            "video_id": ["A", "A", "A", "A"],
            "frame_path": ["a1", "a2", "a3", "a4"],
            "abs_residual": [1.0, 1.0, 1.0, 4.0],
        }
    )

    selected_df, stats_df = select_by_overfit_residuals(
        residual_df,
        k=0.5,
        min_keep_frac=0.5,
        fallback_quantile=0.5,
    )

    assert selected_df["frame_path"].tolist() == ["a1", "a2", "a3"]
    assert set(selected_df["selection_reason"]) == {"fallback_quantile_0.5"}
    assert stats_df.loc[0, "n_kept"] == 3
    assert stats_df.loc[0, "kept_frac"] == pytest.approx(0.75)


def test_write_filtered_manifest_filters_train_only_and_summarizes(tmp_path):
    videos = [
        {
            "video_id": "train_vid",
            "split": "train",
            "frames": [
                {"frame_path": "train/0001.jpg"},
                {"frame_path": "train/0002.jpg"},
                {"frame_path": "train/0003.jpg"},
            ],
        },
        {
            "video_id": "val_vid",
            "split": "val",
            "frames": [
                {"frame_path": "val/0001.jpg"},
                {"frame_path": "val/0002.jpg"},
                {"frame_path": "val/0003.jpg"},
            ],
        },
    ]
    selected_df = pd.DataFrame(
        {
            "video_id": ["train_vid", "train_vid"],
            "frame_path": ["train/0001.jpg", "train/0003.jpg"],
            "abs_residual": [0.1, 0.2],
        }
    )

    summary_df = summarize_manifest_after_selection(
        videos,
        selected_df,
        sequence_len=1,
        frame_stride=1,
    )
    out_path = tmp_path / "filtered_manifest.json"
    write_filtered_manifest(videos, selected_df, out_path, k=0.385)

    written = json.loads(out_path.read_text())
    train_video = written[0]
    val_video = written[1]

    assert [frame["frame_path"] for frame in train_video["frames"]] == [
        "train/0001.jpg",
        "train/0003.jpg",
    ]
    assert train_video["selection_method"]["name"] == "controlled_overfit_residual_filter"
    assert val_video["frames"] == videos[1]["frames"]
    assert val_video["selection_method"]["name"] == "not_filtered_eval_split"

    summary_by_video = summary_df.set_index("video_id")
    assert summary_by_video.loc["train_vid", "old_frames"] == 3
    assert summary_by_video.loc["train_vid", "new_frames"] == 2
    assert summary_by_video.loc["train_vid", "old_samples_est"] == estimate_sequence_samples(3, 1, 1)
    assert summary_by_video.loc["train_vid", "new_samples_est"] == estimate_sequence_samples(2, 1, 1)
    assert summary_by_video.loc["val_vid", "new_frames"] == 3


def test_assert_all_train_videos_have_selection_raises_for_missing_video():
    videos = [
        {"video_id": "train_vid", "split": "train", "frames": []},
        {"video_id": "val_vid", "split": "val", "frames": []},
    ]
    selected_df = pd.DataFrame({"video_id": ["other"], "frame_path": ["x"]})

    with pytest.raises(ValueError, match="missing 1 training videos"):
        assert_all_train_videos_have_selection(videos, selected_df)
