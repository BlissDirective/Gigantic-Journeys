"""M4-DATA-02 ranking + anti-gaming tests."""

from datetime import UTC, datetime, timedelta

import ranking
from ranking import Environment, PlayStats, Rating

CFG = ranking.load_config()
NOW = datetime(2026, 9, 30, 12, 0, 0, tzinfo=UTC)


def rating(uid, device, axes=(4, 4, 4, 4), age=365.0, when=None):
    return Rating(
        user_id=uid,
        device_hash=device,
        created_at=when or (NOW - timedelta(days=10)),
        account_age_days=age,
        fun=axes[0],
        interesting=axes[1],
        interactive=axes[2],
        exciting=axes[3],
    )


def env(
    eid="env-1",
    mode="room",
    published=None,
    creator="creator-1",
    ratings=None,
    signals=None,
    play=None,
):
    return Environment(
        environment_id=eid,
        capture_mode=mode,
        published_at=published or (NOW - timedelta(days=2)),
        creator_id=creator,
        ratings=ratings or [],
        signals=signals if signals is not None else {k: 0.6 for k in CFG["signals"]},
        play=play or PlayStats(),
    )


# --- config ---


def test_weight_groups_are_normalised():
    for group in ("composition", "rating_axes", "signals"):
        assert abs(sum(CFG[group].values()) - 1.0) < 1e-9


# --- rating aggregation + shrinkage ---


def test_no_ratings_sits_near_the_prior():
    e = env(ratings=[])
    # prior mean 3.0 on 1..5 -> 0.5 component
    assert abs(ranking.rating_component(e, CFG) - 0.5) < 1e-9


def test_many_genuine_high_ratings_raise_the_component():
    ratings = [rating(f"u{i}", f"dev{i}", axes=(5, 5, 5, 5)) for i in range(30)]
    assert ranking.rating_component(env(ratings=ratings), CFG) > 0.75


def test_one_rating_per_account_latest_wins():
    early = rating("u1", "dev1", axes=(1, 1, 1, 1), when=NOW - timedelta(days=9))
    late = rating("u1", "dev1", axes=(5, 5, 5, 5), when=NOW - timedelta(days=1))
    eff = ranking.effective_ratings(env(ratings=[early, late]), CFG)
    assert len(eff) == 1 and eff[0][0].fun == 5


def test_creator_self_rating_is_dropped():
    r = rating("creator-1", "devc", axes=(5, 5, 5, 5))
    assert ranking.effective_ratings(env(creator="creator-1", ratings=[r]), CFG) == []


def test_per_device_cap_limits_sybil_farm():
    # 20 accounts, all on one device -> at most per_device_cap counted
    ratings = [rating(f"u{i}", "one-device") for i in range(20)]
    eff = ranking.effective_ratings(env(ratings=ratings), CFG)
    assert len(eff) == CFG["anti_gaming"]["per_device_cap"]


# --- AT-3: a deliberate rate-spam attack does not materially move the rank ---


def _spam(n, device_count, star, base_time):
    return [
        rating(
            f"spam{i}",
            f"spamdev{i % device_count}",
            axes=(star, star, star, star),
            age=0.0,
            when=base_time + timedelta(minutes=i),
        )
        for i in range(n)
    ]


def test_rate_spam_does_not_materially_move_score():
    genuine = [rating(f"g{i}", f"gdev{i}", axes=(4, 4, 4, 4)) for i in range(5)]
    baseline = ranking.base_score(env(ratings=genuine), CFG)
    burst = NOW - timedelta(hours=2)
    inflate = ranking.base_score(env(ratings=genuine + _spam(200, 4, 5, burst)), CFG)
    deflate = ranking.base_score(env(ratings=genuine + _spam(200, 4, 1, burst)), CFG)
    # 200 spam ratings from 4 devices move the 0..100 score by only a couple of points
    assert abs(inflate - baseline) < 3.0
    assert abs(deflate - baseline) < 3.0


