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


def fetch_text(url):
    """Fetch a URL's text, cache-busted. Network shell."""
    busted = f"{url}?cb={int(time.time())}"
    with urllib.request.urlopen(busted, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def build_date_from_meta(meta_text):
    """Pull build_date out of a fetched meta.json body, or None."""
    try:
        return json.loads(meta_text).get("build_date")
    except (ValueError, AttributeError):
        return None


def verify_deploy(expected_date, check_fn, retrigger_fn, attempts, wait_fn=time.sleep):
    """Poll check_fn() for expected_date; re-trigger and retry if stale. Returns
    True once the live build_date matches, False if all attempts are exhausted.
    check_fn/retrigger_fn/wait_fn are injected so the loop is testable offline."""
    for _ in range(attempts):
        wait_fn()
        if check_fn() == expected_date:
            return True
        retrigger_fn()
    return False
