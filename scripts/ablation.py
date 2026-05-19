from testforge.orchestrator import run_cycle

TARGETS: dict[str, str] = {
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
    "days_in_month": """\
def days_in_month(year: int, month: int) -> int:
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if month in (4, 6, 9, 11):
        return 30
    if year % 400 == 0:
        return 29
    if year % 100 == 0:
        return 28
    if year % 4 == 0:
        return 29
    return 28
""",
    "max_subarray": """\
def max_subarray(nums: list[int]) -> int:
    if not nums:
        return 0
    current = best = nums[0]
    for n in nums[1:]:
        current = max(n, current + n)
        best = max(best, current)
    return best
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
    "no_judge": {
        "author_model": "openai/gpt-oss-120b:free",
        "judge_model": "openai/gpt-oss-120b:free",
        "use_judge": False,
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
