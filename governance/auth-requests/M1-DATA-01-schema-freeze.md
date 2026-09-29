# AUTH request: freeze scene_graph / traversal_graph / environment_spec v1.0.0 (M1-DATA-01)

> **STATUS: PROPOSED, awaiting the Owner.** Filed by gj-operator on 2026-09-29 (overnight worker). No AUTH
> number is assigned, because Bots never write the Decisions table. If the Owner approves, the Coordinator
> logs it as the next free number (#036 today, or #037 if the M0-UNITY-03 movement.json request is logged
> first).

```
AUTH REQUEST (next free #)
Type: design-change (protected path: data/schemas/)
What: Freeze the three M1 data contracts at v1.0.0, as drafted in
      design/proposals/m1-data-01-schemas/: scene_graph.json, traversal_graph.json and
      environment_spec.json (JSON Schema 2020-12), with fixtures, a cross-document consistency checker
      and 51 tests. On approval they move unchanged into data/schemas/.
Why:  M1-DATA-01 is P0 and blocks M1-GAME-01 (Unity loads the environment), M1-SCEN-02
      (classification output), M4-PLAT-01 (package) and M4-DATA-02 (ranking). The environments table
      (AUTH #034) already stores environment_spec as jsonb, waiting for this shape.
Cost: $0
Reversible: yes. Later field changes need their own AUTH, following the change rule in data/schemas/README.md.
Waiting on: the Owner (approve, or send back with changes); gj-gameplay + gj-platform review (AT-4)
```

## What the Owner is approving (plain language)

- The data that describes a scanned place for the game, in three files. **Surfaces** say what each part of
  the place is (ledge, rung, studs and so on), what it is made of, and how big it is in avatar heights.
  The **traversal graph** says which spot the avatar can reach from which, with which move, and how hard
  that move is. The **environment spec** holds the summit, 2–3 routes with four beats each, and up to three
  vistas.
- Guarantees built into the format: beat 1 of every route uses only the easiest move set; every move stays
  within 85 % of the avatar's limits; a route that needs a tool must teach the tool in an earlier beat;
  when generation fails, a simple one-route "explore" fallback is recorded rather than failing the
  environment.

## Questions for the Owner or reviewers (defaults are in the draft)

1. Sprint jump and balance walk count as **T1** (not beginner moves). OK?
2. Vistas: **0–3** (a tiny environment may have fewer) or strictly 3?
3. The vault-variant names (`speed-vault`, `kong-vault`, `lazy-vault`) are placeholders until M1-MOVE-02.
