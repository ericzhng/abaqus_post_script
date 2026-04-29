"""
This script is executed by the Abaqus Python interpreter to extract data from ODB files.

This script contains functions to handle Abaqus ODB files, including upgrading them
to the current version and extracting simulation data. It is designed to be called
from a standard Python environment, receiving its configuration via a JSON string.

Author: Eric Zhang (zhanghui@bfusa.com)
Date: Nov. 5, 2025
"""

import sys
import json
import argparse

from .common import unicode_to_str
from .extract_odb import extract_cleat_odb, extract_fm_odb

from .mylogger import get_logger

logger = get_logger()


def main():
    """
    Main execution function for the script.

    Parses command-line arguments, loads configuration from the JSON string,
    triggers the data extraction, and saves the results to a JSON file.
    """
    parser = argparse.ArgumentParser(description="Extract ODB data.")
    parser.add_argument("--job_id", required=True, help="Job ID")
    parser.add_argument("--sim_type", required=True, help="Simulation type")
    parser.add_argument("--output_path", required=True, help="Path to output JSON file")
    parser.add_argument(
        "--config_path", required=False, default=None, help="Path to config file"
    )
    parser.add_argument(
        "--debug", action="store_true", default=False, help="Enable debugger attachment"
    )
    args = parser.parse_args()

    if args.debug:
        import ptvsd

        ptvsd.enable_attach(address=("localhost", 5678))
        logger.info("Waiting for VS Code debugger to attach...")
        ptvsd.wait_for_attach()
        logger.info("Debugger attached!")

    config = None
    if args.config_path:
        with open(args.config_path, "r") as f:
            config = unicode_to_str(json.load(f))
    else:
        config = unicode_to_str(json.load(sys.stdin))

    if not config:
        logger.error("Failed to load configuration.")
        sys.exit(1)

    # Perform the data extraction.
    sim_type = args.sim_type.lower()
    if sim_type in ["braking", "cornering", "freerolling"]:
        output_data = extract_fm_odb(args.job_id, sim_type, config)
    elif "cleat" in sim_type:
        output_data = extract_cleat_odb(args.job_id, sim_type, config)
    else:
        raise ValueError("Unknown sim_type: {}".format(args.sim_type))

    with open(args.output_path, "w") as f:
        json.dump(output_data, f)


if __name__ == "__main__":
    main()
