"""The commercial-license gate (ADR-0005; INRIA/SuGaR excluded)."""

import pytest
from reconstruction import Component, LicenseError, assert_commercial_safe
from reconstruction.licenses import MANIFEST


def test_default_manifest_is_commercial_safe():
    assert assert_commercial_safe() is MANIFEST
    assert len(MANIFEST) >= 6


def test_every_default_component_is_allowed_license():
    allowed = {"MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0"}
    assert all(c.license in allowed for c in MANIFEST)


def test_excluded_component_is_rejected():
    bad = (*MANIFEST, Component("SuGaR", "Apache-2.0", "mesh extraction"))
    with pytest.raises(LicenseError, match="non-commercial"):
        assert_commercial_safe(bad)


def test_noncommercial_license_is_rejected():
    bad = (Component("SomeTool", "CC-BY-NC-4.0", "trainer"),)
    with pytest.raises(LicenseError, match="non-allowed license"):
        assert_commercial_safe(bad)
