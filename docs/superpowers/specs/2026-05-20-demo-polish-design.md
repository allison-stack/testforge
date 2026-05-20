# Demo Polish for 5-min Video Demo

**Status:** Approved design — implementation plan TBD
**Date:** 2026-05-20

## Context

TestForge has a working end-to-end multi-agent pipeline (Author → Executor → Adversary → Executor → Judge) plus a heterogeneity ablation that produces `results/report.md`. We need to package it for a 5-minute video demo with two parts:

- **Part 1 (slides):** why we built it.
- **Part 2 (live terminal walkthrough):** what it does, watched in real time.

The video is recorded, not delivered live, but it must read on screen as a single unbroken live terminal session — no mid-step cuts, no obvious post-edit speedups. Re-recording is the failure recovery; no replay/canned-stdout mode is needed.

The current `testforge` CLI prints only a final summary. The orchestrator writes JSONL traces but produces no human-readable intermediate output during a cycle. A demo viewer cannot see the agent loop happening.

## Goals

1. Make the agent loop **visible** during execution: each phase labeled, timed, and resolved with a visible result.
2. Make the **headline result** — heterogeneous Judge beats homogeneous — land in the same terminal session, without flipping to slides.
3. Keep total Part 2 runtime under ~3 minutes so the demo fits the 5-min budget with slide time to spare.

## Non-goals

- Replay / canned-stdout fallback mode.
- Slide content for Part 1.
- Side-by-side parallel rendering of two cycles.
- Web UI or dashboard.
- Video recording / editing tooling.
- Changing model defaults outside the demo script.

## Design

### Deliverables

1. A new entry point that runs **one chosen target twice** — homogeneous then heterogeneous — sequentially in a single column, completing in <~90s wall-clock total.
2. **Rich-styled step-by-step output** so the viewer watches Author → Executor → Adversary → Executor → Judge unfold, with live elapsed time per step.
3. A **final comparison table** showing hom vs het kill rates side-by-side, printed once at the end.

### Target selection

Default target: `roman_to_int`. Reasoning:

- Well-known problem; the audience parses what it does in under five seconds.
- Short function body, fits on screen.
- Existing traces show a non-trivial hom-vs-het delta on this target.
- Moderate mutation count keeps the per-cycle executor loop short.

Overridable via `--target <function_name>`. The target file is fixed to `targets/sample.py` (same as the rest of TestForge).

### File layout

- **`scripts/demo.py`** (new) — owns the demo flow, the `rich` rendering, and the final summary table. Entry point: `uv run python scripts/demo.py [--target NAME]`.
- **`src/testforge/orchestrator.py`** — extend the existing `on_iteration` callback into a small **phase-event hook**:
  - New parameter `on_event: Callable[[str, dict], None] | None = None`.
  - Fired at agent-step boundaries: `author_start`, `author_done`, `executor_original_start`, `executor_original_done`, `adversary_start`, `adversary_done`, `mutation_run_start`, `mutation_run_done`, `judge_start`, `judge_done`.
  - `on_iteration` stays as a backward-compatible alias fired after `mutation_pass`.
  - Pure additions at existing seams — no control-flow change.
- **`tests/test_orchestrator_events.py`** (new) — assert the orchestrator fires the expected `on_event` phases in the expected order across one cycle.
- No edits to `author.py`, `executor.py`, `adversary.py`, `judge.py`, or the CLI. Orchestrator owns all eventing.

### Output shape, per cycle

Rendered with `rich.live.Live` + a vertical list of spinner lines that resolve to checkmarks when the phase completes. Each in-flight line shows live elapsed time. Numbers below are illustrative, not targets.

```
TestForge demo — roman_to_int · config: homogeneous (Author+Judge: gpt-oss-120b)

  ⏵ Author drafting test…                          (3.2s) ✓
  ⏵ Executor running test on original…             (0.4s) ✓ pass
  ⏵ Adversary generating mutations…                (5.1s) ✓ 18 mutants (13 mutmut + 5 LLM)
  ⏵ Executor running test vs. 18 mutants…          (2.1s) ✓ 15/18 killed
  ⏵ Judge critiquing surviving 3…                  (4.4s) ✓
  ⏵ Author iterating (round 2)…                    (3.8s) ✓
  ⏵ Executor running test vs. 18 mutants…          (2.0s) ✓ 18/18 killed ✦

  result: 100% kill · 2 iterations · 41s · 6,210 tokens
```

### Final summary table

Printed once, after both cycles complete:

```
┌──────────────┬──────────┬────────┬─────────┬──────┐
│ config       │ kill rate│ killed │ tokens  │ time │
├──────────────┼──────────┼────────┼─────────┼──────┤
│ homogeneous  │ 88%      │ 16/18  │ 4,210   │ 38s  │
│ heterogeneous│ 100% ✦   │ 18/18  │ 6,210   │ 41s  │
└──────────────┴──────────┴────────┴─────────┴──────┘
heterogeneous Judge caught 2 mutations homogeneous missed.
```

Rendered with `rich.table.Table`. The footer line is computed from the two `CycleResult`s.

## Risks and mitigations

- **A cycle takes too long.** A slow LLM call could push Part 2 past the budget.
  *Mitigation:* `demo.py` pins a fast Author model (free-tier Haiku-class) in its defaults rather than the project-wide defaults. Dry-run the demo before recording day and pick a (target, models) combo that consistently lands under ~45s per cycle.

- **Both cycles all-kill in round 1 — Judge gets undersold.** If both runs finish in one Author pass, the viewer never sees the Judge feedback loop.
  *Mitigation:* Pick a target where homogeneous typically takes 2+ iterations (existing trace files flag candidates). If `roman_to_int` doesn't, fall back to `wildcard_match` or `parse_ipv4` based on observed trace history.

- **`rich.live.Live` flickers in some terminals.** Particularly bad on terminals that don't support cursor-up escapes well.
  *Mitigation:* Test in the actual recording terminal ahead of time and choose one with full ANSI support (iTerm2, modern Terminal.app, Alacritty all known good).

- **Pacing dead air.** Even with fast models, a single 8-second LLM call mid-step makes for dull video.
  *Mitigation:* The spinner with live elapsed time keeps the screen moving; the viewer reads "this is doing work" rather than "this is frozen." Do not paper over with post-edit speedups — that breaks the unedited-session illusion.

## Test plan

- **Unit:** `tests/test_orchestrator_events.py` asserts the orchestrator emits the full phase sequence in order across one cycle, with payload keys present.
- **Manual:** Run `scripts/demo.py` end-to-end twice (cold start + warm start), time both, watch in the actual recording terminal. Confirm:
  - Total wall-clock ≤ ~90s.
  - Each spinner line resolves cleanly to ✓ with no visual artifacts.
  - The final summary table renders correctly and shows a hom-vs-het delta.

## Open questions

None at design time. Model-pinning and target-fallback choices are tuning concerns handled during implementation dry-runs, not design decisions.
