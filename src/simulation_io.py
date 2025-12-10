"""
Functions for handling simulation data I/O.

This module contains functions for extracting data from Abaqus ODB files
and other simulation output files.

Author: Eric Zhang (zhanghui@bfusa.com)
Date: Nov. 5, 2025
"""

import os
import json
import subprocess

import numpy as np

from src.utility import get_file_path


def extract_uamp_property(job_id_str, sim_type, config) -> np.ndarray:
    """
    Extracts slip ratio or slip angle from a uamp-properties.dat file.

    Args:
        job_id_str (str): The job ID used to locate the uamp-properties.dat file.
        sim_type (str): The type of simulation ('braking' or 'cornering').
        config (dict): The configuration dictionary.

    Returns:
        float: The extracted slip ratio or slip angle in degrees.
    """
    print("  --------------------------------------------------")
    print(f"  Extracting UAMP property for job ID: {job_id_str}")
    uamp_file_path_list = get_file_path(
        job_id_str,
        config,
        file_name_key="uamp_properties",
    )

    uamp_file_path = None
    keyword = config["paths"].get("solver_sub_folder_keyword", "").strip()
    if keyword:
        for path in uamp_file_path_list:
            if keyword in os.path.dirname(path):
                uamp_file_path = path
                break
    else:
        uamp_file_path = uamp_file_path_list[0]

    if not uamp_file_path:
        raise FileNotFoundError("No uamp-properties.dat file found.")

    print(f"    Reading UAMP properties from: {uamp_file_path}")

    uamp_keys = config["extraction_details"]["uamp_keys"][sim_type.lower()]
    # list of dictionary to hold extracted properties
    uamp_property_dict = dict()
    for key in uamp_keys:
        uamp_property_dict[key] = []

    with open(uamp_file_path, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        for key in uamp_keys:
            if key in line and i + 1 < len(lines):
                properties_line = lines[i + 1]
                parts = properties_line.split(",")
                if len(parts) > 1:
                    try:
                        value = float(parts[1].strip())
                        uamp_property_dict[key].append(value)
                        print(f"      Extracted {key}: {value}")
                    except ValueError:
                        raise ValueError(f"Could not convert value for {key} to float.")
                else:
                    raise ValueError(f"{key} found, but no properties line followed.")

    if sim_type.lower() == "braking":
        if "RIMSRY" not in uamp_property_dict:
            raise ValueError("RIMSRY not found in uamp-properties.dat for braking.")
        control_variables = np.array(uamp_property_dict["RIMSRY"])

    elif sim_type.lower() in {"cornering", "freerolling"}:
        if "ROADVX" not in uamp_property_dict or "ROADVY" not in uamp_property_dict:
            raise ValueError(
                f"ROADVX or ROADVY not found in uamp-properties.dat for {sim_type.lower()}."
            )
        vx = np.array(uamp_property_dict["ROADVX"])
        vy = np.array(uamp_property_dict["ROADVY"])
        control_variables = np.degrees(np.arctan2(vy, np.abs(vx)))
    else:
        raise ValueError(f"Unknown sim_type: {sim_type}")

    steps_selection = config["abaqus_settings"]["history_step_selection"][
        "sim_type_mapping"
    ].get(sim_type.lower())

    if steps_selection == "last":
        return control_variables[-1:]
    elif steps_selection == "first":
        return control_variables[:1]
    elif steps_selection == "all":
        return control_variables
    elif steps_selection == "all_but_first" and control_variables.size > 1:
        return control_variables[1:]
    else:
        raise UserWarning(
            "Invalid or insufficient steps for selection criteria: '{}'".format(
                steps_selection
            )
        )


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
    print("  --------------------------------------------------")
    print(f"  Executing Abaqus script for job ID: {job_id_str}")
    script_path = os.path.join(src_dir, "abaqus_script.py")
    output_path = os.path.join(output_dir, f"{sim_type}_{job_id_str}_data.json")
    temp_config_path = os.path.join(output_dir, f"temp_config_{job_id_str}.json")

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

    print(f"    Command: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("    Abaqus script executed successfully.")
        if result.stdout:
            print(f"    Stdout [below]:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"    [ERROR] Abaqus script failed with return code {e.returncode}")
        if e.stderr:
            print(f"    Stderr [below]:\n{e.stderr}")
        raise
    except FileNotFoundError:
        print(f"    [ERROR] The executable '{command[0]}' was not found.")
        raise
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)

    try:
        with open(output_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"  [ERROR] Output file not found at {output_path}.")
        raise
    except json.JSONDecodeError:
        print(f"  [ERROR] Could not decode JSON from file {output_path}.")
        raise
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

    return data
