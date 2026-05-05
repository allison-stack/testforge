import argparse

from .orchestrator import run_cycle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("target_code_file_path", help="Path to target code file")
    parser.add_argument(
        "target_name", help="The name of the function to be tested in the target code file"
    )
    parser.add_argument(
        "--author_model",
        default="gpt-oss-120b:free",
        help="Name of LLM model to be used for Author agent",
    )
    parser.add_argument(
        "--judge_model",
        default="z-ai/glm-4.5-air:free",
        help="Name of LLM model to be used for Judge model",
    )
    args = parser.parse_args()

    # open file and get contents
    with open(args.target_code_file_path, encoding="utf-8") as f:
        target_code = f.read()

    # run the target code through the pipeline
    result = run_cycle(
        target_code, args.target_name, author_model=args.author_model, judge_model=args.judge_model
    )

    # output metrics
    print(f"kill_rate:  {result.kill_rate:.0%}")
    print(f"mutations:  {result.mutations_killed}/{result.mutations_total} killed")
    print(f"tokens:     {result.tokens_used}")
    print(f"stopped:    {result.stopped_reason}")
    print(f"critique:   {result.judge_critique}")
