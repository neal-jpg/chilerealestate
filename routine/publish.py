"""Commit + push the regenerated data, then confirm GitHub Pages actually
deployed it (re-triggering on the transient 'Deployment failed, try again
later' error that otherwise silently leaves the site stale)."""

import json
import subprocess
import time
import urllib.request


def run_git(args, cwd, check=True):
    """Run a git command in cwd. Returns the exit code; raises on failure if check."""
    result = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.returncode


def publish(repo_dir, message):
    """Stage data/, commit, push. Returns True if a commit was made, False if
    there was nothing to commit (git commit exits non-zero on an empty index)."""
    run_git(["add", "data"], repo_dir)
    if run_git(["commit", "-m", message], repo_dir, check=False) != 0:
        return False
    run_git(["push"], repo_dir)
    return True


def retrigger(repo_dir):
    """Empty commit + push to re-kick a failed Pages deploy."""
    run_git(["commit", "--allow-empty", "-m", "chore: re-trigger GitHub Pages deploy"], repo_dir)
    run_git(["push"], repo_dir)


def cache_bust(url, ts):
    """Append a cb= cache-buster, honoring any existing query string."""
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}cb={ts}"


def fetch_text(url):
    """Fetch a URL's text, cache-busted. Network shell."""
    with urllib.request.urlopen(cache_bust(url, int(time.time())), timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def build_date_from_meta(meta_text):
    """Pull build_date out of a fetched meta.json body, or None."""
    try:
        return json.loads(meta_text).get("build_date")
    except (ValueError, AttributeError):
        return None


def verify_deploy(expected_date, check_fn, retrigger_fn, attempts,
                  polls=5, poll_seconds=30, sleep_fn=time.sleep):
    """Confirm the live build_date matches expected_date. Within each attempt,
    poll up to `polls` times (sleeping poll_seconds between checks) to let a
    normal deploy land, and only retrigger if it never shows up — so a slow but
    successful deploy doesn't spawn a spurious empty commit. Returns True once
    matched, False after all attempts are exhausted. sleep_fn is injected so the
    loop runs instantly in tests."""
    for attempt in range(attempts):
        for _ in range(polls):
            sleep_fn(poll_seconds)
            if check_fn() == expected_date:
                return True
        if attempt < attempts - 1:
            retrigger_fn()
    return False
