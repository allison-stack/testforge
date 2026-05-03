from testforge.author import author
from testforge.executor import run_test

fn = """def count_vowels(text):
    vowels = "aeiouAEIOU"
    count = 0
    for char in text:
        if char in vowels:
            count += 1
    return count
"""

test_code, tokens = author(fn)

print("==========GENERATED TEST:==========")
print(test_code)

result = run_test(fn, test_code)

print(f"\n==========PASSED: {result.passed}==========")
print(result.stdout or result.stderr)
