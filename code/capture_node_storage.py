from os import path, listdir
import re
import yaml
import json
import logging
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


def read_node_info(maas_user, node_id):
    """subprocess placeholder"""
    cmd = ["maas", maas_user, "block-devices", "read", node_id]
    try:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
        )
    except subprocess.CalledProcessError:
        logger.error(f"error running: {' '.join(cmd)}")

    data = json.loads(proc.stdout.decode())

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
        logger.error(
            f"{error}\nUnable to write node initial disk config to agent!"
        )


def main():
    # Define a regex pattern for the desired filename
    pattern = re.compile(r'.+_snappy\.yaml$')

    # List all files in the './sut' directory and filter based on the pattern
    files = [
        f for f in listdir("./sut") if path.isfile(
            path.join("./sut", f)
        ) and pattern.match(f)
    ]

    for fname in files:
        fpath = path.join("./sut", fname)
        config = read_config_from_file(fpath)

        maas_user = config.get("maas_user")
        node_id = config.get("node_id")

        if not maas_user or not node_id:
            logger.error(
                "maas_user and/or node_id not in config %s", fname
            )
            continue

        logger.info("Capturing node storage layout for %s", fname)
        node_info = read_node_info(maas_user, node_id)
        device_list = capture_initial_config(node_info, config)
        write_devs_to_file(fpath, device_list)

        # log the updated default_disks configuration
        logger.info(
            "Updated config for %s::\ndefault_disks:\n%s\n",
            fname,
            yaml.dump(device_list["default_disks"]),
        )


if __name__ == "__main__":
    main()