def test_anti_gaming_actually_bites_vs_naive_mean():
    # without the defences, 200 five-star spam would push a naive mean to ~1.0 component
    genuine = [rating(f"g{i}", f"gdev{i}", axes=(3, 3, 3, 3)) for i in range(5)]
    spam = _spam(200, 4, 5, NOW - timedelta(hours=1))
    comp = ranking.rating_component(env(ratings=genuine + spam), CFG)
    assert comp < 0.65  # nowhere near the 1.0 a naive mean would report


# --- signals ---


def test_compute_signals_from_spec_graph_play():
    spec = {
        "summit": {"height_A": 10.0},
        "bounds": {"min": [-10, 0, -10], "max": [10, 10, 10]},
        "routes": [{"beats": [{"edge_ids": ["edge-1", "edge-2"]}]}],
    }
    graph = {
        "nodes": [{"position": [0, 0, 0]}, {"position": [5, 8, 5]}],
        "edges": [
            {"id": "edge-1", "verb": "mantle"},
            {"id": "edge-2", "verb": "grapple-ascend"},
        ],
    }
    e = Environment(
        "env-1",
        "room",
        NOW,
        "c",
        signals=None,
        spec=spec,
        graph=graph,
        play=PlayStats(plays=100, summits=40, players=70, replays=30),
    )
    s = ranking.compute_signals(e, CFG)
    assert abs(s["verticality"] - 0.5) < 1e-9  # 10 / 20
    assert abs(s["move_variety"] - 2 / 34) < 1e-9
    assert abs(s["completion_rate"] - 0.4) < 1e-9
    assert abs(s["replay_rate"] - 0.3) < 1e-9
    assert 0.0 <= s["reachable_volume"] <= 1.0


# --- AT-2: the three sort tabs ---


def test_top_week_decays_so_fresher_ranks_higher_at_equal_base():
    fresh = env(eid="fresh", published=NOW - timedelta(days=1))
    stale = env(eid="stale", published=NOW - timedelta(days=10))
    order = [e.environment_id for e in ranking.feed_top_week([stale, fresh], CFG, NOW)]
    assert order == ["fresh", "stale"]


def test_top_week_rewards_better_received_at_equal_age():
    loved = env(
        eid="loved", ratings=[rating(f"u{i}", f"d{i}", axes=(5, 5, 5, 5)) for i in range(20)]
    )
    meh = env(eid="meh", ratings=[rating(f"v{i}", f"e{i}", axes=(2, 2, 2, 2)) for i in range(20)])
    order = [e.environment_id for e in ranking.feed_top_week([meh, loved], CFG, NOW)]
    assert order == ["loved", "meh"]


def test_new_is_recency():
    a = env(eid="a", published=NOW - timedelta(days=5))
    b = env(eid="b", published=NOW - timedelta(days=1))
    c = env(eid="c", published=NOW - timedelta(days=3))
    assert [e.environment_id for e in ranking.feed_new([a, b, c])] == ["b", "c", "a"]


def test_near_your_scale_filters_room_vs_tabletop():
    r1 = env(eid="r1", mode="room")
    t1 = env(eid="t1", mode="tabletop")
    r2 = env(eid="r2", mode="room")
    rooms = ranking.feed_near_scale([r1, t1, r2], "room", CFG, NOW)
    assert {e.environment_id for e in rooms} == {"r1", "r2"}
    tabletops = ranking.feed_near_scale([r1, t1, r2], "tabletop", CFG, NOW)
    assert {e.environment_id for e in tabletops} == {"t1"}


def test_deterministic():
    envs = [env(eid=f"e{i}", ratings=[rating(f"u{i}", f"d{i}")]) for i in range(5)]
    a = [e.environment_id for e in ranking.feed_top_week(envs, CFG, NOW)]
    b = [e.environment_id for e in ranking.feed_top_week(envs, CFG, NOW)]
    assert a == b
