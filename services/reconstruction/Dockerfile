# Self-hosted reconstruction pipeline — CUDA container (M1-CAPT-03, ADR-0005).
#
# Runs the headless SfM -> gsplat -> compress -> mesh pipeline on a GPU host
# (rented serverless/spot or owned). NOT built in CI (no GPU). All components
# are MIT/BSD/Apache-2.0 (SECURITY_CHECKLIST §7.3); INRIA 3DGS and SuGaR are
# excluded (ADR-0005) and enforced by reconstruction.licenses. Exact versions
# are recorded in research/vendors/reconstruction-spike-report.md.
#
# LAYERS. Each "modal-layer: <name>" marker comment starts a section that
# modal_app.py builds as its own cached Modal image layer (Modal otherwise
# builds a whole Dockerfile as ONE layer, so any edit rebuilt the ~17 min gsplat
# compile). Order = least- to most-frequently changed. Comment-only edits do not
# invalidate a layer (modal_app.py drops comment lines before hashing). The
# final "modal-skip" section is for a plain `docker build` only: on Modal the
# `reconstruction/` package is mounted at container start instead, so code
# edits never rebuild the image.

# modal-layer: base
FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

# /opt/venv (Python 3.11) is first on PATH, so `python` and `pip` resolve to the
# interpreter that has torch/gsplat/nerfstudio/open3d. Modal requires `python` +
# `pip` on PATH and runs the function with it. PYTHONPATH=/work makes the
# `reconstruction` package importable. QT_QPA_PLATFORM=offscreen keeps any
# Qt-linked tool headless. /opt/colmap/bin (the CUDA COLMAP, layer `colmap`) is
# APPENDED to PATH so its conda env (which has its own python) never shadows
# the venv. GJ_COLMAP_CUDA=1: COLMAP is a CUDA build, so SIFT extraction and
# matching run on the GPU (modal_app.py / sfm.py).
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH:/opt/colmap/bin \
    PYTHONPATH=/work \
    QT_QPA_PLATFORM=offscreen \
    GJ_COLMAP_CUDA=1

# Python 3.11 comes from the deadsnakes PPA: Ubuntu 22.04's own python3.11 is a
# 3.11.0 release candidate, which lacks tarfile's extraction `filter=` (3.11.4+)
# used by modal_app.py. bzip2 is for the micromamba bootstrap (layer `colmap`).
RUN apt-get update && apt-get install -y --no-install-recommends \
        software-properties-common gpg-agent \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
        python3.11 python3.11-venv python3.11-dev \
        git curl ca-certificates bzip2 libgl1 libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && python3.11 -m venv /opt/venv \
    && python -c "import sys, tarfile; assert sys.version_info >= (3, 11, 4) and hasattr(tarfile, 'data_filter'), sys.version"

# Node 22 for @playcanvas/splat-transform (MIT): PLY -> .spz/.sog. splat-transform
# 3.x requires Node >= 22; the unscoped npm name "splat-transform" does not exist.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @playcanvas/splat-transform@3.6.4 \
    && splat-transform --version

# modal-layer: torch
# torch (CUDA 12.4) — BSD-style. torchvision is pinned from the same cu124 index
# so nerfstudio's torchvision requirement cannot pull a newer PyPI torch.
RUN python -m pip install --upgrade pip==24.2 setuptools wheel ninja \
    && python -m pip install torch==2.4.1 torchvision==0.19.1 \
        --index-url https://download.pytorch.org/whl/cu124

# modal-layer: gsplat
# gsplat 1.4.0 (Apache-2.0) ships only a pure-Python PyPI wheel (CUDA kernels are
# JIT-compiled on first use, i.e. on billed GPU time) and its sdist lacks the glm
# submodule; prebuilt wheels exist only for cp310. So compile the CUDA extension
# here, from the tagged source, for A100 (8.0), A10G (8.6) and L4/L40S (8.9). No
# GPU is needed to compile. This is the slow (~15 min) layer.
ENV TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9" \
    MAX_JOBS=4
RUN git clone --depth 1 --branch v1.4.0 --recurse-submodules --shallow-submodules \
        https://github.com/nerfstudio-project/gsplat.git /tmp/gsplat \
    && python -m pip install --no-build-isolation /tmp/gsplat \
    && rm -rf /tmp/gsplat

