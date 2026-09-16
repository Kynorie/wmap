import ipaddress
import socket
import re
import requests

LOCAL_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
]


IP_SHAPE_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.")


def clean_target(raw: str) -> str:
    cleaned = raw.strip()
    cleaned = cleaned.strip("'\"")
    cleaned = cleaned.strip()
    cleaned = re.sub(r"^https?://", "", cleaned, flags=re.IGNORECASE)

    if "/" in cleaned:
        head, tail = cleaned.split("/", 1)
        if tail.isdigit() and int(tail) <= 128:
            cleaned = f"{head}/{tail}"
        else:
            cleaned = head

    cleaned = cleaned.rstrip(",;'\"")
    return cleaned


def parse_ip_network(target: str) -> ipaddress.IPv4Network | ipaddress.IPv6Network | None:
    try:
        if "/" in target:
            return ipaddress.ip_network(target, strict=False)
        return ipaddress.ip_network(f"{target}/32", strict=False)
    except ValueError:
        return None


def looks_like_broken_ip(target: str) -> bool:
    return IP_SHAPE_RE.match(target) is not None and parse_ip_network(target) is None


def is_local_target(target: str) -> bool:
    network = parse_ip_network(target)
    if network is None:
        return False

    return any(
        network.subnet_of(local_net) for local_net in LOCAL_NETWORKS
    )


def get_local_title(host: str, port: int, timeout: float = 3.0) -> str:
    for scheme in ("http", "https"):
        try:
            resp = requests.get(
                f"{scheme}://{host}:{port}",
                timeout=timeout,
                verify=False,
            )
            match = re.search(
                r"<title[^>]*>(.*?)</title>", resp.text, re.IGNORECASE | re.DOTALL
            )
            if match:
                return match.group(1).strip()
            return "Untitled"
        except requests.RequestException:
            continue

    return "Unknown service"


def scan_local_ports(host: str, ports: list[int], timeout: float = 0.5) -> list[int]:
    open_ports = []
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            result = sock.connect_ex((host, port))
            if result == 0:
                open_ports.append(port)
        except socket.error:
            pass
        finally:
            sock.close()

    return open_ports


COMMON_LOCAL_PORTS = [
    80, 443, 3000, 5000, 8000, 8080, 8081, 8443, 8888, 9000,
]
