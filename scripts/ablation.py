from testforge.orchestrator import run_cycle

TARGETS: dict[str, str] = {
    "parse_semver": """\
def parse_semver(s: str) -> tuple[int, int, int]:
    if not isinstance(s, str):
        raise TypeError("semver must be a string")
    parts = s.lstrip("v").split(".")
    if len(parts) != 3:
        raise ValueError("semver must have 3 components")
    major, minor, patch = parts
    if not (major.isdigit() and minor.isdigit() and patch.isdigit()):
        raise ValueError("semver components must be non-negative integers")
    return int(major), int(minor), int(patch)
""",
    "balanced_parens": """\
def balanced_parens(s: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in ")]}":
            if not stack or stack[-1] != pairs[ch]:
                return False
            stack.pop()
    return not stack
""",
    "round_half_even": """\
def round_half_even(x: float, ndigits: int = 0) -> float:
    import math
    if math.isnan(x) or math.isinf(x):
        raise ValueError("cannot round non-finite values")
    mult = 10 ** ndigits
    scaled = x * mult
    floor = math.floor(scaled)
    diff = scaled - floor
    if diff < 0.5:
        rounded = floor
    elif diff > 0.5:
        rounded = floor + 1
    else:
        rounded = floor if floor % 2 == 0 else floor + 1
    return rounded / mult
""",
}

CONFIGS: dict[str, dict[str, str]] = {
    "homogeneous": {
        "author_model": "openai/gpt-oss-120b:free",
        "judge_model": "openai/gpt-oss-120b:free",
    },
    "heterogeneous": {
        "author_model": "openai/gpt-oss-120b:free",
        "judge_model": "poolside/laguna-m.1:free",
    },
}

COL = "{:<20} {:<15} {:<12} {:<18} {:<10} {:<15} {}"

if __name__ == "__main__":
    print(
        COL.format("function", "config", "kill_rate", "mutations", "tokens", "stopped", "retries")
    )
    print("-" * 90)

    for fn_name, fn_code in TARGETS.items():
        for config_name, models in CONFIGS.items():
            result = run_cycle(
                fn_code,
                target_name=f"{fn_name}_{config_name}",
                **models,  # type: ignore[arg-type]
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
