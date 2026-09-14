#!/usr/bin/env python3

import argparse
import sys

import config
import notices
import local
import discovery
import whois
import certs
import update
import output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wmap",
        description="wmap — map websites, subdomains, and hosts on a network range.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="IP address, CIDR range, or domain to scan",
    )
    parser.add_argument(
        "--active",
        action="store_true",
        help="enable active DNS brute-force discovery (sends traffic to target's DNS)",
    )
    parser.add_argument(
        "--wordlist",
        metavar="PATH",
        help="path to a custom wordlist for --active brute-force",
    )
    parser.add_argument(
        "--i-agree",
        action="store_true",
        help="acknowledge the permission notice permanently, skip future prompts",
    )
    parser.add_argument(
        "--result",
        action="store_true",
        help="show the results of the last scan",
    )
    parser.add_argument(
        "--result-deep",
        action="store_true",
        help="show the results of the last scan, including SSL/TLS certificate details",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="check for and install wmap updates",
    )
    return parser


def load_wordlist(path: str) -> list[str]:
    with open(path, "r") as f:
        return [line.strip() for line in f if line.strip()]


def run_deep_lookup(data: dict) -> dict:
    """For --result-deep: fetch cert info for any public host in the
    cached results that doesn't have it yet, update the cache."""
    for entry in data["results"]:
        if entry.get("type") == "public" and entry.get("cert") is None:
            host = entry["host"]
            cert_info = certs.get_certificate_info(host)
            entry["cert"] = cert_info
            output.update_cert_field(host, cert_info)

    return data


def run_scan(target: str, active: bool, wordlist_path: str | None) -> None:
    is_local = local.is_local_target(target)

    if not is_local:
        agreed = config.has_agreed()
        proceed = notices.confirm_scan(target, agreed=agreed)
        if not proceed:
            print("Scan cancelled.")
            return

    results = []

    if is_local:
        host_str = target.split("/")[0]
        open_ports = local.scan_local_ports(host_str, local.COMMON_LOCAL_PORTS)

        for port in open_ports:
            title = local.get_local_title(host_str, port)
            results.append({
                "host": f"{host_str}:{port}",
                "type": "local",
                "title": title,
                "domain_age": None,
                "cert": None,
            })
    else:
        wordlist = load_wordlist(wordlist_path) if wordlist_path else None
        hosts = discovery.discover(target, active=active, wordlist=wordlist)

        for host in hosts:
            age = whois.get_domain_age(host)
            results.append({
                "host": host,
                "type": "public",
                "domain_age": age,
                "cert": None,
            })

    output.save_results(target, is_local, results)

    data = output.load_results()
    print(output.format_results(data))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.i_agree:
        config.set_agreed(True)
        print("Preference saved. Future scans won't show the permission reminder.")
        return

    if args.update:
        update.check_for_update()
        return

    if args.result or args.result_deep:
        data = output.load_results()
        if data is None:
            print("No previous scan results found. Run a scan first.")
            return
        if args.result_deep:
            data = run_deep_lookup(data)
        print(output.format_results(data, deep=args.result_deep))
        return

    if not args.target:
        if config.is_first_run():
            notices.show_first_run_notice()
            config.save_config(config.load_config())
        parser.print_help()
        return

    if config.is_first_run():
        notices.show_first_run_notice()
        config.save_config(config.load_config())

    run_scan(args.target, active=args.active, wordlist_path=args.wordlist)


if __name__ == "__main__":
    main()
