# TestForge ablation report

Heterogeneous (Author + Judge from different model families) vs homogeneous (same family). Hypothesis: heterogeneous kill rates should be >= homogeneous because the Judge catches blind spots the Author shares with a same-family Judge.

## Per-target kill rates

| target | homo kill | hetero kill | Δ | homo tokens | hetero tokens | homo stopped | hetero stopped |
|---|---|---|---|---|---|---|---|
| binary_search | 100% | 100% | +0% | 592 | 566 | all_killed | all_killed |
| caesar_cipher | 100% | 100% | +0% | 485 | 484 | all_killed | all_killed |
| clamp | 100% | 100% | +0% | 605 | 582 | all_killed | all_killed |
| count_change | 100% | 100% | +0% | 563 | 562 | all_killed | all_killed |
| fizzbuzz | 100% | 100% | +0% | 440 | 442 | all_killed | all_killed |
| is_palindrome | 100% | 100% | +0% | 416 | 910 | all_killed | all_killed |
| luhn_check | 100% | 100% | +0% | 505 | 615 | all_killed | all_killed |
| merge_intervals | 100% | 100% | +0% | 536 | 539 | all_killed | all_killed |
| run_length_encode | 100% | 100% | +0% | 474 | 474 | all_killed | all_killed |
| running_max | 100% | 100% | +0% | 436 | 436 | all_killed | all_killed |

## Summary

- Targets evaluated: **10**
- Mean kill rate, homogeneous: **100.0%**
- Mean kill rate, heterogeneous: **100.0%**
- Total tokens, homogeneous: **5,052**
- Total tokens, heterogeneous: **5,610**

## Interpretation

Both configs hit a **100% kill-rate ceiling** on every target. This is a saturation result, not a null result — the targets in this batch are 5-15 line pure functions where any competent test (3-5 assertions covering boundary cases) catches every mutmut-style mutation. The ablation cannot distinguish homogeneous from heterogeneous when both configs are operating above the difficulty floor.

What the run *does* validate:
- End-to-end pipeline works: Author → Executor (Docker) → Adversary (mutmut) → Executor → Judge → Supervisor → trace log, across two model families, with zero crashes on 20 cycles.
- Token budget is healthy: ~500 tokens/cycle average, well under the 20k Supervisor cap. Heterogeneous spent ~11% more tokens, driven almost entirely by one outlier (`is_palindrome` heterogeneous required 1 retry → 910 vs 416 tokens).
- Mutmut coverage scales with target complexity: 2 mutations for `clamp`, 27 for `luhn_check`. The Executor handled all of them.

What this run does *not* show:
- Whether heterogeneous Judges actually help. Need harder targets where the Author's first test is incomplete and the Judge has something to critique. Candidates: real OSS functions with multiple branches, exception paths, or numerical edge cases (off-by-one, NaN, overflow).
- Whether the Judge improves anything at all vs. just retrying the Author with no feedback. A third "no-judge" config would isolate that.

## Method

- Each target is a small pure-Python function in `scripts/ablation.py::TARGETS`.
- For each (target, config) we run one `orchestrator.run_cycle`. Each cycle: Author writes a pytest, Executor runs it in a Docker sandbox, Adversary (mutmut) generates mutations, Executor reruns the test on each mutation, Judge critiques on survivors, loop until kill rate = 100% or Supervisor stops the loop.
- Author model is held constant across configs. Only the Judge model varies, so any delta is attributable to Judge heterogeneity.
- Traces are append-only JSONL in `traces/<target>_<config>.jsonl`; this report reads the final line of each file.
