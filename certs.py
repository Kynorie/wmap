import ssl
import socket
from datetime import datetime, timezone
from cryptography import x509
from cryptography.hazmat.backends import default_backend


def get_certificate_info(host: str, port: int = 443, timeout: float = 5.0) -> dict | None:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                der_cert = ssock.getpeercert(binary_form=True)
    except (socket.error, ssl.SSLError, OSError):
        return None

    if der_cert is None:
        return None

    try:
        cert = x509.load_der_x509_certificate(der_cert, default_backend())
    except ValueError:
        return None

    subject = cert.subject.rfc4514_string()
    issuer = cert.issuer.rfc4514_string()

    not_before = cert.not_valid_before_utc
    not_after = cert.not_valid_after_utc
    now = datetime.now(timezone.utc)

    try:
        san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        san_names = san_ext.value.get_values_for_type(x509.DNSName)
    except x509.ExtensionNotFound:
        san_names = []

    return {
        "subject": subject,
        "issuer": issuer,
        "valid_from": not_before.strftime("%Y-%m-%d"),
        "valid_until": not_after.strftime("%Y-%m-%d"),
        "expired": now > not_after,
        "days_remaining": (not_after - now).days if now <= not_after else 0,
        "san": san_names,
        "serial_number": format(cert.serial_number, "x"),
    }