# modal-layer: nerfstudio
# nerfstudio (Splatfacto) — Apache-2.0; open3d — MIT. numpy<2: open3d 0.18 is
# built against the numpy 1.x ABI.
RUN python -m pip install \
        gsplat==1.4.0 \
        nerfstudio==1.1.5 \
        open3d==0.18.0 \
        numpy==1.26.4 \
        torch==2.4.1 \
        torchvision==0.19.1 \
    && ns-train --help > /dev/null \
    && python -c "import open3d, gsplat, torch; print('torch', torch.__version__, 'gsplat', gsplat.__version__, 'open3d', open3d.__version__)"

# modal-layer: colmap
# SfM: COLMAP 4.1.1 (BSD-3-Clause), CUDA 12.9 build from conda-forge, in its own
# prefix (/opt/colmap) so its libraries never mix with the venv. COLMAP >= 4.0
# ships the GLOMAP global mapper as `colmap global_mapper` (GLOMAP is maintained
# inside COLMAP since 4.0), so no separate glomap binary is needed.
# - CONDA_OVERRIDE_CUDA lets the solver pick the CUDA variant on a GPU-less
#   builder; at run time the CUDA 12.9 runtime needs an R525+ driver
#   (minor-version compatibility), which Modal's GPU hosts exceed.
# - CONDA_OVERRIDE_ARCHSPEC=x86_64_v3 pins the CPU micro-architecture level
#   (AVX2/FMA, which every Modal GPU host has). Without it the solver picks
#   packages tuned for the BUILDER's CPU (x86_64_v4 / AVX-512 on Modal's
#   builders), and `colmap` dies with SIGILL on a GPU host without AVX-512.
# - openimageio=3.1 is listed explicitly: the conda-forge colmap 4.1.x builds
#   link libOpenImageIO.so.3.1 but do not declare it (they still declare
#   freeimage), so without it `colmap` fails to load.
# - The vocabulary tree (sequential-matcher loop detection, vocab_tree_matcher)
#   is baked in, checksum-pinned, at the path COLMAP's own downloader caches it
#   to, so runs never depend on a GitHub download.
# This layer sits after the Python stack so a COLMAP bump never recompiles gsplat.
ENV MAMBA_ROOT_PREFIX=/opt/micromamba
RUN curl -fsSL https://micro.mamba.pm/api/micromamba/linux-64/2.3.2 \
        | tar -xj -C /usr/local bin/micromamba \
    && CONDA_OVERRIDE_CUDA=12.9 CONDA_OVERRIDE_ARCHSPEC=x86_64_v3 micromamba create -y -p /opt/colmap -c conda-forge \
        --strict-channel-priority "colmap=4.1.1=cuda_129ha585b08_4" "openimageio=3.1" \
    && test -f /opt/colmap/conda-meta/_x86_64-microarch-level-3-*_x86_64_v3.json \
    && micromamba clean -a -y \
    && colmap help 2>&1 | head -n 1 | grep -q "with CUDA" \
    && colmap global_mapper -h > /dev/null
RUN mkdir -p /root/.cache/colmap \
    && cd /root/.cache/colmap \
    && curl -fsSL -o 96ca8ec8ea60b1f73465aaf2c401fd3b3ca75cdba2d3c50d6a2f6f760f275ddc-vocab_tree_faiss_flickr100K_words256K.bin \
        https://github.com/colmap/colmap/releases/download/3.11.1/vocab_tree_faiss_flickr100K_words256K.bin \
    && echo "96ca8ec8ea60b1f73465aaf2c401fd3b3ca75cdba2d3c50d6a2f6f760f275ddc  96ca8ec8ea60b1f73465aaf2c401fd3b3ca75cdba2d3c50d6a2f6f760f275ddc-vocab_tree_faiss_flickr100K_words256K.bin" \
        | sha256sum -c -

# modal-skip
WORKDIR /work
COPY reconstruction ./reconstruction

# Default: show the license manifest gate. The spike driver invokes
# reconstruction.pipeline.run_pipeline with the real adapters.
CMD ["python", "-c", "from reconstruction import assert_commercial_safe; print('license gate OK:', len(assert_commercial_safe()), 'components')"]
