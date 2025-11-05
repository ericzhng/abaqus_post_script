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


def _get_file_path(job_id_str, sim_type, config, file_name):
    """
    Constructs the file path for a given simulation file based on configuration.

    This helper function builds a file path pattern using the job ID, simulation
    type, and configuration details, then searches for a matching file.

    Args:
        job_id_str (str): The job ID.
        sim_type (str): The simulation type (e.g., 'Braking', 'Cornering').
        config (dict): A dictionary containing configuration parameters like
                       'job_folder' and 'solver_sub_folder'.
        file_name (str): The name of the file to locate.

    Returns:
        str: The absolute path to the located file.

    Raises:
        IOError: If no file matching the constructed pattern is found.
    """
    platform = "win32" if "win32" in sys.platform.lower() else "linux"
    job_folder = config["job_folder"][platform]

    solver_sub_folder = config["solver_sub_folder"].format(sim_type=sim_type)
    file_match_pattern = os.path.join(
        job_folder, job_id_str, solver_sub_folder, file_name
    )

    # Find files matching the pattern.
    file_path_list = glob.glob(file_match_pattern)

    if not file_path_list:
        raise IOError(
            "No file found for pattern: {}".format(file_match_pattern)
        )
    return os.path.abspath(file_path_list[0])


def _upgrade_odb_if_necessary(odb_file_name):
    """
    Upgrades an Abaqus ODB file to the current version if it's outdated.

    This function checks if the specified ODB file requires an upgrade to be
    compatible with the current Abaqus version. If an upgrade is needed, it
    runs the Abaqus upgrade utility. An upgraded file with the `_upgraded`
    suffix is created.

    Args:
        odb_file_name (str): The absolute path to the ODB file.

    Returns:
        str: The path to the (potentially) upgraded ODB file. If no upgrade
             was needed, the original file path is returned.

    Raises:
        RuntimeError: If the ODB upgrade process fails.
    """
    odb_base, _ = os.path.splitext(odb_file_name)
    upgraded_odb_file_name = odb_base + "_upgraded.odb"

    # Check if the ODB file needs to be upgraded.
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
            # Execute the Abaqus upgrade command.
            result = subprocess.call(command)
            if result != 0:
                print("  ODB upgrade failed with error:")
                raise RuntimeError("ODB upgrade failed.")
            else:
                print("  ODB upgrade successful.")
        else:
            print("  Upgraded ODB file already exists.")
        return upgraded_odb_file_name
    else:
        print("  ODB file does not require an upgrade.")
        return odb_file_name


def extract_odb_data(job_id_str, str_type, config):
    """
    Extracts specified simulation data from an Abaqus ODB file.

    This function orchestrates the process of finding the ODB file, upgrading it
    if necessary, and then extracting key data points (forces, coordinates, etc.)
    based on the provided configuration.

    Args:
        job_id_str (str): The simulation job ID.
        str_type (str): The type of simulation (e.g., 'Braking', 'Cornering').
        config (dict): A dictionary with configuration for file paths and
                       the names of history regions/outputs to be extracted.

    Returns:
        dict: A dictionary where keys are the output variable names (e.g., 'RF3', 'V1')
              and values are lists of extracted data for each processed step.

    Raises:
        UserWarning: If expected data keys are not found in the ODB file.
    """
    odb_file_path = _get_file_path(
        job_id_str, str_type, config, config["odb_file_name"]
    )

    # Ensure the ODB file is compatible with the current Abaqus version.
    odb_file_path_upgraded = _upgrade_odb_if_necessary(odb_file_path)

    print("  Open odb file: {}".format(odb_file_path_upgraded))
    curr_odb = openOdb(odb_file_path_upgraded, readOnly=True)

    # Initialize a dictionary of lists for all expected output variables
    extracted_data = {}
    extracted_data['step_name'] = []  # Add step_name list
    for region_key, outputs_list in config["history_outputs"].items():
        for output_name in outputs_list:
            extracted_data[output_name] = []

    # Determine which steps to process based on 'use_option'
    use_option = config["use_option"][str_type.lower()]
    all_step_names = list(curr_odb.steps.keys())
    steps_to_process = []

    if use_option == "last":
        if all_step_names:
            steps_to_process.append(all_step_names[-1])
    elif use_option == "all":
        steps_to_process = all_step_names
    elif use_option == "all_not_first":
        if len(all_step_names) > 1:
            steps_to_process = all_step_names[1:]
        else:
            raise UserWarning("Not enough steps to exclude the first one.")
    else:
        raise UserWarning("Invalid use_option specified in config: {}".format(use_option))

    print("  Extract data from steps: {}".format(", ".join(steps_to_process)))

    # Iterate through selected steps in the ODB file.
    for step_name in steps_to_process:
        print("  - extracting {}:".format(step_name))
        step = curr_odb.steps[step_name]

        current_step_values = {}
        try:
            # Iterate through each region defined in history_outputs
            for region_key, outputs_list in config["history_outputs"].items():
                history_region_name = config["history_regions"].get(region_key)
                if not history_region_name:
                    raise KeyError(
                        "History region '{}' not found in config['history_regions']".format(region_key)
                    )

                history_region = step.historyRegions[history_region_name]

                for output_name in outputs_list:
                    # last increment value, leaving out the increment time
                    value = history_region.historyOutputs[output_name].data[-1][1]

                    # Apply specific transformations based on output name
                    if output_name == "RF3":
                        value *= -1.0  # Invert the sign of RF3
                    elif output_name == "UR1":
                        value = round(value * 180 / math.pi, 1)  # Convert radians to degrees

                    current_step_values[output_name] = value

            # Sanity check for RF3 if it was extracted correctly
            if "RF3" in current_step_values and current_step_values["RF3"] is not None and current_step_values["RF3"] < 1000:
                print("  RF3 is too small (RF3 = {:.2f} N). Please check the simulation.".format(current_step_values["RF3"]))

            # Append successfully extracted data for this step to the main extracted_data dictionary
            extracted_data['step_name'].append(step_name)  # Record the step name
            for key, value in current_step_values.items():
                extracted_data[key].append(value)

        except KeyError as e:
            print("  Skipping step {} due to missing data: {}".format(step_name, e))
            continue  # Skip this step if data extraction fails
        except UserWarning as e:
            print("  Skipping step {} due to warning: {}".format(step_name, e))
            continue  # Skip this step if a UserWarning occurs
        except Exception as e:
            print("  Skipping step {} due to unexpected error: {}".format(step_name, e))
            continue  # Catch any other unexpected errors
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
    parser.add_argument("--config_json", required=True, help="Config as JSON string")
    args = parser.parse_args()

    # Load configuration from the JSON string passed as an argument.
    config = json.loads(args.config_json)

    # Perform the data extraction.
    output_data = extract_odb_data(args.job_id, args.sim_type, config)

    # Write the extracted data to the specified output file.
    with open(args.output_path, 'w') as f:
        json.dump(output_data, f)


if __name__ == "__main__":
    main()