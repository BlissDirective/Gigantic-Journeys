"""check_rls: a created table needs RLS + a policy in the same migration."""

import pathlib

import check_rls


def test_good_migration_passes():
    sql = """
    create table public.foo (id uuid primary key);
    alter table public.foo enable row level security;
    create policy foo_owner on public.foo for all using (true);
    """
    assert check_rls.violations(sql) == []


def test_missing_rls_is_flagged():
    sql = """
    create table public.foo (id uuid primary key);
    create policy foo_owner on public.foo for all using (true);
    """
    bad = check_rls.violations(sql)
    assert len(bad) == 1
    assert "enable row level security" in bad[0]


def test_missing_policy_is_flagged():
    sql = """
    create table public.foo (id uuid primary key);
    alter table public.foo enable row level security;
    """
    bad = check_rls.violations(sql)
    assert len(bad) == 1
    assert "create policy" in bad[0]


def test_comments_do_not_false_positive():
    sql = "-- create table public.ghost (documented, not created)\nselect 1;"
    assert check_rls.violations(sql) == []


def test_schema_qualifier_mismatch_still_matches():
    # created as public.foo, RLS/policy reference the bare name
    sql = """
    create table public.foo (id uuid primary key);
    alter table foo enable row level security;
    create policy p on foo for select using (true);
    """
    assert check_rls.violations(sql) == []


def test_real_migrations_pass():
    for path in sorted(check_rls.MIGRATIONS.glob("*.sql")):
        assert check_rls.violations(path.read_text(encoding="utf-8")) == [], path.name


FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"


def test_compliant_fixture_migration_passes(capsys):
    assert check_rls.main([str(FIXTURES / "compliant")]) == 0
    assert "OK" in capsys.readouterr().out


def test_noncompliant_fixture_migration_fails(capsys):
    assert check_rls.main([str(FIXTURES / "noncompliant")]) == 1
    out = capsys.readouterr().out
    assert "fixture_open: missing" in out
    assert "fixture_half: missing create policy" in out
    assert "enable row level security" in out.split("fixture_open: missing", 1)[1].splitlines()[0]
    assert "supabase/scripts/tests/fixtures/noncompliant/" in out


def test_main_default_dir_is_green():
    assert check_rls.main([]) == 0
