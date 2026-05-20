"""
Central registry for LLM model IDs.

Every agent's default model lives here so swapping models is a 1-file change.
Currently emulating the model lineup available at the workplace deployment.
"""

AUTHOR_MODEL = "anthropic/claude-haiku-4.5"
JUDGE_MODEL = "openai/gpt-4o-mini"
ADVERSARY_MODEL = "google/gemini-2.5-flash"
