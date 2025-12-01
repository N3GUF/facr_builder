import csv
import os
import socket
from dataclasses import asdict, dataclass, fields
from enum import Enum
from typing import Dict, List, Optional

import click
import yaml
from dotenv import load_dotenv

LOB = Enum("CONINFRA", "FUELS", "PAYMENTS")


@dataclass
class Rule:
    # Non-default fields first, then fields with defaults
    source_hostname: str
    source_ip_address: str
    source_lob: str
    destination_hostname: str
    destination_ip_address: str
    destination_lob: str
    destination_protocol_port: str
    add_modify_remove: str = "Add"
    temporary: str = "No"


@click.command()
@click.option("--hosts", default="HOSTS", help="Path to a list of hosts.")
@click.option(
    "--lob",
    type=click.Choice(["CONINFRA", "FUELS", "PAYMENTS"], case_sensitive=False),
    default="FUELS",
    show_default=True,
    help="LOB for the hosts.",
)
@click.option(
    "--output",
    default="OUTPUT.csv",
    show_default=True,
    help="Path to the output CSV file.",
)
@click.argument("service_names", nargs=-1, type=str)
def main(hosts, lob, output, service_names) -> None:
    load_dotenv()

    if hosts == "HOSTS":
        hosts_filename = os.getenv("HOSTS")
        if not hosts_filename:
            print("Environment variable HOSTS is not set.")
            return -1

    services_filename = os.getenv("SERVICES")
    if not services_filename:
        print("Environment variable SERVICES is not set.")
        return -1

    if output == "OUTPUT.csv":
        csv_filename = os.getenv("CSVOUT")
        if not csv_filename:
            print("Environment variable CSVOUT is not set.")
            return -1

    print("Loading hosts from", hosts_filename)
    print("Loading services from", services_filename)

    services = load_services(services_filename)

    if len(service_names) == 0:
        print("No service name(s) provided.\n")
        list_available_services(services)
        return -1

    hosts = load_hosts(hosts_filename)
    hosts = [add_server_info(host) for host in hosts]
    rules = []

    for name in service_names:
        service = get_service(name=name, services=services)

        if service is None:
            print("Skipping service", name)
            continue

        print(f"Generating rules to connect to {name}.")
        rules.extend(generate_rules_for_service(hosts, lob, service))

    if len(rules) > 0:
        print(f"Writing {len(rules)} rules to {csv_filename}.")
        write_rules_to_csv(rules, csv_filename)


def load_hosts(filename: str) -> List[Dict[str, str]]:
    host_list = []

    with open(filename, "r") as file:
        hosts = [line.strip() for line in file if line.strip()]

    for hostname in hosts:
        host = {}
        host["hostname"] = hostname
        host_list.append(host)

    return host_list


def load_services(yaml_file: str) -> Dict[str, any]:
    with open(yaml_file, "r") as file:
        services = yaml.safe_load(file)

    return services


def list_available_services(services: Dict[str, any]) -> None:
    print("Available services:")
    [print("  -", service_name) for service_name in services.keys()]


def get_service(name: str, services: Dict[str, any]) -> Optional[Dict[str, any]]:
    if name.lower() in services.keys():
        return services.get(name.lower(), None)
    else:
        print(f"Service '{name}' not found in services list.")
        return None


def add_server_info(server: dict[str, any]) -> dict[str, any]:
    server["ip_address"] = get_ip_address(server["hostname"])
    server["hostname"] = get_fqdn(server["hostname"])
    return server


def get_ip_address(hostname: str) -> Optional[str]:
    try:
        ip_address = socket.gethostbyname(hostname)
    except socket.error:
        ip_address = None

    if ip_address is None:
        print(f"Could not resolve IP for hostname: {hostname}")
        return None

    return ip_address


def get_fqdn(host_or_ip):
    try:
        fqdn = socket.getfqdn(host_or_ip)
    except socket.error:
        fqdn = None

    if fqdn is None:
        print(f"Could not resolve fqdn for host or ip: {host_or_ip}")
        return None

    return fqdn


def generate_rules_for_service(hosts, lob, service) -> List[Rule]:
    if service.get("bi-directional", False):
        print("Bi-directional communication enabled between hosts and services.")

    if service.get("incoming") is not None:
        service["incoming"] = [
            add_server_info(server) for server in service.get("incoming", [])
        ]
    if service.get("outgoing") is not None:
        service["outgoing"] = [
            add_server_info(server) for server in service.get("outgoing", [])
        ]

    rules = generate_rules(hosts, lob, service, service.get("lob", "CONINFRA"))
    return rules


def generate_rules(
    hosts: List[Dict[str, str]],
    host_lob: str,
    service: Dict[str, str],
    service_lob: str = "CONINFRA",
) -> List[Rule]:
    rules = []

    for host in hosts:
        for server in service["incoming"]:
            rule = Rule(
                source_hostname=host["hostname"],
                source_ip_address=host["ip_address"],
                source_lob=host_lob,
                destination_hostname=server["hostname"],
                destination_ip_address=server["ip_address"],
                destination_lob=service_lob,
                destination_protocol_port=server["protocol_port"],
            )
            rules.append(rule)

    if not service.get("bi-directional", False):
        return rules

    for server in service["outgoing"]:
        for host in hosts:
            rule = Rule(
                source_hostname=server["hostname"],
                source_ip_address=server["ip_address"],
                source_lob="CONINFRA",
                destination_hostname=host["hostname"],
                destination_ip_address=host["ip_address"],
                destination_lob=host_lob,
                destination_protocol_port=server["protocol_port"],
            )
            rules.append(rule)

    return rules


def write_rules_to_csv(rules: List[Rule], filename: str) -> None:
    """Write a list of Rule dataclass instances to a CSV file.

    The CSV header is taken from the Rule dataclass field names in order.
    """
    # Ensure we have the header fields in the dataclass order
    header = [f.name for f in fields(Rule)]

    # Write the CSV
    with open(filename, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        for rule in rules:
            writer.writerow(asdict(rule))


if __name__ == "__main__":
    main()
