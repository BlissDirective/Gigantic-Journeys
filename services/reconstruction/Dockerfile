# Self-hosted reconstruction pipeline — CUDA container (M1-CAPT-03, ADR-0005).
#
# Runs the headless SfM -> gsplat -> compress -> mesh pipeline on a GPU host
# (rented serverless/spot or owned). NOT built in CI (no GPU); it is built and
# its pins are validated on the GPU box during the spike. All components are
# MIT/BSD/Apache-2.0 (SECURITY_CHECKLIST §7.3); INRIA 3DGS and SuGaR are
# excluded (ADR-0005) and enforced by reconstruction.licenses.
#
# Pins below are the starting point; bump/confirm them during the spike and
# record the exact versions in research/vendors/reconstruction-spike-report.md.

FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

# /opt/venv (Python 3.11) is first on PATH, so `python` and `pip` resolve to the
# interpreter that has torch/gsplat/nerfstudio/open3d. Modal (from_dockerfile)
# requires `python` + `pip` on PATH and runs the function with it.
# PYTHONPATH=/work makes the `reconstruction` package importable in the function.
# QT_QPA_PLATFORM=offscreen lets the Qt-linked apt COLMAP run headless.
# GJ_COLMAP_CUDA=0: the apt COLMAP has no CUDA, so SIFT runs on CPU (modal_app.py).
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/work \
    QT_QPA_PLATFORM=offscreen \
    GJ_COLMAP_CUDA=0

# System + SfM. COLMAP is BSD-3-Clause. The Ubuntu 22.04 apt COLMAP (3.7) is
# built WITHOUT CUDA, so SIFT extraction/matching run on CPU (slow). GLOMAP is
# NOT installed (no apt package); modal_app.py defaults to --sfm colmap. A
# CUDA COLMAP (+ GLOMAP) is a follow-up, see OPERATOR_RUNBOOK.md.
# Python 3.11 comes from the deadsnakes PPA: Ubuntu 22.04's own python3.11 is a
# 3.11.0 release candidate, which lacks tarfile's extraction `filter=` (3.11.4+)
# used by modal_app.py.
RUN apt-get update && apt-get install -y --no-install-recommends \
        software-properties-common gpg-agent \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
        python3.11 python3.11-venv python3.11-dev \
        git curl ca-certificates libgl1 libgomp1 \
        colmap \
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

# Python GPU stack (pins validated during the spike):
#   torch (CUDA 12.4) — BSD-style; gsplat / nerfstudio (Splatfacto) — Apache-2.0;
#   open3d — MIT.
# torchvision is pinned from the same cu124 index so nerfstudio's torchvision
# requirement cannot pull a newer PyPI torch over the CUDA build.
RUN python -m pip install --upgrade pip==24.2 setuptools wheel ninja \
    && python -m pip install torch==2.4.1 torchvision==0.19.1 \
        --index-url https://download.pytorch.org/whl/cu124

# gsplat 1.4.0 ships only a pure-Python PyPI wheel (CUDA kernels are JIT-compiled
# on first use, i.e. on billed GPU time) and its sdist lacks the glm submodule;
# prebuilt wheels exist only for cp310. So compile the CUDA extension here, from
# the tagged source, for A100 (8.0), A10G (8.6) and L4/L40S (8.9). No GPU is
# needed to compile.
ENV TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9" \
    MAX_JOBS=4
RUN git clone --depth 1 --branch v1.4.0 --recurse-submodules --shallow-submodules \
        https://github.com/nerfstudio-project/gsplat.git /tmp/gsplat \
    && python -m pip install --no-build-isolation /tmp/gsplat \
    && rm -rf /tmp/gsplat

# numpy<2: open3d 0.18 is built against the numpy 1.x ABI.
RUN python -m pip install \
        gsplat==1.4.0 \
        nerfstudio==1.1.5 \
        open3d==0.18.0 \
        numpy==1.26.4 \
        torch==2.4.1 \
        torchvision==0.19.1 \
    && ns-train --help > /dev/null \
    && python -c "import open3d, gsplat, torch; print('torch', torch.__version__, 'gsplat', gsplat.__version__, 'open3d', open3d.__version__)"

WORKDIR /work
COPY reconstruction ./reconstruction

# Default: show the license manifest gate. The spike driver invokes
# reconstruction.pipeline.run_pipeline with the real adapters.
CMD ["python", "-c", "from reconstruction import assert_commercial_safe; print('license gate OK:', len(assert_commercial_safe()), 'components')"]
