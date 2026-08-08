"""
Section 2 — Hand-rolled sorting and searching algorithms.
These are the real implementations wired into the task endpoints.
Never uses Python's built-in sorted() / list.sort().
"""

from typing import Any, Optional


# ---------------------------------------------------------------------------
# Insertion Sort
# ---------------------------------------------------------------------------

def insertion_sort(records: list, key: str) -> None:
    """
    Sort *records* in place by records[i][key] using insertion sort.
    Mutates the list directly; returns nothing (bare return / no return).

    Time complexity:
        Best case  : O(n)   — already sorted, inner loop never shifts
        Worst case : O(n²)  — reverse-sorted, inner loop shifts every element
    """
    for i in range(1, len(records)):
        current = records[i]
        current_val = current[key]
        j = i - 1
        while j >= 0 and records[j][key] > current_val:
            records[j + 1] = records[j]
            j -= 1
        records[j + 1] = current
    # bare return — mutated list is the result
    return


# ---------------------------------------------------------------------------
# Binary Search
# ---------------------------------------------------------------------------

def binary_search(sorted_records: list, target_value: Any, key: str) -> Optional[int]:
    """
    Search *sorted_records* (sorted by *key*) for a record whose [key] == target_value.
    Returns the index of a matching record, or -1 if not found.

    Precondition : records must be sorted ascending by *key* (use insertion_sort first).

    Time complexity:
        Best case  : O(1)   — target is at the midpoint on the first probe
        Worst case : O(log n) — target absent or at an extreme
    """
    low, high = 0, len(sorted_records) - 1
    while low <= high:
        mid = (low + high) // 2
        mid_val = sorted_records[mid][key]
        if mid_val == target_value:
            return mid
        elif mid_val < target_value:
            low = mid + 1
        else:
            high = mid - 1
    return -1


# ---------------------------------------------------------------------------
# Linear Search
# ---------------------------------------------------------------------------

def linear_search(records: list, target_value: Any, key: str) -> Optional[int]:
    """
    Scan *records* from the start and return the index of the first record
    whose [key] == target_value, or -1 if none found.

    Time complexity:
        Best case  : O(1)   — first element matches
        Worst case : O(n)   — target absent or at the last position
    """
    for idx, record in enumerate(records):
        if record[key] == target_value:
            return idx
    return -1


# ---------------------------------------------------------------------------
# Section 2 — Counting wrappers (for benchmark / Task 5)
# Same logic as above; different return contracts as specified.
# ---------------------------------------------------------------------------

def insertion_sort_count(records: list, key: str) -> int:
    """
    Identical to insertion_sort but returns only the comparison count (int).
    Sorts *records* in place.
    """
    comparisons = 0
    for i in range(1, len(records)):
        current = records[i]
        current_val = current[key]
        j = i - 1
        while j >= 0:
            comparisons += 1          # count every comparison against records[j][key]
            if records[j][key] > current_val:
                records[j + 1] = records[j]
                j -= 1
            else:
                break
        records[j + 1] = current
    return comparisons


def binary_search_count(sorted_records: list, target_value: Any, key: str) -> dict:
    """
    Identical to binary_search but returns {"index": int, "comparison_count": int}.
    """
    low, high = 0, len(sorted_records) - 1
    comparisons = 0
    while low <= high:
        mid = (low + high) // 2
        comparisons += 1
        mid_val = sorted_records[mid][key]
        if mid_val == target_value:
            return {"index": mid, "comparison_count": comparisons}
        comparisons += 1              # second comparison for < branch
        if mid_val < target_value:
            low = mid + 1
        else:
            high = mid - 1
    return {"index": -1, "comparison_count": comparisons}


def linear_search_count(records: list, target_value: Any, key: str) -> dict:
    """
    Identical to linear_search but returns {"index": int, "comparison_count": int}.
    """
    for idx, record in enumerate(records):
        if record[key] == target_value:
            return {"index": idx, "comparison_count": idx + 1}
    # Scanned the entire list without finding the target
    return {"index": -1, "comparison_count": len(records)}
