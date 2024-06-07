#!/bin/env python3

import argparse
import json
import operator
import os
import subprocess
import sys
import yaml

from pathlib import Path


def maas_cli(maas_user, command):
    command_list = ["maas", maas_user] + command
    str_command = [str(i) for i in command_list]
    result = subprocess.check_output(str_command)
    return json.loads(result)


def get_machines(maas_user, subnet):
    machines_dict = {}  # name: {system_id, interface_id, ip}
    raw = maas_cli(maas_user, ["machines", "read"])
    raw_sorted = sorted(raw, key=operator.itemgetter("hostname"))
    for machine in raw_sorted:
        desired_data = {}
        desired_data["system_id"] = machine["system_id"]
        desired_data["public_ip"] = get_ip_address(machine["interface_set"], subnet)
        machines_dict[machine["hostname"]] = desired_data
    return machines_dict


def get_ip_address(interfaces, subnet):
    ip_address = None
    for interface in interfaces:
        for link in interface["links"]:
            if link.get("subnet", {}).get("name") == subnet:
                # assuming there is only one interface with a static ip on the subnet
                if ip_address is None:
                    ip_address = link.get("ip_address")
    return ip_address


def write_snappy_config(output_dir, hostname, machine):
    snappy_config_path = os.path.join(output_dir, f"{hostname}_snappy.yaml")
    snappy_config = {}
    if os.path.exists(snappy_config_path):
        with open(snappy_config_path) as f:
            snappy_config = yaml.safe_load(f)

    snappy_config["device_ip"] = machine["public_ip"]
    snappy_config["node_id"] = machine["system_id"]
    snappy_config["node_name"] = hostname
    snappy_config["maas_user"] = "testflinger-maastiff"
    snappy_config["agent_name"] = hostname
    if snappy_config.get("env") is None:
        snappy_config["env"] = {}
    snappy_config["env"]["DEVICE_IP"] = machine["public_ip"]
    with open(snappy_config_path, "w") as f:
        f.write(yaml.safe_dump(snappy_config, sort_keys=False))


def write_testflinger_config(output_dir, hostname, machine):
    testflinger_config_path = os.path.join(output_dir, f"{hostname}.conf")
    testflinger_config = {}
    if os.path.exists(testflinger_config_path):
        with open(testflinger_config_path) as f:
            testflinger_config = yaml.safe_load(f)
            print("loaded existing data")

    testflinger_config["agent_id"] = hostname
    testflinger_config["server_address"] = "https://testflinger.canonical.com:443"
    testflinger_config["global_timeout"] = 172800
    testflinger_config["output_timeout"] = 43200
    testflinger_config[
        "execution_basedir"
    ] = f"/data/testflinger/agent/tests/{hostname}/run"
    testflinger_config[
        "logging_basedir"
    ] = f"/data/testflinger/agent/tests/{hostname}/logs"
    testflinger_config[
        "results_basedir"
    ] = f"/data/testflinger/agent/tests/{hostname}/results"
    testflinger_config["logging_level"] = "INFO"
    if testflinger_config.get("job_queues") is None:
        testflinger_config["job_queues"] = []
    testflinger_config["job_queues"].extend([hostname, "anything"])
    testflinger_config["job_queues"] = list(set(testflinger_config["job_queues"]))
    testflinger_config["setup_command"] = "echo Setup"
    testflinger_config[
        "provison_command"
    ] = f"PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 snappy-device-agent maas2 provision -c /data/testflinger/device-connectors/sut/{hostname}_snappy.yaml testflinger.json"
    testflinger_config[
        "test_command"
    ] = f"PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 snappy-device-agent maas2 runtest -c /data/testflinger/device-connectors/sut/{hostname}_snappy.yaml testflinger.json"
    testflinger_config[
        "allocate_command"
    ] = f"PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 snappy-device-agent maas2 allocate -c /srv/testflinger/agent/sut/{hostname}_snappy.yaml testflinger.json"
    testflinger_config[
        "reserve_command"
    ] = f"PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 snappy-device-agent maas2 reserve -c /data/testflinger/device-connectors/sut/{hostname}_snappy.yaml testflinger.json"
    testflinger_config[
        "cleanup_command"
    ] = f"PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 snappy-device-agent maas2 cleanup -c /srv/testflinger/agent/sut/{hostname}_snappy.yaml testflinger.json || /bin/true"

    with open(testflinger_config_path, "w") as f:
        f.write(yaml.safe_dump(testflinger_config, sort_keys=False))


def get_parser():
    parser = argparse.ArgumentParser(
        description="Generate testflinger configs for a host or set of hosts in a maas."
    )
    parser.add_argument(
        "maas_user",
        help="The maas user to configure the kvms for; should be logged in",
    )
    parser.add_argument(
        "subnet",
        help="The subnet that the static IP addresses for testflinger users are in.",
    )
    parser.add_argument(
        "output_dir",
        help="The output directory for the testflinger node configs",
    )
    parser.add_argument(
        "-m",
        "--machine_name",
        help="The name of the machine to generate a config for, if not set, any machine with a config in the output dir will be updated.",
        default=None,
    )
    return parser


def main(args):
    parser = get_parser()
    parsed_args = parser.parse_args(args)
    print("loading machine data...")
    machines = get_machines(parsed_args.maas_user, parsed_args.subnet)
    print("done")
    root_dir = Path(parsed_args.output_dir)
    root_dir.mkdir(parents=True, exist_ok=True)
    for hostname, machine in machines.items():
        if (
            parsed_args.machine_name is not None
            and parsed_args.machine_name == hostname
        ):
            print(f"writing configs for {hostname}")
            write_snappy_config(parsed_args.output_dir, hostname, machine)
            write_testflinger_config(parsed_args.output_dir, hostname, machine)
        elif (
            parsed_args.machine_name is None
            and root_dir.joinpath(Path(f"{hostname}.conf")).exists()
        ):
            print(f"writing configs for {hostname}")
            write_snappy_config(parsed_args.output_dir, hostname, machine)
            write_testflinger_config(parsed_args.output_dir, hostname, machine)


if __name__ == "__main__":
    main(sys.argv[1:])
