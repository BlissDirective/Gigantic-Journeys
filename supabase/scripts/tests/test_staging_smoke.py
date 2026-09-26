"""staging_smoke: pure evaluators (no network)."""

import staging_smoke as s


def test_auth_settings_spec():
    settings = {
        "external": {"email": True, "anonymous_users": False, "apple": False, "google": True},
        "mailer_autoconfirm": False,
    }
    got = {n: r for n, r, _ in s.auth_settings_checks(settings)}
    assert got == {
        "auth.email": s.PASS,
        "auth.anonymous_off": s.PASS,
        "auth.apple": s.PENDING,
        "auth.google": s.PASS,
    }


def test_autoconfirm_and_anonymous_fail():
    settings = {"external": {"email": True, "anonymous_users": True}, "mailer_autoconfirm": True}
    got = {n: r for n, r, _ in s.auth_settings_checks(settings)}
    assert got["auth.email"] == s.FAIL
    assert got["auth.anonymous_off"] == s.FAIL


def test_rls_gaps_ignores_system_schemas():
    rows = [
        ("public", "environments", True, 2),
        ("public", "open_table", False, 0),
        ("public", "no_policy", True, 0),
        ("auth", "users", False, 0),
        ("storage", "objects", True, 5),
    ]
    assert s.rls_gaps(rows) == ["public.open_table: RLS disabled", "public.no_policy: no policy"]


def test_pending_migrations():
    files = ["20260926120000_a.sql", "20261001000000_b.sql"]
    assert s.pending_migrations(files, {"20260926120000"}) == ["20261001000000_b.sql"]
