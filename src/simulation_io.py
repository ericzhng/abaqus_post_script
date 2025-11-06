"""
Functions for handling simulation data I/O.

This module contains functions for extracting data from Abaqus ODB files
and other simulation output files.

Author: Eric Zhang (zhanghui@bfusa.com)
Date: Nov. 5, 2025
"""

import os
import sys
import glob
import math
import subprocess
import json


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

    solver_sub_folder = config["solver_sub_folder"].format(sim_type=sim_type.title())
    file_match_pattern = os.path.join(
        job_folder, job_id_str, solver_sub_folder, file_name
    )

    # Find files matching the pattern.
    file_path_list = glob.glob(file_match_pattern)

    if not file_path_list:
        raise FileNotFoundError(
            "No file found for pattern: {}".format(file_match_pattern)
        )
    return os.path.abspath(file_path_list[0])


def extract_uamp_property(job_id_str, sim_type, config):
    """
    Extracts slip ratio or slip angle from a uamp-properties.dat file.

    Args:
        job_id_str (str): The job ID used to locate the uamp-properties.dat file.
        sim_type (str): The type of simulation ('braking' or 'cornering').
        config (dict): The configuration dictionary.

    Returns:
        float: The extracted slip ratio (for braking) or slip angle in degrees (for cornering).
    """
    uamp_file_path = _get_file_path(
        job_id_str, sim_type, config, config["uamp_file_name"]
    )
    uamp_properties = {}
    uamp_keys = config["uamp_keys"][sim_type.lower()]

    with open(uamp_file_path, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        for key in uamp_keys:
            if key in line:
                if i + 1 < len(lines):
                    properties_line = lines[i + 1]
                    parts = properties_line.split(",")
                    if len(parts) > 1:
                        try:
                            uamp_properties[key] = float(parts[1].strip())
                        except ValueError:
                            raise ValueError(
                                f"Could not convert value for {key} to float."
                            )
                else:
                    raise ValueError(f"{key} found, but no properties line followed.")

    if sim_type.lower() == "braking":
        if "RIMSRY" not in uamp_properties:
            raise ValueError(
                "RIMSRY not found in uamp-properties.dat file for braking."
            )
        return uamp_properties["RIMSRY"]
    elif sim_type.lower() == "cornering":
        if "ROADVX" not in uamp_properties or "ROADVY" not in uamp_properties:
            raise ValueError(
                "ROADVX or ROADVY not found in uamp-properties.dat for cornering."
            )
        vx = uamp_properties["ROADVX"]
        vy = uamp_properties["ROADVY"]
        slip_angle = math.degrees(math.atan2(vy, abs(vx)))
        return slip_angle
    else:
        raise ValueError(f"Unknown sim_type: {sim_type}")


def extract_odb_result(src_dir, output_dir, job_id_str, str_type, config):
    """
    Extracts simulation data from an Abaqus ODB file by calling a separate script.
    """
    script_path = os.path.join(src_dir, "abaqus_script.py")
    output_path = os.path.join(output_dir, f"{str_type}_{job_id_str}_data.json")

    # abaqus solver path
    abaqus_solver_path = config["paths"]["abaqus_solver_path"]

    # Prepare config as JSON
    config_json = json.dumps(config)

    # save config_json to a temporary json file
    temp_config_path = os.path.join(output_dir, f"temp_config_{job_id_str}.json")
    with open(temp_config_path, "w") as f:
        f.write(config_json)

    # Build the command to run the Abaqus script
    command = [
        abaqus_solver_path,
        "python",
        script_path,
        "--job_id",
        job_id_str,
        "--sim_type",
        str_type,
        "--config_path",
        temp_config_path,
        "--output_path",
        output_path,
    ]

    try:
        # check=True: raises CalledProcessError on non-zero exit code
        # capture_output=True: captures stdout and stderr
        # text=True: decodes output as text (string)
        result = subprocess.run(
            command,
            input=config_json,
            check=True,
            capture_output=True,
            text=True,  # Decodes stdout/stderr as text
        )
        print("Command executed successfully.")
        print(f"Stdout: {result.stdout}")

    except subprocess.CalledProcessError as e:
        # 2. Catch the specific error raised by check=True
        print(f"ERROR: Command failed with return code {e.returncode}")
        print(f"Stderr: {e.stderr}")
    except FileNotFoundError:
        # 3. Catch errors where the command executable itself isn't found
        print(f"ERROR: The executable '{command[0]}' was not found.")
    except Exception as e:
        # Catch any other unexpected errors during execution
        print(f"An unexpected error occurred during subprocess execution: {e}")

    # Read the result file
    try:
        with open(output_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(
            f"Error: Output file not found at {output_path}. Abaqus script may have failed silently or in an unexpected way."
        )
        raise
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from file {output_path}.")
        raise

    # os.remove(output_path)
    return data
