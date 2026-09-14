import sys


FIRST_RUN_NOTICE = """
Thank you for using wmap!

Please remember: use wmap only on IP address(es) you own
or IP address(es) you have explicit permission to scan.
Scanning an IP you don't have permission to scan may violate laws.

Type wmap --i-agree to skip this warning in the future.
"""

SCAN_REMINDER = """
Remember: using wmap on IP address(es) you own, or have
explicit permission to scan, is fine.

Scanning an IP you don't have permission to scan may violate laws.
"""


def show_first_run_notice() -> None:
    print(FIRST_RUN_NOTICE)


def confirm_scan(target: str, agreed: bool) -> bool:
    if agreed:
        return True

    print(SCAN_REMINDER)
    try:
        response = input(f"Continue scanning {target}? [Y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        return False

    return response == "y"
