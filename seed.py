"""
seed.py — Populate the TaskFlow database with sample data and run the
Section 2 benchmark (comparison counts at three data sizes).

Usage:
    cd backend
    python ../seed.py

The script:
 1. Creates all tables (if not already present).
 2. Inserts a demo user, project, and N tasks at sizes 10, 500, 3000.
 3. Runs insertion_sort_count, binary_search_count, and linear_search_count
    on synthetic in-memory task dicts at each size and prints the counts.
 4. Saves results to results/benchmark_results.txt in the project root.
"""

import sys
import os
import random
import string

# Make sure 'backend/' is on the path so 'app' is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.database import engine, SessionLocal
from app.models import Base, User, Project, Task
from app.algorithms import (
    insertion_sort_count,
    binary_search_count,
    linear_search_count,
    insertion_sort,
)

SIZES = [10, 500, 3000]
PRIORITIES = ["low", "medium", "high"]
STATUSES = ["todo", "in_progress", "done"]


def random_title(length: int = 12) -> str:
    return "task_" + "".join(random.choices(string.ascii_lowercase, k=length))


def make_synthetic_tasks(n: int) -> list:
    return [
        {
            "id": i,
            "title": random_title(),
            "priority": random.choice(PRIORITIES),
            "due_date": random.choice(["today", "tomorrow", "next week", None]),
        }
        for i in range(n)
    ]


def seed_db():
    """Create tables and insert a minimal demo dataset."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Idempotent: skip if demo data already present
        if db.query(User).filter(User.email == "demo@taskflow.io").first():
            print("[seed] Demo data already present — skipping DB insert.")
            return

        user = User(name="Demo User", email="demo@taskflow.io")
        db.add(user)
        db.flush()

        project = Project(name="Demo Project", description="Seeded project", owner_id=user.id)
        db.add(project)
        db.flush()

        for i in range(10):
            task = Task(
                title=f"Seeded task {i + 1}",
                priority=PRIORITIES[i % 3],
                status=STATUSES[i % 3],
                project_id=project.id,
            )
            db.add(task)

        db.commit()
        print(f"[seed] Inserted demo user, project, and 10 tasks.")
    finally:
        db.close()


def run_benchmark() -> str:
    lines = []
    lines.append("=" * 64)
    lines.append("TaskFlow — Section 2 Algorithm Benchmark")
    lines.append("=" * 64)
    lines.append(f"{'Size':>6}  {'InsSort Cmps':>14}  {'BinSearch Cmps':>16}  {'LinSearch Cmps':>16}")
    lines.append("-" * 64)

    for n in SIZES:
        tasks = make_synthetic_tasks(n)

        # --- insertion sort count (sorts in place) ---
        is_tasks = [t.copy() for t in tasks]
        is_count = insertion_sort_count(is_tasks, "title")

        # --- binary search count (needs sorted list) ---
        bs_tasks = [t.copy() for t in tasks]
        insertion_sort(bs_tasks, "title")          # sort first (no counting)
        # Search for the title at the midpoint
        mid_title = bs_tasks[len(bs_tasks) // 2]["title"]
        bs_result = binary_search_count(bs_tasks, mid_title, "title")

        # --- linear search count (unsorted) ---
        ls_tasks = [t.copy() for t in tasks]
        ls_result = linear_search_count(ls_tasks, mid_title, "title")

        lines.append(
            f"{n:>6}  {is_count:>14,}  {bs_result['comparison_count']:>16,}  {ls_result['comparison_count']:>16,}"
        )

    lines.append("=" * 64)
    lines.append("")
    lines.append("Complexity Summary")
    lines.append("-" * 40)
    lines.append("insertion_sort : best O(n), worst O(n²)")
    lines.append("binary_search  : best O(1), worst O(log n)  [requires sorted input]")
    lines.append("linear_search  : best O(1), worst O(n)")
    lines.append("")
    lines.append("Analysis (sort-first trade-off)")
    lines.append("-" * 40)
    lines.append(
        "At n=3000, insertion_sort costs ~4.5 M comparisons (worst case O(n²)).\n"
        "Once the list is sorted, every binary search costs at most ~24 comparisons (O(log n)).\n"
        "Linear search on the unsorted list costs up to 3000 comparisons per query.\n"
        "For a team that sorts/views tasks many times a day but adds tasks infrequently,\n"
        "the one-time sort cost is amortised over many binary searches — each of which is\n"
        "~125× cheaper than a linear scan at n=3000.  The sort-first strategy is therefore\n"
        "worth it for TaskFlow's read-heavy usage pattern."
    )
    lines.append("=" * 64)
    return "\n".join(lines)


if __name__ == "__main__":
    seed_db()
    report = run_benchmark()
    print(report)

    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, "benchmark_results.txt")
    with open(out_path, "w") as f:
        f.write(report)
    print(f"\n[benchmark] Results saved to {out_path}")
