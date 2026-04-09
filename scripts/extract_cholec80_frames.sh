#!/bin/bash
# ============================================================
# Extract frames from Cholec80 videos at 1 fps
# ============================================================
# Cholec80 videos are at 25 fps. Extracting all frames would be
# ~4.5M frames total. At 1 fps we get ~180K frames, which is
# manageable and standard for RSD prediction.
#
# Usage:
#   chmod +x scripts/extract_cholec80_frames.sh
#   ./scripts/extract_cholec80_frames.sh /data/cholec80/videos /data/cholec80/frames
# ============================================================

set -e

VIDEO_DIR="${1:-/data/cholec80/videos}"
FRAME_DIR="${2:-/data/cholec80/frames}"
FPS="${3:-1}"  # frames per second to extract

echo "Extracting frames from Cholec80 videos"
echo "  Video dir:  $VIDEO_DIR"
echo "  Frame dir:  $FRAME_DIR"
echo "  FPS:        $FPS"
echo ""

# Check ffmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo "Installing ffmpeg..."
    sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg
fi

# Count videos
VIDEOS=$(ls "$VIDEO_DIR"/video*.mp4 2>/dev/null | wc -l)
if [ "$VIDEOS" -eq 0 ]; then
    echo "ERROR: No video*.mp4 files found in $VIDEO_DIR"
    echo "Download Cholec80 first from http://camma.u-strasbg.fr/datasets"
    exit 1
fi
echo "Found $VIDEOS videos"
echo ""

COUNT=0
for VIDEO_PATH in "$VIDEO_DIR"/video*.mp4; do
    VIDEO_NAME=$(basename "$VIDEO_PATH" .mp4)
    OUT_DIR="$FRAME_DIR/$VIDEO_NAME"
    COUNT=$((COUNT + 1))

    if [ -d "$OUT_DIR" ] && [ "$(ls "$OUT_DIR"/*.jpg 2>/dev/null | wc -l)" -gt 100 ]; then
        echo "[$COUNT/$VIDEOS] $VIDEO_NAME — already extracted, skipping"
        continue
    fi

    mkdir -p "$OUT_DIR"
    echo "[$COUNT/$VIDEOS] $VIDEO_NAME — extracting at ${FPS} fps..."

    ffmpeg -i "$VIDEO_PATH" \
        -vf "fps=$FPS" \
        -q:v 2 \
        -start_number 0 \
        "$OUT_DIR/frame_%06d.jpg" \
        -loglevel warning

    NFRAMES=$(ls "$OUT_DIR"/*.jpg | wc -l)
    echo "  -> $NFRAMES frames"
done

echo ""
echo "Done! Frames saved to $FRAME_DIR"
TOTAL_FRAMES=$(find "$FRAME_DIR" -name "*.jpg" | wc -l)
TOTAL_SIZE=$(du -sh "$FRAME_DIR" | cut -f1)
echo "Total: $TOTAL_FRAMES frames, $TOTAL_SIZE"
