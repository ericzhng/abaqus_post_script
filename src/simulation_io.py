"""
Functions for handling simulation data I/O.

This module contains functions for extracting data from Abaqus ODB files
and other simulation output files.

Author: Eric Zhang (zhanghui@bfusa.com)
Date: Nov. 5, 2025
"""

import os
import math
import subprocess
import json

from src.utility import get_file_path


def extract_uamp_property(job_id_str, sim_type, config):
    """
    Extracts slip ratio or slip angle from a uamp-properties.dat file.

    Args:
        job_id_str (str): The job ID used to locate the uamp-properties.dat file.
        sim_type (str): The type of simulation ('braking' or 'cornering').
        config (dict): The configuration dictionary.

    Returns:
        float: The extracted slip ratio or slip angle in degrees.
    """
    uamp_file_path = get_file_path(
        job_id_str,
        sim_type,
        config,
        file_name_key="uamp_properties",
    )
    uamp_properties = {}
    uamp_keys = config["extraction_details"]["uamp_keys"][sim_type.lower()]

    with open(uamp_file_path, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        for key in uamp_keys:
            if key in line and i + 1 < len(lines):
                properties_line = lines[i + 1]
                parts = properties_line.split(",")
                if len(parts) > 1:
                    try:
                        uamp_properties[key] = float(parts[1].strip())
                    except ValueError:
                        raise ValueError(f"Could not convert value for {key} to float.")
                else:
                    raise ValueError(f"{key} found, but no properties line followed.")

    sim_type_lower = sim_type.lower()
    if sim_type_lower == "braking":
        if "RIMSRY" not in uamp_properties:
            raise ValueError("RIMSRY not found in uamp-properties.dat for braking.")
        return uamp_properties["RIMSRY"]
    elif sim_type_lower == "cornering":
        if "ROADVX" not in uamp_properties or "ROADVY" not in uamp_properties:
            raise ValueError(
                "ROADVX or ROADVY not found in uamp-properties.dat for cornering."
            )
        vx = uamp_properties["ROADVX"]
        vy = uamp_properties["ROADVY"]
        return math.degrees(math.atan2(vy, abs(vx)))
    else:
        raise ValueError(f"Unknown sim_type: {sim_type}")


def extract_odb_result(src_dir, output_dir, job_id_str, sim_type, config):
    """
    Extracts simulation data from an Abaqus ODB file by calling a separate script.

    This function constructs a command to execute the Abaqus Python script, passing
    the necessary parameters and configuration. It captures the output and returns
    the extracted data as a dictionary.

    Args:
        src_dir (str): The directory containing the Abaqus script.
        output_dir (str): The directory to save temporary and output files.
        job_id_str (str): The job ID.
        sim_type (str): The simulation type.
        config (dict): The configuration dictionary.

    Returns:
        dict: The data extracted from the ODB file.
    """
    script_path = os.path.join(src_dir, "abaqus_script.py")
    output_path = os.path.join(output_dir, f"{sim_type}_{job_id_str}_data.json")
    temp_config_path = os.path.join(output_dir, f"temp_config_{job_id_str}.json")

    # Save config to a temporary JSON file to be passed to the Abaqus script
    with open(temp_config_path, "w") as f:
        json.dump(config, f)

    command = [
        config["paths"]["abaqus_solver_path"],
        "python",
        script_path,
        "--job_id",
        job_id_str,
        "--sim_type",
        sim_type,
        "--config_path",
        temp_config_path,
        "--output_path",
        output_path,
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("Abaqus script executed successfully.")
        print(f"Stdout: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Abaqus script failed with return code {e.returncode}")
        print(f"Stderr: {e.stderr}")
        raise
    except FileNotFoundError:
        print(f"ERROR: The executable '{command[0]}' was not found.")
        raise
    finally:
        # Clean up the temporary config file
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)

    # Read the result file from the Abaqus script
    try:
        with open(output_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Output file not found at {output_path}.")
        raise
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from file {output_path}.")
        raise
    finally:
        # Clean up the output file
        if os.path.exists(output_path):
            os.remove(output_path)

    return data
