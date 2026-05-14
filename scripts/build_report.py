"""
Aggregate traces/*.jsonl into a markdown report under results/.

Each JSONL file holds one line per orchestrator iteration; the last line is
the final state of the cycle. We split target names on the config suffix
(`_homogeneous` / `_heterogeneous`) to pivot back into a per-target table.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACES = ROOT / "traces"
OUT = ROOT / "results" / "report.md"

CONFIGS = ("homogeneous", "heterogeneous")


def last_line(path: Path) -> dict:
    with path.open() as f:
        last = None
        for line in f:
            line = line.strip()
            if line:
                last = line
    return json.loads(last) if last else {}


def main() -> None:
    rows: dict[str, dict[str, dict]] = {}
    for path in sorted(TRACES.glob("*.jsonl")):
        stem = path.stem
        config = next((c for c in CONFIGS if stem.endswith(f"_{c}")), None)
        if not config:
            continue
        target = stem[: -(len(config) + 1)]
        rows.setdefault(target, {})[config] = last_line(path)

    lines = [
        "# TestForge ablation report",
        "",
        "Heterogeneous (Author + Judge from different model families) vs "
        "homogeneous (same family). Hypothesis: heterogeneous kill rates "
        "should be >= homogeneous because the Judge catches blind spots "
        "the Author shares with a same-family Judge.",
        "",
        "## Per-target kill rates",
        "",
        "| target | homo kill | hetero kill | Δ | homo tokens | hetero tokens"
        " | homo stopped | hetero stopped |",
        "|---|---|---|---|---|---|---|---|",
    ]

    homo_kills: list[float] = []
    hetero_kills: list[float] = []
    homo_tokens = 0
    hetero_tokens = 0

    for target in sorted(rows):
        h = rows[target].get("homogeneous", {})
        x = rows[target].get("heterogeneous", {})
        hk = h.get("kill_rate")
        xk = x.get("kill_rate")
        delta = (xk - hk) if (hk is not None and xk is not None) else None
        if hk is not None:
            homo_kills.append(hk)
            homo_tokens += h.get("tokens_used", 0)
        if xk is not None:
            hetero_kills.append(xk)
            hetero_tokens += x.get("tokens_used", 0)
        lines.append(
            "| {t} | {hk} | {xk} | {d} | {ht} | {xt} | {hs} | {xs} |".format(
                t=target,
                hk=f"{hk:.0%}" if hk is not None else "—",
                xk=f"{xk:.0%}" if xk is not None else "—",
                d=f"{delta:+.0%}" if delta is not None else "—",
                ht=h.get("tokens_used", "—"),
                xt=x.get("tokens_used", "—"),
                hs=h.get("stopped_reason") or ("all_killed" if hk == 1.0 else "—"),
                xs=x.get("stopped_reason") or ("all_killed" if xk == 1.0 else "—"),
            )
        )

    def avg(xs: list[float]) -> str:
        return f"{sum(xs) / len(xs):.1%}" if xs else "—"

    lines += [
        "",
        "## Summary",
        "",
        f"- Targets evaluated: **{len(rows)}**",
        f"- Mean kill rate, homogeneous: **{avg(homo_kills)}**",
        f"- Mean kill rate, heterogeneous: **{avg(hetero_kills)}**",
        f"- Total tokens, homogeneous: **{homo_tokens:,}**",
        f"- Total tokens, heterogeneous: **{hetero_tokens:,}**",
        "",
        "## Method",
        "",
        "- Each target is a small pure-Python function in `scripts/ablation.py::TARGETS`.",
        "- For each (target, config) we run one `orchestrator.run_cycle`."
        " Each cycle: Author writes a pytest, Executor runs it in a Docker"
        " sandbox, Adversary (mutmut) generates mutations, Executor reruns"
        " the test on each mutation, Judge critiques on survivors, loop until"
        " kill rate = 100% or Supervisor stops the loop.",
        "- Author model is held constant across configs. Only the Judge model"
        " varies, so any delta is attributable to Judge heterogeneity.",
        "- Traces are append-only JSONL in `traces/<target>_<config>.jsonl`;"
        " this report reads the final line of each file.",
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
