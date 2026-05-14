from testforge.orchestrator import run_cycle

TARGETS: dict[str, str] = {
    "clamp": """\
def clamp(value: float, lo: float, hi: float) -> float:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value
""",
    "is_palindrome": """\
def is_palindrome(s: str) -> bool:
    s = s.lower().replace(" ", "")
    return s == s[::-1]
""",
    "fizzbuzz": """\
def fizzbuzz(n: int) -> str:
    if n % 15 == 0:
        return "FizzBuzz"
    if n % 3 == 0:
        return "Fizz"
    if n % 5 == 0:
        return "Buzz"
    return str(n)
""",
    "binary_search": """\
def binary_search(arr: list[int], target: int) -> int:
    low = 0
    high = len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
""",
    "running_max": """\
def running_max(nums: list[int]) -> list[int]:
    if not nums:
        return []
    result = [nums[0]]
    for n in nums[1:]:
        result.append(max(result[-1], n))
    return result
""",
    "caesar_cipher": """\
def caesar_cipher(text: str, shift: int) -> str:
    result = []
    for ch in text:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            result.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            result.append(ch)
    return ''.join(result)
""",
    "merge_intervals": """\
def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    if not intervals:
        return []
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
""",
    "luhn_check": """\
def luhn_check(card_number: str) -> bool:
    digits = [int(d) for d in card_number if d.isdigit()]
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    return sum(digits) % 10 == 0
""",
    "run_length_encode": """\
def run_length_encode(s: str) -> str:
    if not s:
        return ''
    result = []
    count = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            count += 1
        else:
            result.append(f'{count}{s[i-1]}')
            count = 1
    result.append(f'{count}{s[-1]}')
    return ''.join(result)
""",
    "count_change": """\
def count_change(amount: int, coins: list[int]) -> int:
    dp = [0] * (amount + 1)
    dp[0] = 1
    for coin in coins:
        for i in range(coin, amount + 1):
            dp[i] += dp[i - coin]
    return dp[amount]
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
