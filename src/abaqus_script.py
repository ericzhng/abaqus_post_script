from __future__ import print_function

"""
This script is executed by the Abaqus Python interpreter to extract data from ODB files.

This script contains functions to handle Abaqus ODB files, including upgrading them
to the current version and extracting simulation data. It is designed to be called
from a standard Python environment, receiving its configuration via a JSON string.

Author: Eric Zhang (zhanghui@bfusa.com)
Date: Nov. 5, 2025
"""

import os
import sys
import glob
import math
import json
import argparse
import subprocess
from odbAccess import openOdb, isUpgradeRequiredForOdb


def convert_unicode_to_str(data):
    """
    Recursively converts dictionary keys and string values from unicode to str
    in a Python 2.7 environment.
    """
    if isinstance(data, dict):
        return {
            convert_unicode_to_str(k): convert_unicode_to_str(v)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [convert_unicode_to_str(i) for i in data]
    elif isinstance(data, unicode):
        return data.encode("utf-8")
    else:
        return data


def _get_file_path(job_id_str, sim_type, config, file_name_key):
    """
    Constructs the file path for a given simulation file based on configuration.

    This helper function builds a file path pattern using the job ID, simulation
    type, and configuration details, then searches for a matching file.

    Args:
        job_id_str (str): The job ID.
        sim_type (str): The simulation type (e.g., 'Braking', 'Cornering').
        config (dict): A dictionary containing configuration parameters.
        file_name_key (str): The key for the file name in the config.

    Returns:
        str: The absolute path to the located file.

    Raises:
        IOError: If no file matching the constructed pattern is found.
    """
    platform = "win32" if "win32" in sys.platform.lower() else "linux"
    job_folder = config["paths"]["job_folder"][platform]
    file_name = config["paths"]["file_names"][file_name_key]

    solver_sub_folder = config["paths"]["solver_sub_folder_pattern"].format(
        sim_type=sim_type.title()
    )
    file_match_pattern = os.path.join(
        job_folder, job_id_str, solver_sub_folder, file_name
    )

    file_path_list = glob.glob(file_match_pattern)

    if not file_path_list:
        raise IOError("No file found for pattern: {}".format(file_match_pattern))
    return os.path.abspath(file_path_list[0])


def _upgrade_odb_if_needed(odb_file_name):
    """
    Upgrades an Abaqus ODB file to the current version if outdated.

    This function checks if the specified ODB file requires an upgrade to be
    compatible with the current Abaqus version. If an upgrade is needed, it
    runs the Abaqus upgrade utility. An upgraded file with the `_upgraded`
    suffix is created.
    """
    odb_base, _ = os.path.splitext(odb_file_name)
    upgraded_odb_file_name = odb_base + "_upgraded.odb"

    if isUpgradeRequiredForOdb(upgradeRequiredOdbPath=odb_file_name):
        # If the upgraded file doesn't already exist, run the upgrade utility.
        if not os.path.exists(upgraded_odb_file_name):
            print("  Upgrading ODB file...")
            command = [
                "abaqus",
                "-upgrade",
                "-job",
                odb_base + "_upgraded",
                "-odb",
                odb_file_name,
            ]
            result = subprocess.call(command)
            if result != 0:
                raise RuntimeError("ODB upgrade failed.")
            else:
                print("  ODB upgrade successful.")
        else:
            print("  Upgraded ODB file already exists.")
        return upgraded_odb_file_name
    else:
        print("  ODB file does not require an upgrade.")
        return odb_file_name


def extract_odb_data(job_id_str, sim_type, config):
    """
    Extracts specified simulation data from an Abaqus ODB file.

    This function orchestrates the process of finding the ODB file, upgrading it
    if necessary, and then extracting key data points (forces, coordinates, etc.)
    based on the provided configuration.
    """
    odb_file_path = _get_file_path(job_id_str, sim_type, config, "odb_main")

    # load abaqus settings from config
    abaqus_settings = config["abaqus_settings"]

    # Ensure the ODB file is compatible with the current Abaqus version.
    odb_file_path_upgraded = _upgrade_odb_if_needed(odb_file_path)

    print("  Open odb file: {}".format(odb_file_path_upgraded))
    curr_odb = openOdb(odb_file_path_upgraded, readOnly=True)

    extracted_data = {"step_name": []}
    for outputs_list in abaqus_settings["history_outputs"].values():
        for output_name in outputs_list:
            extracted_data[output_name] = []

    steps_selection = abaqus_settings["history_step_selection"]["sim_type_mapping"].get(
        sim_type.lower()
    )
    all_step_names = list(curr_odb.steps.keys())
    steps_to_process = []

    if steps_selection == "last":
        steps_to_process.append(all_step_names[-1])
    elif steps_selection == "first":
        steps_to_process = all_step_names[:1]
    elif steps_selection == "all":
        steps_to_process = all_step_names
    elif steps_selection == "all_but_first" and len(all_step_names) > 1:
        steps_to_process = all_step_names[1:]
    else:
        raise UserWarning("Invalid or insufficient steps for selection criteria.")

    print("  Extract data from steps: {}".format(", ".join(steps_to_process)))

    # Iterate through selected steps in the ODB file.
    for step_name in steps_to_process:
        print("  - extracting {}:".format(step_name))
        step = curr_odb.steps[step_name]
        current_step_values = {}

        try:
            # Iterate through each region defined in history_outputs
            for region_key, outputs_list in abaqus_settings["history_outputs"].items():
                history_region_name = abaqus_settings["history_regions"].get(region_key)
                if not history_region_name:
                    raise KeyError("History region '{}' not found".format(region_key))

                history_region = step.historyRegions[history_region_name]
                for output_name in outputs_list:
                    # last increment value, leaving out the increment time
                    value = history_region.historyOutputs[output_name].data[-1][1]
                    # Apply specific transformations based on output name
                    if output_name == "RF3":
                        value *= -1.0
                    elif output_name == "UR1":
                        value = round(value * 180 / math.pi, 1)
                    current_step_values[output_name] = value

            # Sanity check for RF3 if it was extracted correctly
            if current_step_values.get("RF3", float("inf")) < 1000:
                print(
                    "  RF3 is too small (RF3 = {:.2f} N). Please check simulation.".format(
                        current_step_values["RF3"]
                    )
                )

            # Append successfully extracted step to extracted_data dictionary
            extracted_data["step_name"].append(step_name)
            for key, value in current_step_values.items():
                extracted_data[key].append(value)

        except (KeyError, UserWarning) as e:
            print("  Skipping step {} due to error: {}".format(step_name, e))
            continue

    print("  End of data extraction.")
    return extracted_data


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
    args = parser.parse_args()

    config = None
    if args.config_path:
        with open(args.config_path, "r") as f:
            config = convert_unicode_to_str(json.load(f))
    else:
        config = convert_unicode_to_str(json.load(sys.stdin))

    if not config:
        print("ERROR: Failed to load configuration.")
        sys.exit(1)

    # Perform the data extraction.
    output_data = extract_odb_data(args.job_id, args.sim_type, config)

    with open(args.output_path, "w") as f:
        json.dump(output_data, f)


if __name__ == "__main__":
    main()
