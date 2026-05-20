function             config          kill_rate    mutations          tokens     stopped         retries
--------------------------------------------------------------------------------------------------------------
[1/9] running roman_to_int/baseline...
  iter 1: killed 45/47 (96%), 2 survivors
roman_to_int         baseline        96%          45/47              2432       baseline        0
[2/9] running roman_to_int/homogeneous...
  iter 1: killed 45/47 (96%), 2 survivors
  iter 2: killed 47/47 (100%), 0 survivors
roman_to_int         homogeneous     100%         47/47              7396       all_killed      1
[3/9] running roman_to_int/heterogeneous...
  iter 1: killed 47/47 (100%), 0 survivors
roman_to_int         heterogeneous   100%         47/47              2543       all_killed      0
[4/9] running balanced_brackets/baseline...
  iter 1: killed 25/26 (96%), 1 survivors
balanced_brackets    baseline        96%          25/26              2111       baseline        0
[5/9] running balanced_brackets/homogeneous...
  iter 1: killed 25/26 (96%), 1 survivors
  iter 2: initial test failed (will retry)
  iter 3: initial test failed (will retry)
balanced_brackets    homogeneous     96%          25/26                4841       initial_test_failed 2
[6/9] running balanced_brackets/heterogeneous...
  iter 1: killed 24/26 (92%), 2 survivors
  iter 2: killed 24/26 (92%), 2 survivors
  iter 3: killed 26/26 (100%), 0 survivors
balanced_brackets    heterogeneous   100%         26/26              13151      all_killed      2
[7/9] running is_valid_isbn10/baseline...
  iter 1: killed 42/44 (95%), 2 survivors
is_valid_isbn10      baseline        95%          42/44              2540       baseline        0
[8/9] running is_valid_isbn10/homogeneous...
  iter 1: killed 42/44 (95%), 2 survivors
  iter 2: killed 41/44 (93%), 3 survivors
  iter 3: killed 43/44 (98%), 1 survivors
is_valid_isbn10      homogeneous     98%          43/44              13539      max_retries     2
[9/9] running is_valid_isbn10/heterogeneous...
  iter 1: killed 42/44 (95%), 2 survivors
  iter 2: killed 43/44 (98%), 1 survivors
  iter 3: initial test failed (will retry)
is_valid_isbn10      heterogeneous   98%           43/44                11665      initial_test_failed 2
