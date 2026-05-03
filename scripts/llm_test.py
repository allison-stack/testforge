"""Day-1 hello-world script.

uv run python scripts/llm_test.py
"""

from testforge.llm import call_llm

if __name__ == "__main__":
    text, tokens = call_llm(
        model="openai/gpt-oss-120b:free",
        system="You are a Python test writer. Reply with code only.",
        user="Write a single pytest test for: def add(a, b): return a + b",
    )
print(f"--- output ({tokens} tokens) ---")
print(text)
