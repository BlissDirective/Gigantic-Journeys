#!/usr/bin/env bash
# In-pod bootstrap for the Runpod benchmark (runpod_bench.py), on the public
# nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04 image (the Dockerfile's base).
#
# FALLBACK for the private GHCR image: the Operator PAT has no `packages` scope
# (GHCR push denied 2026-09-28), so instead of pulling ghcr.io/blissdirective/gj-recon
# this installs the Dockerfile's stack at pod start. Same pins (torch 2.4.1 cu124,
# gsplat 1.4.0, nerfstudio 1.1.5, open3d 0.18.0, numpy 1.26.4, COLMAP 4.1.1 CUDA
# conda-forge build, splat-transform 3.6.4, pinned vocab tree) with two differences:
#   - Python 3.10 (Ubuntu 22.04's 3.10.12, which has tarfile's data filter) instead
#     of 3.11 (deadsnakes), so gsplat comes from its PREBUILT cp310 wheel
#     (gsplat-1.4.0+pt24cu124) instead of the ~15 min source compile;
#   - install time (~5-10 min) is billed pod time; it is reported separately and
#     NOT counted in the per-scene numbers.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
t0=$(date +%s)
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
    python3.10 python3.10-venv python3.10-dev git curl ca-certificates bzip2 libgl1 libgomp1 \
    > /dev/null
python3.10 -m venv /opt/venv
. /opt/venv/bin/activate
python -c "import sys, tarfile; assert hasattr(tarfile, 'data_filter'), sys.version"

# Node 22 + splat-transform, pip stack and COLMAP in parallel (independent prefixes).
(curl -fsSL https://deb.nodesource.com/setup_22.x | bash - > /dev/null \
    && apt-get install -y -qq --no-install-recommends nodejs > /dev/null \
    && npm install -g --silent @playcanvas/splat-transform@3.6.4 > /dev/null \
    && splat-transform --version) > /root/setup-node.log 2>&1 &
node_pid=$!

(python -m pip install -q --upgrade pip==24.2 setuptools wheel ninja \
    && python -m pip install -q torch==2.4.1 torchvision==0.19.1 \
        --index-url https://download.pytorch.org/whl/cu124 \
    && python -m pip install -q "gsplat==1.4.0+pt24cu124" \
        --extra-index-url https://docs.gsplat.studio/whl/pt24cu124 \
    && python -m pip install -q gsplat==1.4.0+pt24cu124 nerfstudio==1.1.5 open3d==0.18.0 \
        numpy==1.26.4 torch==2.4.1 torchvision==0.19.1 \
        --extra-index-url https://docs.gsplat.studio/whl/pt24cu124 \
    && ns-train --help > /dev/null \
    && python -c "import open3d, gsplat, torch; print('torch', torch.__version__, 'gsplat', gsplat.__version__, 'open3d', open3d.__version__, 'cuda', torch.cuda.is_available())") \
    > /root/setup-pip.log 2>&1 &
pip_pid=$!

(export MAMBA_ROOT_PREFIX=/opt/micromamba \
    && curl -fsSL https://micro.mamba.pm/api/micromamba/linux-64/2.3.2 | tar -xj -C /usr/local bin/micromamba \
    && CONDA_OVERRIDE_CUDA=12.9 CONDA_OVERRIDE_ARCHSPEC=x86_64_v3 micromamba create -q -y -p /opt/colmap \
        -c conda-forge --strict-channel-priority "colmap=4.1.1=cuda_129ha585b08_4" "openimageio=3.1" \
    && micromamba clean -a -y -q \
    && mkdir -p /root/.cache/colmap && cd /root/.cache/colmap \
    && f=96ca8ec8ea60b1f73465aaf2c401fd3b3ca75cdba2d3c50d6a2f6f760f275ddc-vocab_tree_faiss_flickr100K_words256K.bin \
    && curl -fsSL -o "$f" https://github.com/colmap/colmap/releases/download/3.11.1/vocab_tree_faiss_flickr100K_words256K.bin \
    && echo "96ca8ec8ea60b1f73465aaf2c401fd3b3ca75cdba2d3c50d6a2f6f760f275ddc  $f" | sha256sum -c - \
    && QT_QPA_PLATFORM=offscreen /opt/colmap/bin/colmap help 2>&1 | head -n 1 \
    && QT_QPA_PLATFORM=offscreen /opt/colmap/bin/colmap global_mapper -h > /dev/null) \
    > /root/setup-colmap.log 2>&1 &
colmap_pid=$!

rc=0
wait $node_pid || { echo "node/splat-transform FAILED"; tail -20 /root/setup-node.log; rc=1; }
wait $pip_pid || { echo "pip stack FAILED"; tail -20 /root/setup-pip.log; rc=1; }
wait $colmap_pid || { echo "colmap FAILED"; tail -20 /root/setup-colmap.log; rc=1; }
cat /root/setup-node.log /root/setup-pip.log /root/setup-colmap.log | grep -E "^(torch|COLMAP|[0-9]+\.[0-9]+)" || true
cat > /root/gj-env.sh <<'ENV'
export VIRTUAL_ENV=/opt/venv PATH=/opt/venv/bin:$PATH:/opt/colmap/bin PYTHONPATH=/root/gj
export QT_QPA_PLATFORM=offscreen GJ_COLMAP_CUDA=1 PYTHONUNBUFFERED=1
ENV
echo "setup_s=$(( $(date +%s) - t0 )) rc=$rc"
exit $rc
