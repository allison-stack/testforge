import argparse
from typing import Any

from testforge.models import AUTHOR_MODEL, JUDGE_MODEL
from testforge.orchestrator import run_cycle

TARGETS: dict[str, str] = {
    "parse_ipv4": """\
def parse_ipv4(s: str) -> tuple:
    parts = s.split(".")
    if len(parts) != 4:
        raise ValueError("must have 4 octets")
    out = []
    for p in parts:
        if not p or not p.isdigit():
            raise ValueError("octet must be digits")
        if len(p) > 1 and p[0] == "0":
            raise ValueError("leading zero not allowed")
        n = int(p)
        if n > 255:
            raise ValueError("octet out of range")
        out.append(n)
    return tuple(out)
""",
    "roman_to_int": """\
def roman_to_int(s: str) -> int:
    if not s:
        raise ValueError("empty")
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    prev = 0
    for ch in reversed(s):
        if ch not in vals:
            raise ValueError("invalid numeral")
        v = vals[ch]
        if v < prev:
            total -= v
        else:
            total += v
        prev = v
    return total
""",
    "wildcard_match": """\
def wildcard_match(pattern: str, s: str) -> bool:
    m, n = len(pattern), len(s)
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = True
    for i in range(1, m + 1):
        if pattern[i - 1] == "*":
            dp[i][0] = dp[i - 1][0]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if pattern[i - 1] == "*":
                dp[i][j] = dp[i - 1][j] or dp[i][j - 1]
            elif pattern[i - 1] == "?" or pattern[i - 1] == s[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
    return dp[m][n]
""",
    "balanced_brackets": """\
def balanced_brackets(s: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}
    opens = set("([{")
    stack = []
    for ch in s:
        if ch in opens:
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack[-1] != pairs[ch]:
                return False
            stack.pop()
    return not stack
""",
    "parse_duration": """\
def parse_duration(s: str) -> int:
    if not s:
        raise ValueError("empty")
    units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    total = 0
    num = ""
    for ch in s:
        if ch.isdigit():
            num += ch
        elif ch in units:
            if not num:
                raise ValueError("missing number")
            total += int(num) * units[ch]
            num = ""
        else:
            raise ValueError("bad character")
    if num:
        raise ValueError("trailing number without unit")
    return total
""",
    "run_length_decode": """\
def run_length_decode(s: str) -> str:
    out = []
    count = ""
    for ch in s:
        if ch.isdigit():
            count += ch
        else:
            n = int(count) if count else 1
            if n == 0:
                raise ValueError("zero count")
            out.append(ch * n)
            count = ""
    if count:
        raise ValueError("trailing count without char")
    return "".join(out)
""",
    "is_valid_isbn10": """\
def is_valid_isbn10(s: str) -> bool:
    s = s.replace("-", "").replace(" ", "")
    if len(s) != 10:
        return False
    total = 0
    for i, ch in enumerate(s):
        if ch == "X" and i == 9:
            v = 10
        elif ch.isdigit():
            v = int(ch)
        else:
            return False
        total += v * (10 - i)
    return total % 11 == 0
""",
}

CONFIGS: dict[str, dict[str, str | bool]] = {
    "baseline": {
        # one author pass, no judge feedback loop - measures raw author quality
        # against the same mutation set as the iterating configs.
        "author_model": AUTHOR_MODEL,
        "judge_model": AUTHOR_MODEL,  # unused when iterate=False
        "use_llm_adversary": True,
        "iterate": False,
    },
    "homogeneous": {
        "author_model": AUTHOR_MODEL,
        "judge_model": AUTHOR_MODEL,
        "use_llm_adversary": True,
    },
    "heterogeneous": {
        "author_model": AUTHOR_MODEL,
        "judge_model": JUDGE_MODEL,
        "use_llm_adversary": True,
    },
}

COL = "{:<20} {:<15} {:<12} {:<18} {:<10} {:<15} {}"


def _make_iter_printer() -> "callable":
    """Return an on_iteration callback that prints one indented line per pass."""

    def _print(trace: dict[str, Any]) -> None:
        # retries in the trace reflects the count BEFORE this iteration's
        # potential judge call, so this iteration's 1-based index is retries+1.
        iter_idx = trace.get("retries", 0) + 1
        phase = trace.get("phase")
        if phase == "initial_test_failed":
            print(f"  iter {iter_idx}: initial test failed (will retry)", flush=True)
        elif phase == "mutation_pass":
            killed = trace["mutations_killed"]
            total = trace["mutations_total"]
            rate = trace["kill_rate"]
            survivors = total - killed
            print(
                f"  iter {iter_idx}: killed {killed}/{total} ({rate:.0%}), {survivors} survivors",
                flush=True,
            )

    return _print


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the testforge ablation sweep.")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show live progress and per-iteration kill-rate breakdown.",
    )
    args = parser.parse_args()

    print(
        COL.format("function", "config", "kill_rate", "mutations", "tokens", "stopped", "retries")
    )
    print("-" * 110)

    total = len(TARGETS) * len(CONFIGS)
    i = 0
    on_iteration = _make_iter_printer() if args.verbose else None
    for fn_name, fn_code in TARGETS.items():
        for config_name, models in CONFIGS.items():
            i += 1
            if args.verbose:
                print(f"[{i}/{total}] running {fn_name}/{config_name}...", flush=True)
            try:
                result = run_cycle(
                    fn_code,
                    target_name=f"{fn_name}_{config_name}",
                    on_iteration=on_iteration,
                    **models,
                )
                print(
                    COL.format(
                        fn_name,
                        config_name,
                        f"{result.kill_rate:.0%}",
                        f"{result.mutations_killed}/{result.mutations_total}",
                        result.tokens_used,
                        result.stopped_reason or "all_killed",
                        result.retries,
                    )
                )
            except Exception as e:
                print(
                    COL.format(
                        fn_name, config_name, "ERR", "-", "-", f"err:{type(e).__name__}", "-"
                    )
                )
                continue


if __name__ == "__main__":
    main()
