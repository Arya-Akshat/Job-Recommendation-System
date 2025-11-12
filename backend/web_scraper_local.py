"""Local placeholder scraper used to avoid import-time errors while the real scraper is being fixed.

This file provides fetch_and_update_jobs() with a safe, side-effect-free implementation
that returns 0 and logs an informational message. Replace with the real scraper when ready.
"""

import os


def fetch_and_update_jobs() -> int:
    """Placeholder: do not perform network I/O here. Return 0 new jobs.

    This keeps the backend importable for local development and testing.
    """
    print("fetch_and_update_jobs(): placeholder called — real scraper disabled for now.")
    return 0
