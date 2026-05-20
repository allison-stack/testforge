"""Sample target functions for TestForge to generate tests for.

These are intentionally simple, pure functions:
  - No I/O, no side effects, no external dependencies.
  - Easy to mutate (mutmut can flip operators, change return values, etc).
  - Easy for you to eyeball whether a generated test is "good".

Use these as your training wheels for week 1-2. Once the pipeline works
end-to-end on these, swap in real OSS functions (flask, requests utils)
for the week 4 evaluation.
"""


def add(a: int, b: int) -> int:
    return a + b


def is_even(n: int) -> bool:
    return n % 2 == 0


def discount(price: float, percent: float) -> float:
    """Apply a percent discount to a price. percent=10 means 10% off."""
    return price * (1 - percent / 100)


def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number. fibonacci(0)=0, fibonacci(1)=1."""
    if n < 0:
        raise ValueError("n must be non-negative")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def is_palindrome(s: str) -> bool:
    """Case-insensitive palindrome check, ignoring non-alphanumerics."""
    cleaned = "".join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]
