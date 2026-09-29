"""Runpod benchmark tools (M1-RES-01 validation): shell snippets parse, the COLMAP
thread shim appends num_threads only where supported, cgroup quotas (v1 + v2) are
read, and the launcher only ever asks for Secure Cloud."""

from __future__ import annotations

import shutil
import subprocess

import pytest
from tools import runpod_bench as rb
from tools import runpod_job as rj

bash = shutil.which("bash")
pytestmark = pytest.mark.skipif(bash is None, reason="needs bash")


def test_start_and_idle_commands_parse():
    job = "true > /root/job.log 2>&1; rc=$?; " + rb.IDLE_SHUTDOWN + " exit $rc"
    for cmd in (rb.START_CMD, job):
        assert subprocess.run([bash, "-n", "-c", cmd]).returncode == 0
    assert "GJ_MAX_RUNTIME_S" in rb.START_CMD
    assert "remove pod" in rb.SELF_TERMINATE and "DELETE" in rb.SELF_TERMINATE


def test_colmap_shim_adds_num_threads(tmp_path):
    fake = tmp_path / "colmap"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        'if [ "$2" = "-h" ]; then echo "  --Mapper.num_threads arg (=-1)"; '
        'echo "  --SiftExtraction.max_num_features arg"; exit 0; fi\n'
        'echo "ARGS: $*"\n'
    )
    fake.chmod(0o755)
    shim = tmp_path / "shim"
    shim.write_text(rj.COLMAP_SHIM.format(real=fake, n=7))
    out = subprocess.run([bash, str(shim), "mapper", "--x", "1"], capture_output=True, text=True)
    assert out.stdout.strip() == "ARGS: mapper --x 1 --Mapper.num_threads 7"


def test_cgroup_quota_v2_and_v1(tmp_path):
    v2 = tmp_path / "v2"
    v2.mkdir()
    (v2 / "cpu.max").write_text("1730000 100000\n")
    assert rj.cgroup_cpus(v2) == pytest.approx(17.3)
    v1 = tmp_path / "v1"
    (v1 / "cpu").mkdir(parents=True)
    (v1 / "cpu" / "cpu.cfs_quota_us").write_text("1785000\n")
    (v1 / "cpu" / "cpu.cfs_period_us").write_text("100000\n")
    assert rj.cgroup_cpus(v1) == pytest.approx(17.85)
    unlimited = tmp_path / "none"
    unlimited.mkdir()
    (unlimited / "cpu.max").write_text("max 100000\n")
    assert rj.cgroup_cpus(unlimited) >= 1


def test_launcher_is_secure_cloud_us_only():
    src = (rb.HERE / "runpod_bench.py").read_text(encoding="utf-8")
    assert '"cloudType": "SECURE"' in src and "COMMUNITY" not in src
    assert all(dc.startswith("US-") for dc in rb.US_DATACENTERS)
