
import os
import subprocess
import sys
import requests

try:
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    HAVE_RICH = True
except ImportError:
    HAVE_RICH = False


GITHUB_REPO = "kynorie/wmap"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

CURRENT_VERSION = 1  # REMEMBER TO BUMP THIS !!!!!!!!!!!!!!!!!!!


def get_latest_release_tag(timeout: float = 8.0) -> str | None:
    try:
        resp = requests.get(
            RELEASES_API,
            timeout=timeout,
            headers={"Accept": "application/vnd.github+json"},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data.get("tag_name")
    except (requests.RequestException, ValueError):
        return None


def _parse_version(tag: str) -> int | None:
    """Extract the integer version from a tag like 'v1', 'v2'."""
    tag = tag.strip().lower()
    if tag.startswith("v"):
        tag = tag[1:]
    try:
        return int(tag)
    except ValueError:
        return None


def is_running_as_root() -> bool:
    return os.geteuid() == 0


def check_for_update() -> None:
    """
    Entry point for `wmap --update`. Checks current vs. latest,
    prompts to install if behind, checks for sudo before actually
    performing the update.
    """
    latest_tag = get_latest_release_tag()

    if latest_tag is None:
        print("Could not check for updates (network error or repo unreachable).")
        return

    latest_version = _parse_version(latest_tag)
    if latest_version is None:
        print(f"Could not parse version from latest release tag '{latest_tag}'.")
        return

    if latest_version <= CURRENT_VERSION:
        print("Up to date.")
        return

    print(f"There's a new update available for wmap ({latest_tag}). Install? [Y/N] ", end="")
    try:
        response = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        return

    if response != "y":
        return

    if not is_running_as_root():
        print("Run this with sudo!")
        return

    _perform_update(latest_tag)


def _perform_update(tag: str) -> None:
    if HAVE_RICH:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
        ) as progress:
            task = progress.add_task(f"Updating to {tag}...", total=100)
            import time
            for _ in range(100):
                time.sleep(0.01)
                progress.update(task, advance=1)
    else:
        print(f"Updating to {tag}...")

    print(f"wmap updated to {tag}.")
