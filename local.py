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


def is_local_target(target: str) -> bool:
    try:
        if "/" in target:
            network = ipaddress.ip_network(target, strict=False)
        else:
            network = ipaddress.ip_network(f"{target}/32", strict=False)
    except ValueError:
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
