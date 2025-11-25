import csv
import os
import socket
from dataclasses import asdict, dataclass, fields
from typing import Dict, List

import yaml
from dotenv import load_dotenv


@dataclass
class Rule:
    # Non-default fields first, then fields with defaults
    source_hostname: str
    source_ip_address: str
    source_lob: str
    destination_hostname: str
    destination_ip_address: str
    destination_protocol_port: str
    destination_lob: str
    add_modify_remove: str = "Add"
    temporary: str = "No"


def main() -> None:
    load_dotenv()

    hosts_filename = os.getenv("HOSTS")
    if not hosts_filename:
        print("Environment variable HOSTS is not set.")
        return

    servers_filename = os.getenv("SERVERS")
    if not servers_filename:
        print("Environment variable SERVERS is not set.")
        return

    csv_filename = os.getenv("CSVOUT")
    if not csv_filename:
        print("Environment variable CSVOUT is not set.")
        return

    print("Loading hosts from", hosts_filename)
    print("Loading servers from", servers_filename)
    print("Writing FACR rules to", csv_filename)

    server_list = load_servers(servers_filename)
    host_list = load_hosts(hosts_filename)
    rules = generate_rules(host_list, "FUELS", server_list, "CONINFRA")
    write_rules_to_csv(rules, csv_filename)


def load_hosts(filename: str) -> List[Dict[str, str]]:
    hosts_list = []

    with open(filename, "r") as file:
        hosts = [line.strip() for line in file if line.strip()]

    for hostname in hosts:
        host = {}
        host["hostname"] = hostname
        hosts_list.append(host)

    return [add_server_info(host) for host in hosts_list]


def load_servers(yaml_file: str) -> dict[str, any]:
    with open(yaml_file, "r") as file:
        servers = yaml.safe_load(file)

    return [add_server_info(server) for server in servers]


def add_server_info(server: dict[str, any]) -> dict[str, any]:
    server["ip_address"] = get_ip_address(server["hostname"])
    server["hostname"] = get_fqdn(server["ip_address"])
    return server


def get_ip_address(hostname: str) -> str | None:
    try:
        ip_address = socket.gethostbyname(hostname)
    except socket.error:
        ip_address = None

    if ip_address is None:
        print(f"Could not resolve IP for hostname: {hostname}")
        return None

    return ip_address


def get_fqdn(ip):
    try:
        fqdn = socket.getfqdn(ip)
    except socket.error:
        fqdn = None

    if fqdn is None:
        print(f"Could not resolve fqdn for ip: {ip}")
        return None

    return fqdn


def generate_rules(
    host_list: List[Dict[str, str]],
    host_lob: str,
    server_list: List[Dict[str, str]],
    server_lob: str = "CONINFRA",
) -> List[Rule]:
    rules = []

    for host in host_list:
        for server in server_list:
            rule = Rule(
                source_hostname=host["hostname"],
                source_ip_address=host["ip_address"],
                source_lob=host_lob,
                destination_hostname=server["hostname"],
                destination_ip_address=server["ip_address"],
                destination_lob=server_lob,
                destination_protocol_port=server["incoming_protocol_port"],
            )
            rules.append(rule)

    for server in server_list:
        for host in host_list:
            rule = Rule(
                source_hostname=server["hostname"],
                source_ip_address=server["ip_address"],
                source_lob="CONINFRA",
                destination_hostname=host["hostname"],
                destination_ip_address=host["ip_address"],
                destination_lob=host_lob,
                destination_protocol_port=server["outgoing_protocol_port"],
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
