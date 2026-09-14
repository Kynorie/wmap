import json
import os
from datetime import datetime, timezone
from pathlib import Path


WMAP_DIR = Path.home() / ".wmap"
RESULT_FILE = WMAP_DIR / "last_scan.json"


def ensure_wmap_dir() -> None:
    WMAP_DIR.mkdir(parents=True, exist_ok=True)


def save_results(target: str, is_local: bool, results: list[dict]) -> None:
    """Write the scan results to the JSON cache, overwriting any
    previous scan. Schema:

    {
      "scanned_at": ISO8601 timestamp,
      "target": the CIDR/IP/domain that was scanned,
      "is_local": bool,
      "results": [
        {
          "host": "example.com" or "127.0.0.1:8888",
          "type": "public" | "local",
          "domain_age": {"registered": ..., "years_ago": ...} | None,
          "title": str | None,   # local only
          "cert": {...} | None   # populated by --result-deep
        },
        ...
      ]
    }
    """
    ensure_wmap_dir()

    data = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "target": target,
        "is_local": is_local,
        "results": results,
    }

    with open(RESULT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_results() -> dict | None:
    if not RESULT_FILE.exists():
        return None

    try:
        with open(RESULT_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def update_cert_field(host: str, cert_info: dict | None) -> None:
    data = load_results()
    if data is None:
        return

    for entry in data["results"]:
        if entry["host"] == host:
            entry["cert"] = cert_info
            break

    with open(RESULT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def format_results(data: dict, deep: bool = False) -> str:
    results = data.get("results", [])
    is_local = data.get("is_local", False)

    if not results:
        return "No websites found."

    lines = []
    count = len(results)
    label = "local website" if is_local else "Website"
    plural = "s" if count != 1 else ""
    lines.append(f"Found {count} {label}{plural}!")
    lines.append("")

    for entry in results:
        host = entry["host"]

        if entry.get("type") == "local":
            title = entry.get("title", "Unknown service")
            lines.append(f"{host} ({title})")
        else:
            age = entry.get("domain_age")
            if age:
                lines.append(f"{host} (Registered in {age['registered'][:4]}, {age['years_ago']} years ago)")
            else:
                lines.append(f"{host} (Registration date unavailable)")

        if deep and entry.get("cert"):
            cert = entry["cert"]
            lines.append(f"  Subject: {cert['subject']}")
            lines.append(f"  Issuer: {cert['issuer']}")
            lines.append(f"  Valid: {cert['valid_from']} to {cert['valid_until']}")
            if cert.get("expired"):
                lines.append(f"  ⚠ EXPIRED")
            else:
                lines.append(f"  ({cert['days_remaining']} days remaining)")
            if cert.get("san"):
                lines.append(f"  SANs: {', '.join(cert['san'])}")
            lines.append("")

    return "\n".join(lines)
