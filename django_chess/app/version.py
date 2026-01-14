"""Utility for getting the application version."""
import os
import subprocess
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def get_version() -> str:
    """
    Get the application version (git commit hash).

    First tries to read from version.html template (for production).
    Falls back to git rev-parse HEAD (for development).
    Returns "unknown" if neither method works.
    """
    # Try reading from version.html first (production)
    version_file = Path(__file__).parent / "templates" / "app" / "version.html"
    if version_file.exists():
        try:
            content = version_file.read_text().strip()
            # First line is the commit hash
            commit_hash = content.split('\n')[0].strip()
            if commit_hash and len(commit_hash) >= 7:
                return commit_hash[:7]  # Return short hash
        except Exception:
            pass

    # Fall back to git (development)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        full_hash = result.stdout.strip()
        return full_hash[:7]  # Return short hash
    except Exception:
        pass

    return "unknown"
