# TestForge

A multi-agent test-quality system for open-model pipelines. The Author writes pytest tests, the Adversary mutates the target to generate "plausible bugs", the Executor runs everything in a Docker sandbox, and a Judge from a different model family critiques tests that fail to catch mutations. The orchestrator loops Author → Executor → Adversary → Executor → Judge until the test kills every mutation or the Supervisor pulls the budget cord.

> **Status:** v0.1 working end-to-end. All agents are implemented, the orchestrator loop runs, and the heterogeneity ablation produces a markdown report.

---

## Repo tour — what every file is for

### Project metadata

| File | What it's for |
|---|---|
| `pyproject.toml` | Python project definition: deps, dev tools (ruff, mypy, pytest), and the `testforge` console script entry point. |
| `uv.lock` | Pinned dependency versions. Don't edit by hand — `uv add <pkg>` updates it. |
| `.python-version` | Tells `uv` / `pyenv` which Python to use (3.12). |
| `.env.example` | Template for `.env`. Copy to `.env` and fill in `OPENROUTER_API_KEY`. |
| `.gitignore` | Standard Python ignores plus `.env`, `.venv`, caches. |
| `.pre-commit-config.yaml` | Runs ruff + mypy before every commit. |

### Sandbox infrastructure

| File | What it's for |
|---|---|
| `Dockerfile` | Pre-built container image with pytest installed. The Executor runs untrusted LLM-generated test code inside this. Build once with `docker build -t testforge-sandbox .`. |

### Source code: `src/testforge/`

Every file has a docstring at the top explaining its role.

| File | What it does |
|---|---|
| `__init__.py` | Package marker. Holds `__version__`. |
| `llm.py` | **Model router.** The single place LLM calls happen. Wraps the OpenAI SDK pointed at OpenRouter. Swap models with one string. |
| `executor.py` | **Executor (NOT an LLM).** Runs `pytest` inside `testforge-sandbox` against a target + test pair, returns pass/fail + stdout/stderr. Deterministic ground truth. |
| `author.py` | **Author agent.** LLM call that writes a pytest function for the target, optionally given a Judge critique to incorporate. |
| `adversary.py` | **Adversary agent.** `generate_mutations` wraps `mutmut` for mechanical mutations; `generate_llm_mutations` calls an LLM for "semantic" mutations. |
| `judge.py` | **Judge agent.** LLM call (different model family) that critiques the Author's test against surviving mutations. |
| `supervisor.py` | **Supervisor.** Pure-Python budget tracker (tokens, retries, wall-clock). Tells the orchestrator when to stop. |
| `orchestrator.py` | **Glue.** `run_cycle` runs Author → Executor → Adversary → Executor → Judge in a retry loop, writes a JSONL trace per iteration, and returns a `CycleResult`. |
| `cli.py` | `testforge` console entry point: `testforge <target_file> <function_name> [--author_model ...] [--judge_model ...]`. |
| `prompts/author.txt` | System prompt for Author. |
| `prompts/judge.txt` | System prompt for Judge. |
| `prompts/adversary.txt` | System prompt for the LLM Adversary. |

### Scripts, targets, tests, traces, results

| Path | What it's for |
|---|---|
| `targets/sample.py` | Small Python functions used as the training-wheels target set. |
| `scripts/llm_test.py` | **Day-1 hello-world.** Makes one LLM call and prints the response. Run this first to verify your env is set up. |
| `scripts/llm_api_test.py` | Minimal direct-API smoke test. |
| `scripts/executor_author_test.py` | End-to-end smoke: Author writes a test, Executor runs it. |
| `scripts/ablation.py` | Sweeps a bank of target functions against homogeneous vs. heterogeneous (Author + Judge) model pairings, prints a per-cycle summary table, and writes per-target JSONL traces. |
| `scripts/build_report.py` | Aggregates `traces/*.jsonl` (one file per `<target>_<config>`) into `results/report.md` — per-target kill rates, deltas, token totals, and method notes. |
| `tests/test_executor.py` | Unit tests for TestForge itself. Run with `uv run pytest tests/`. |
| `traces/` | Append-only JSONL logs, one file per cycle (`<target>_<config>.jsonl`). The audit trail. |
| `results/` | Aggregated outputs from `build_report.py` (`report.md`, ablation stdout/stderr). |

---

## How the pieces fit together

```
                                       targets/sample.py  (input)
                                              │
                                              ▼
   prompts/author.txt ──▶ author.py  ◀──┐
                              │         │ uses
                              ▼         │
                          llm.py ───────┘ (model router)
                              │
                              ▼
                         executor.py ─────▶ Dockerfile (sandbox)
                              │
                              ▼
                        adversary.py (mutmut + optional LLM)
                              │
                              ▼
                          executor.py  (run test against each mutation)
                              │
                              ▼
   prompts/judge.txt ──▶ judge.py
                              │
                              ▼
                       orchestrator.py ─────▶ traces/ (JSONL audit log)
                              ▲                       │
                              │                       ▼
                       supervisor.py            results/ (report.md)
                       (budget guards)
```

---

## Setup

### 1. Install Docker
You need Docker Desktop running for the Executor. Verify:

```bash
docker run --rm hello-world
```

### 2. Install Python deps
```bash
cd testforge
uv sync                                    # installs everything in pyproject.toml
```

All runtime deps (including `mutmut`, `rich`, `structlog`, `tenacity`) are already pinned in `pyproject.toml`.

### 3. Configure your API key
```bash
cp .env.example .env
# Open .env and paste your OpenRouter API key.
```

> Set a **$20 spending cap** in the OpenRouter dashboard. A loop bug can spend $50 in 5 minutes.

### 4. Build the sandbox image
```bash
docker build -t testforge-sandbox .
```

### 5. Smoke-test your environment
```bash
uv run python scripts/llm_test.py
```

---

## Running TestForge

### One target via the CLI

```bash
uv run testforge targets/sample.py <function_name> \
  --author_model openai/gpt-oss-120b:free \
  --judge_model  z-ai/glm-4.5-air:free
```

Prints kill rate, mutations killed/total, tokens used, stop reason, and the final Judge critique. A per-cycle JSONL trace is written to `traces/<function_name>.jsonl`.

### Heterogeneity ablation

```bash
uv run python scripts/ablation.py | tee results/ablation_stdout.txt
uv run python scripts/build_report.py
```

`ablation.py` runs each target under both `homogeneous` and `heterogeneous` Author/Judge pairings. `build_report.py` aggregates the per-target traces into `results/report.md`.

---

## Common commands

```bash
# Run the smoke test
uv run python scripts/llm_test.py

# Run a single target through the pipeline
uv run testforge targets/sample.py clamp

# Sweep the ablation and rebuild the report
uv run python scripts/ablation.py
uv run python scripts/build_report.py

# Unit tests for TestForge itself
uv run pytest tests/

# Format + lint
uv run ruff format .
uv run ruff check . --fix

# Type-check
uv run mypy src/

# Rebuild the sandbox image (after editing Dockerfile)
docker build -t testforge-sandbox .
```

---

## What this is NOT (in v0.1)

- Not fine-tuned. Pure prompt + off-the-shelf models via OpenRouter.
- No web UI. CLI only.
- No vector DB / Scout agent — context is the raw target code.
- No LLM-based Supervisor — pure-Python budget heuristics only.
- Not air-gapped. Hosted APIs (OpenRouter). Air-gapping is a v0.2 roadmap claim.

The LLM-based Adversary (`generate_llm_mutations`) is implemented but the orchestrator currently uses the deterministic `mutmut` path; wiring the LLM mutations into the loop is a v0.2 task.
