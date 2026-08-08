"""
check_algorithms.py — Section 2 PASS/FAIL verification script.

Run with:
    python check_algorithms.py

Prints one PASS/FAIL line per case; exits normally regardless of failures.
Uses only plain if/else — no assert, pytest, or unittest.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.algorithms import (
    insertion_sort,
    binary_search,
    linear_search,
    insertion_sort_count,
    binary_search_count,
    linear_search_count,
)

NOT_FOUND = -1   # documented not-found sentinel


def check(case_name: str, result, expected):
    if result == expected:
        print(f"PASS: {case_name}")
    else:
        print(f"FAIL: {case_name} — expected {expected!r}, got {result!r}")


# ---------------------------------------------------------------------------
# Case 1 — insertion_sort on an empty list
# ---------------------------------------------------------------------------
records = []
insertion_sort(records, "title")
check("insertion_sort — empty list stays empty", records, [])

# ---------------------------------------------------------------------------
# Case 2 — insertion_sort on a single-element list
# ---------------------------------------------------------------------------
records = [{"title": "only"}]
insertion_sort(records, "title")
check("insertion_sort — single element unchanged", records, [{"title": "only"}])

# ---------------------------------------------------------------------------
# Case 3 — binary_search finds value at FIRST index
# ---------------------------------------------------------------------------
sorted_list = [{"title": "alpha"}, {"title": "beta"}, {"title": "gamma"}]
idx = binary_search(sorted_list, "alpha", "title")
check("binary_search — value at first index", idx, 0)

# ---------------------------------------------------------------------------
# Case 4 — binary_search finds value at LAST index
# ---------------------------------------------------------------------------
idx = binary_search(sorted_list, "gamma", "title")
check("binary_search — value at last index", idx, 2)

# ---------------------------------------------------------------------------
# Case 5 — binary_search finds value at MIDDLE index
# ---------------------------------------------------------------------------
idx = binary_search(sorted_list, "beta", "title")
check("binary_search — value at middle index", idx, 1)

# ---------------------------------------------------------------------------
# Case 6 — binary_search returns not-found when target absent
# ---------------------------------------------------------------------------
idx = binary_search(sorted_list, "zeta", "title")
check("binary_search — absent target returns -1", idx, NOT_FOUND)

# ---------------------------------------------------------------------------
# Case 7a — insertion_sort_count: list is correctly sorted
# ---------------------------------------------------------------------------
records = [{"v": 3}, {"v": 1}, {"v": 2}]
insertion_sort_count(records, "v")
check(
    "insertion_sort_count — list correctly sorted after call",
    records,
    [{"v": 1}, {"v": 2}, {"v": 3}],
)

# ---------------------------------------------------------------------------
# Case 7b — insertion_sort_count: returns a plain int > 0 for multi-element list
# ---------------------------------------------------------------------------
records = [{"v": 3}, {"v": 1}, {"v": 2}]
count = insertion_sort_count(records, "v")
is_int_gt_zero = (type(count) == int) and (count > 0)
check("insertion_sort_count — returns int > 0 for multi-element list", is_int_gt_zero, True)

# ---------------------------------------------------------------------------
# Case 8 — binary_search_count: present value at known index
# ---------------------------------------------------------------------------
sorted_list = [{"title": "apple"}, {"title": "mango"}, {"title": "orange"}]
result = binary_search_count(sorted_list, "apple", "title")
index_ok = result["index"] == 0
count_ok = isinstance(result["comparison_count"], int) and result["comparison_count"] > 0
check("binary_search_count — 'index' is correct expected index (0)", index_ok, True)
check("binary_search_count — 'comparison_count' is int > 0", count_ok, True)

# ---------------------------------------------------------------------------
# Case 9 — linear_search_count: absent target → index=-1, count==len(list)
# ---------------------------------------------------------------------------
records = [{"title": "a"}, {"title": "b"}, {"title": "c"}]
result = linear_search_count(records, "z", "title")
check(
    "linear_search_count — absent target: index == -1",
    result["index"],
    NOT_FOUND,
)
check(
    "linear_search_count — absent target: comparison_count == len(list)",
    result["comparison_count"],
    len(records),
)

print("\nAll checks complete.")
