import requests
import dns.resolver
import dns.exception
from concurrent.futures import ThreadPoolExecutor, as_completed


CRT_SH_URL = "https://crt.sh/?q=%25.{domain}&output=json"

DEFAULT_WORDLIST = [
    "www", "mail", "ftp", "api", "dev", "staging", "test", "admin",
    "portal", "app", "blog", "shop", "store", "support", "help",
    "docs", "cdn", "static", "assets", "img", "images", "media",
    "vpn", "remote", "git", "gitlab", "jenkins", "ci", "monitor",
    "status", "beta", "demo", "secure", "login", "auth", "sso",
    "webmail", "ns1", "ns2", "mx", "smtp", "pop", "imap",
]


def passive_discovery(domain: str, timeout: float = 10.0) -> list[str]:
    hostnames = set()

    try:
        resp = requests.get(
            CRT_SH_URL.format(domain=domain),
            timeout=timeout,
            headers={"User-Agent": "wmap (https://github.com/opencinnamon/wmap)"},
        )
        resp.raise_for_status()
        entries = resp.json()
    except (requests.RequestException, ValueError):
        return []

    for entry in entries:
        name_value = entry.get("name_value", "")
        for name in name_value.split("\n"):
            name = name.strip().lower()
            if name and not name.startswith("*."):
                hostnames.add(name)
            elif name.startswith("*."):
                hostnames.add(name[2:])

    return sorted(hostnames)


def _resolve_one(subdomain: str, domain: str, resolver: dns.resolver.Resolver) -> str | None:
    """Helper for active_discovery's thread pool — resolves a single
    candidate subdomain, returns it if it resolves, else None."""
    fqdn = f"{subdomain}.{domain}"
    try:
        resolver.resolve(fqdn, "A")
        return fqdn
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.Timeout):
        return None
    except dns.exception.DNSException:
        return None


def active_discovery(
    domain: str,
    wordlist: list[str] | None = None,
    max_workers: int = 10,
    timeout: float = 3.0,
) -> list[str]:
    words = wordlist if wordlist is not None else DEFAULT_WORDLIST

    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout

    found = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_resolve_one, word, domain, resolver): word
            for word in words
        }
        for future in as_completed(futures):
            result = future.result()
            if result:
                found.append(result)

    return sorted(found)


def discover(domain: str, active: bool = False, wordlist: list[str] | None = None) -> list[str]:
    hosts = set(passive_discovery(domain))

    if active:
        hosts.update(active_discovery(domain, wordlist=wordlist))

    return sorted(hosts)
