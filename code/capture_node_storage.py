from os import path, listdir
import re
import yaml
import json
import logging
import argparse
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/var/log/default_disk"),
        logging.StreamHandler()
    ],
)
logger = logging.getLogger(__name__)


def gen_disk_cfg(dev):
    return {
        "id": str(dev["id"]),
        "parent_disk_blkid": str(dev["id"]),
        "name": dev["name"],
        "ptable": dev["partition_table_type"],
        "type": "disk",
    }


def gen_partn_cfg(partition):
    return {
        "id": partition["path"].split("/")[-1],
        "parent_disk": str(partition["device_id"]),
        "parent_disk_blkid": str(partition["device_id"]),
        "device": str(partition["id"]),
        "number": str(partition["id"]),
        "size": str(partition["size"]),
        "type": "partition",
    }


def gen_frmt_mnt_cfg(partition):
    format_id = f"{partition['id']}-format"
    mount_id = f"{partition['id']}-mount"

    format_device = {
        "id": format_id,
        "parent_disk": str(partition["device_id"]),
        "parent_disk_blkid": str(partition["device_id"]),
        "volume": str(partition["id"]),
        "fstype": partition["filesystem"]["fstype"],
        "label": partition["filesystem"]["label"],
        "type": "format",
    }

    mount_device = {
        "id": mount_id,
        "parent_disk": str(partition["device_id"]),
        "parent_disk_blkid": str(partition["device_id"]),
        "device": format_id,
        "path": partition["filesystem"]["mount_point"],
        "type": "mount",
    }
    return format_device, mount_device


def capture_initial_config(node_info, config):
    config["default_disks"] = []

    for dev in node_info:
        config["default_disks"].append(gen_disk_cfg(dev))

        for partn in dev.get("partitions", []):
            config["default_disks"].append(gen_partn_cfg(partn))

            if partn.get("filesystem"):
                format_dev, mount_dev = gen_frmt_mnt_cfg(partn)
                config["default_disks"].extend([format_dev, mount_dev])

    return config


def run_command(cmd):
    """Execute the given command and return the output."""
    try:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
        )
        return proc.stdout.decode().strip()
    except subprocess.CalledProcessError:
        logger.error(f"error running: {' '.join(cmd)}")
        return ""


def parse_json_output(output, node_id, cmd):
    """Parse the JSON output from the command."""
    if not output:
        logger.error(
            f"No output for node_id: {node_id}. Command: {' '.join(cmd)}"
        )
        return {}

    try:
        data = json.loads(output)
        return data
    except json.JSONDecodeError:
        logger.error(
            f"Invalid JSON for node_id: {node_id}. Command: {' '.join(cmd)}"
        )
        return {}


def read_node_info(maas_user, node_id):
    """subprocess placeholder."""
    cmd = ["maas", maas_user, "block-devices", "read", node_id]
    output = run_command(cmd)
    data = parse_json_output(output, node_id, cmd)
    return data


def read_config_from_file(path):
    try:
        with open(path, "r") as file:
            data = yaml.safe_load(file)
    except OSError as error:
        logger.error(f"{error}\nUnable to read device agent config!")

    return data


def write_devs_to_file(path, device_list):
    try:
        with open(path, "w") as config_file:
            yaml.dump(device_list, config_file)
    except OSError as error:
        logger.error(f"{error}\nUnable to write node disk config to agent")


def clear_default_disks(filename):
    """Remove the default_disks key from the config file."""
    with open(filename, "r") as f:
        data = yaml.safe_load(f)

    # Remove the default_disks key
    data.pop("default_disks", None)

    with open(filename, "w") as f:
        yaml.dump(data, f)


def file_needs_processing(filename):
    """Check if the config file doesn't have a default_disks key."""
    with open(filename, "r") as f:
        data = yaml.safe_load(f)
    return "default_disks" not in data


def process_file(fpath):
    """Process a given config file."""
    config = read_config_from_file(fpath)

    maas_user = config.get("maas_user")
    node_id = config.get("node_id")

    if not maas_user or not node_id:
        logger.error(f"maas_user and/or node_id not in config {fpath}")
        return

    logger.info(f"Capturing node storage layout for {fpath}")
    node_info = read_node_info(maas_user, node_id)
    device_list = capture_initial_config(node_info, config)

    if not device_list.get("default_disks"):
        logger.error(
            f"default_disks is empty for file {fpath}. Skipping write."
        )
        return

    write_devs_to_file(fpath, device_list)

    # log the updated default_disks configuration
    logger.info(
        f"Updated config for {fpath}::\ndefault_disks:\n"
        f"{yaml.dump(device_list['default_disks'])}\n"
    )


def main():
    # Define a regex pattern for the desired filename
    pattern = re.compile(r".+_snappy\.yaml$")

    parser = argparse.ArgumentParser(
        description="Process and clear config files."
    )
    parser.add_argument(
        "--process", help="Process a config file", type=str
    )
    parser.add_argument(
        "--clear",
        help="Clear the default_disks key from a specific config file",
        type=str,
    )
    parser.add_argument(
        "--clear-all",
        help="Clear the default_disks key from all config files",
        action="store_true",
    )
    parser.add_argument(
        "--process-all",
        help="Process all files without a default_disks key",
        action="store_true",
    )

    args = parser.parse_args()

    if args.process:
        if file_needs_processing(args.process):
            # Process the specified file
            process_file(args.process)
    elif args.clear:
        # Clear default_disks from the specified file
        clear_default_disks(args.clear)
    elif args.clear_all:
        # Clear default_disks from all config files
        files = [
            f
            for f in listdir("./sut")
            if path.isfile(path.join("./sut", f)) and pattern.match(f)
        ]
        for fname in files:
            clear_default_disks(path.join("./sut", fname))
    elif args.process_all or not (
        args.process or args.clear or args.clear_all
    ):
        # Process all config files without a default_disks key
        files = [
            f
            for f in listdir("./sut")
            if path.isfile(path.join("./sut", f))
            and pattern.match(f)
            and file_needs_processing(path.join("./sut", f))
        ]
        for fname in files:
            process_file(path.join("./sut", fname))


if __name__ == "__main__":
    main()
