"""
Section 3 — Deterministic mock parser for the AI quick-add feature.

parse_task_description(description: str) -> dict
    Returns {"title": str, "priority": str, "due_date_hint": str | None}

Algorithm is fully deterministic — any two correct implementations produce
identical output for any given input.  Zero network calls, zero API keys.

The "prompt" structure (system + user roles) is preserved as docstrings/comments
so the code mirrors how a real LLM call would be structured.

Prompting technique: ZERO-SHOT
  The system message gives a precise, rule-based spec of the extraction task;
  the user message carries the raw description.  No examples are embedded in the
  prompt itself.  Zero-shot is appropriate here because the rules are fully
  deterministic and enumerable — few-shot examples would add token cost without
  improving reliability for a rule-based mock.
"""

import re
from typing import Optional


# ---------------------------------------------------------------------------
# "Prompt" structure (mirrors what a real LLM integration would send)
# ---------------------------------------------------------------------------

SYSTEM_MESSAGE = (
    "You are a task-extraction assistant. "
    "Given a free-text task description, extract: "
    "(1) title — the description stripped of priority and date keywords, trimmed; "
    "    if the result is empty or whitespace, return 'Untitled task'. "
    "(2) priority — 'high' if 'urgent'/'asap' present, "
    "    'low' if 'whenever'/'low priority' present (high wins on conflict), "
    "    otherwise 'medium'. "
    "(3) due_date_hint — first matched date phrase, or null. "
    "Return JSON with keys title, priority, due_date_hint."
)

# The user message template (filled at call time):
# USER_MESSAGE = f"Description: {description}"

# ---------------------------------------------------------------------------
# Keyword definitions (exact order matters per spec)
# ---------------------------------------------------------------------------

PRIORITY_HIGH_KEYWORDS = ["urgent", "asap"]
PRIORITY_LOW_KEYWORDS = ["whenever", "low priority"]

DATE_PHRASES_ORDERED = [
    "today",
    "tomorrow",
    "next week",
    "next monday",
    "next tuesday",
    "next wednesday",
    "next thursday",
    "next friday",
    "next saturday",
    "next sunday",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def _remove_all_occurrences(text: str, phrase: str) -> str:
    """
    Remove every case-insensitive occurrence of *phrase* from *text*.
    Works on the original-cased text using a case-insensitive regex.
    """
    pattern = re.compile(re.escape(phrase), re.IGNORECASE)
    return pattern.sub("", text)


def parse_task_description(description: str) -> dict:
    """
    Deterministic mock that simulates an LLM response for quick-add.

    Parameters
    ----------
    description : str
        Raw free-text task description from the user.

    Returns
    -------
    dict with keys:
        title          : str   (never empty)
        priority       : str   ("low" | "medium" | "high")
        due_date_hint  : str | None
    """
    # (a) Working copy for keyword matching — lower-cased
    lower = description.lower()

    # -----------------------------------------------------------------------
    # (b) Priority detection — first matching group wins
    # -----------------------------------------------------------------------
    has_high = any(kw in lower for kw in PRIORITY_HIGH_KEYWORDS)
    has_low = any(kw in lower for kw in PRIORITY_LOW_KEYWORDS)

    if has_high:
        priority = "high"
    elif has_low:
        priority = "low"
    else:
        priority = "medium"

    # -----------------------------------------------------------------------
    # (c) Due-date hint — first matching phrase in order
    # -----------------------------------------------------------------------
    due_date_hint: Optional[str] = None
    matched_date_phrase: Optional[str] = None

    for phrase in DATE_PHRASES_ORDERED:
        if phrase in lower:
            due_date_hint = phrase          # exact matched text, lower-case
            matched_date_phrase = phrase
            break

    # -----------------------------------------------------------------------
    # (d) Title derivation — strip from original-cased description
    #     Per spec: strip ALL group (i)/(ii) keywords (not just the deciding one)
    #     plus every occurrence of the matched date phrase (if any).
    # -----------------------------------------------------------------------
    title = description

    # Strip every priority keyword found anywhere (all of group i and group ii)
    for kw in PRIORITY_HIGH_KEYWORDS + PRIORITY_LOW_KEYWORDS:
        title = _remove_all_occurrences(title, kw)

    # Strip every occurrence of the matched date phrase
    if matched_date_phrase:
        title = _remove_all_occurrences(title, matched_date_phrase)

    title = title.strip()

    # Clean up double-spaces and leading/trailing punctuation artefacts
    title = re.sub(r"[ \t]{2,}", " ", title).strip()

    # Fallback to placeholder if the result is empty or whitespace-only
    if not title:
        title = "Untitled task"

    return {
        "title": title,
        "priority": priority,
        "due_date_hint": due_date_hint,
    }
