"""check_rls: a created table needs RLS + a policy in the same migration."""

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
