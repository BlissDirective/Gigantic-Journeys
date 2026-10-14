#!/usr/bin/env bash
# In-pod bootstrap for the item-6 phase-1 MapAnything A/B (runpod_mapanything.py), on the
# public nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04 image. Same pins as the Modal app
# (mapanything_ab_app.py): torch 2.5.1 cu124, map-anything @ the pinned commit, the
# pinned Apache checkpoint revision. No COLMAP / nerfstudio: phase 1 trains nothing.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
: "${MA_CODE:?}" "${MA_REV:?}"
t0=$(date +%s)
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
    python3.10 python3.10-venv python3.10-dev git curl ca-certificates libgl1 libglib2.0-0 > /dev/null
python3.10 -m venv /opt/venv
. /opt/venv/bin/activate
python -m pip install -q --upgrade pip==24.2 setuptools wheel
python -m pip install -q torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu124
python -m pip install -q "git+https://github.com/facebookresearch/map-anything@${MA_CODE}"
python -c "from mapanything.models import MapAnything; MapAnything.from_pretrained('facebook/map-anything-apache', revision='${MA_REV}')"
python -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())"
cat > /root/gj-env.sh <<'ENV'
export VIRTUAL_ENV=/opt/venv PATH=/opt/venv/bin:$PATH PYTHONPATH=/root/gj PYTHONUNBUFFERED=1
ENV
echo "setup_s=$(( $(date +%s) - t0 ))"
