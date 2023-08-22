import os
import re
import yaml
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def check_and_add_queues(yaml_file):
    with open(yaml_file, "r") as f:
        data = yaml.safe_load(f)

    default_disks = data.get("default_disks", [])

    # Extract disk and partition sizes
    sizes = [
        int(entry.get("size", 0))
        for entry in default_disks
        if entry["type"] in ["disk", "partition"]
    ]

    # Check conditions
    charmed_ceph = any(size >= 250e9 for size in sizes)

    large_disks = sum(1 for size in sizes if size >= 200e9)
    micro_ceph = large_disks >= 2

    # Update the corresponding .conf file
    conf_file = os.path.join(
        os.path.dirname(yaml_file),
        os.path.basename(yaml_file).replace("_snappy.yaml", ".conf"),
    )
    if os.path.exists(conf_file):
        with open(conf_file, "r") as f:
            conf_data = yaml.safe_load(f)

        queues = conf_data.get("job_queues", [])

        if charmed_ceph and "charmed-ceph" not in queues:
            queues.append("charmed-ceph")
        if micro_ceph and "micro-ceph" not in queues:
            queues.append("micro-ceph")

        conf_data["job_queues"] = queues
        with open(conf_file, "w") as f:
            yaml.dump(conf_data, f)
        logger.info(f"Updated queues for {conf_file}")
    else:
        logger.error(f"{conf_file} not found!")


def main():
    # Define a regex pattern for the desired filename
    pattern = re.compile(r".+_snappy\.yaml$")

    files = [
        f
        for f in os.listdir("./sut")
        if os.path.isfile(os.path.join("./sut", f)) and pattern.match(f)
    ]
    for fname in files:
        check_and_add_queues(os.path.join("./sut", fname))


if __name__ == "__main__":
    main()
