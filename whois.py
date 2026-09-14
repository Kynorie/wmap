import requests
from datetime import datetime, timezone

try:
    import whois as pywhois
    HAVE_PYTHON_WHOIS = True
except ImportError:
    HAVE_PYTHON_WHOIS = False


RDAP_BOOTSTRAP_URL = "https://rdap.org/domain/{domain}"


def _years_ago(date: datetime) -> int:
    now = datetime.now(timezone.utc)
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return int((now - date).days // 365.25)


def _rdap_lookup(domain: str, timeout: float = 8.0) -> dict | None:
    try:
        resp = requests.get(RDAP_BOOTSTRAP_URL.format(domain=domain), timeout=timeout)
        if resp.status_code != 200:
            return None
        data = resp.json()
    except (requests.RequestException, ValueError):
        return None

    for event in data.get("events", []):
        if event.get("eventAction") == "registration":
            try:
                reg_date = datetime.fromisoformat(
                    event["eventDate"].replace("Z", "+00:00")
                )
            except (KeyError, ValueError):
                continue
            return {
                "registered": reg_date.strftime("%Y-%m-%d"),
                "years_ago": _years_ago(reg_date),
            }

    return None


def _whois_lookup(domain: str) -> dict | None:
    if not HAVE_PYTHON_WHOIS:
        return None

    try:
        w = pywhois.whois(domain)
        creation = w.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        if creation is None:
            return None
        return {
            "registered": creation.strftime("%Y-%m-%d"),
            "years_ago": _years_ago(creation),
        }
    except Exception:
        return None


def get_domain_age(domain: str) -> dict | None:
    result = _rdap_lookup(domain)
    if result is not None:
        return result

    return _whois_lookup(domain)
