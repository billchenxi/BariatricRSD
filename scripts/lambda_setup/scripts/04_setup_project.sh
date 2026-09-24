#!/bin/bash
# ============================================================
# 04_setup_project.sh
# Creates the full project directory structure and
# copies source files into place.
# ============================================================
set -e

PROJECT_ROOT="$HOME/bariatric-rsd"
mkdir -p "$PROJECT_ROOT"/{src/{data,models,training,utils},configs,data/{raw,processed,splits},outputs/{checkpoints,logs,predictions},notebooks}

echo "==> Project structure:"
find "$PROJECT_ROOT" -maxdepth 3 -type d | sort | sed 's|'"$PROJECT_ROOT"'||' | sed 's|^/||'

# Write a .env file for paths
cat > "$PROJECT_ROOT/.env" << EOF
# BariatricRSD project environment variables
PROJECT_ROOT=$PROJECT_ROOT
DATA_ROOT=$PROJECT_ROOT/data
WEIGHTS_DIR=$PROJECT_ROOT/weights
OUTPUTS_DIR=$PROJECT_ROOT/outputs
WANDB_PROJECT=bariatric-rsd-neurips2026

# External repos
SURGFORMER_DIR=$PROJECT_ROOT/extern/Surgformer
HECVL_DIR=$PROJECT_ROOT/extern/HecVL
MULTIBYPASS_DIR=$PROJECT_ROOT/extern/MultiBypass140

# Your bariatric dataset (update this path to where you place your 4000+ videos)
BARIATRIC_DATA=/data/bariatric_surgery
CHOLEC80_DATA=/data/cholec80
MULTIBYPASS_DATA=/data/multibypass140
EOF

echo "==> Created .env at $PROJECT_ROOT/.env"
echo "    Update BARIATRIC_DATA, CHOLEC80_DATA, MULTIBYPASS_DATA to your actual data paths"

# Write a setup.py so the src package is importable
cat > "$PROJECT_ROOT/setup.py" << 'SETUPEOF'
from setuptools import setup, find_packages
setup(
    name="bariatric_rsd",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
SETUPEOF

cd "$PROJECT_ROOT" && pip install -e . -q

echo ""
echo "Project scaffold ready. Source files will be created by the next step."
echo "Now run:"
echo "  python scripts/05_smoke_test.py"
