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

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System + SfM. COLMAP/GLOMAP are BSD-3-Clause. (GLOMAP is built from a pinned
# tag in the spike if the distro package lags; the apt package unblocks the
# first smoke test.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 python3.11-venv python3-pip \
        git curl ca-certificates \
        colmap \
    && rm -rf /var/lib/apt/lists/*

# Node for splat-transform (MIT): PLY -> .spz/.sog.
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g splat-transform@2.6.0

# Python GPU stack (pins validated during the spike):
#   torch (CUDA 12.4) — BSD-style; gsplat / nerfstudio (Splatfacto) — Apache-2.0;
#   open3d — MIT.
RUN python3.11 -m pip install --upgrade pip==24.2 \
    && python3.11 -m pip install \
        torch==2.4.1 --index-url https://download.pytorch.org/whl/cu124 \
    && python3.11 -m pip install \
        gsplat==1.4.0 \
        nerfstudio==1.1.5 \
        open3d==0.18.0

WORKDIR /work
COPY reconstruction ./reconstruction

# Default: show the license manifest gate. The spike driver invokes
# reconstruction.pipeline.run_pipeline with the real adapters.
CMD ["python3.11", "-c", "from reconstruction import assert_commercial_safe; \
print('license gate OK:', len(assert_commercial_safe()), 'components')"]
