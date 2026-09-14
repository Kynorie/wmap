import json
from pathlib import Path

WMAP_DIR = Path.home() / ".wmap"
CONFIG_FILE = WMAP_DIR / "config.json"

DEFAULT_CONFIG = {
    "agreed": False,
}


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return dict(DEFAULT_CONFIG)

    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        return {**DEFAULT_CONFIG, **data}
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    WMAP_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def has_agreed() -> bool:
    return load_config().get("agreed", False)


def set_agreed(value: bool = True) -> None:
    config = load_config()
    config["agreed"] = value
    save_config(config)


def is_first_run() -> bool:
    return not CONFIG_FILE.exists()
