from testforge.orchestrator import run_cycle

# target code
fn = """def binary_search(arr, target):
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
"""
# run the target code through the pipeline
result = run_cycle(fn, target_name="clamp")

# output metrics
print(f"kill_rate:  {result.kill_rate:.0%}")
print(f"mutations:  {result.mutations_killed}/{result.mutations_total} killed")
print(f"tokens:     {result.tokens_used}")
print(f"stopped:    {result.stopped_reason}")
print(f"critique:   {result.judge_critique}")
