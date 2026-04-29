"""
Functions for handling simulation data I/O.

This module contains functions for extracting data from Abaqus ODB files
and other simulation output files.

Author: Eric Zhang (zhanghui@bfusa.com)
Date: Nov. 5, 2025
"""

import os
import sys
import json
import subprocess

import numpy as np

from .abaqus_post.common import get_file_path
from .abaqus_post.mylogger import get_logger

logger = get_logger()


def _get_uamp_file_path(job_id_str, sim_type, config):
    """Finds the main ODB file path based on job ID and simulation type."""
    try:
        paths = get_file_path(job_id_str, config, file_name_key="uamp_properties")
    except IOError as e:
        logger.error(str(e))
        return None

    keyword = config["paths"]["solver_sub_folder_keyword"][sim_type].strip()
    if not keyword:
        return paths[0]

    match = next((p for p in paths if keyword in os.path.dirname(p)), None)
    if match:
        return match

    logger.error("No uamp-properties.dat file found.")
    return None


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
    logger.info("  --------------------------------------------------")
    logger.info(f"  Extracting UAMP property for job ID: {job_id_str}")

    uamp_file_path = _get_uamp_file_path(job_id_str, sim_type, config)
    if not uamp_file_path:
        error_msg = "uamp-properties.dat file not found for job ID: {}".format(
            job_id_str
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # list of dictionary to hold extracted properties
    uamp_property_dict = dict()
    uamp_keys = config["extraction_details"]["uamp_keys"][sim_type]
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
                        logger.info(f"      Extracted {key}: {value}")
                    except ValueError:
                        error_msg = f"Could not convert value for {key} to float."
                        logger.error(error_msg)
                        raise ValueError(error_msg)
                else:
                    error_msg = f"{key} found, but no properties line followed."
                    logger.error(error_msg)
                    raise ValueError(error_msg)

    if sim_type == "braking":
        if "RIMSRY" not in uamp_property_dict:
            error_msg = "RIMSRY not found in uamp-properties.dat for braking."
            logger.error(error_msg)
            raise ValueError(error_msg)
        control_variables = np.array(uamp_property_dict["RIMSRY"])

    elif sim_type in {"cornering", "freerolling"}:
        if "ROADVX" not in uamp_property_dict or "ROADVY" not in uamp_property_dict:
            error_msg = (
                f"ROADVX or ROADVY not found in uamp-properties.dat for {sim_type}."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        vx = np.array(uamp_property_dict["ROADVX"])
        vy = np.array(uamp_property_dict["ROADVY"])
        control_variables = np.degrees(np.arctan2(vy, np.abs(vx)))

    else:
        error_msg = f"Unknown sim_type: {sim_type}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    steps_selection = config["abaqus_settings"]["history_step_selection"][
        "sim_type_mapping"
    ].get(sim_type)

    if steps_selection == "last":
        return control_variables[-1:]
    elif steps_selection == "first":
        return control_variables[:1]
    elif steps_selection == "all":
        return control_variables
    elif steps_selection == "all_but_first" and control_variables.size > 1:
        return control_variables[1:]
    else:
        warning_msg = (
            "Invalid or insufficient steps for selection criteria: '{}'".format(
                steps_selection
            )
        )
        logger.warning(warning_msg)
        raise UserWarning(warning_msg)


def run_abaqus_post(src_dir, output_dir, job_id_str, sim_type, config):
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
    logger.info("  --------------------------------------------------")
    logger.info(f"  Executing Abaqus script for job ID: {job_id_str}")
    script_path = os.path.join(src_dir, "abaqus_post", "run_abaqus_post.py")
    output_path = os.path.join(output_dir, f"{sim_type}_{job_id_str}_data.json")
    temp_config_path = os.path.join(output_dir, f"temp_config_{job_id_str}.json")

    with open(temp_config_path, "w") as f:
        json.dump(config, f)

    platform = "win32" if "win32" in sys.platform.lower() else "linux"
    command = [
        config["paths"]["abaqus_solver_path"][platform],
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

    logger.info(f"    Command: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        logger.info("    Abaqus script executed successfully.")
        if result.stdout:
            logger.info(f"    Stdout [below]:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"    Abaqus script failed with return code {e.returncode}")
        if e.stderr:
            logger.error(f"    Stderr [below]:\n{e.stderr}")
        raise
    except FileNotFoundError:
        logger.error(f"    The executable '{command[0]}' was not found.")
        raise
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)

    try:
        with open(output_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"  Output file not found at {output_path}.")
        raise
    except json.JSONDecodeError:
        logger.error(f"  Could not decode JSON from file {output_path}.")
        raise
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

    return data
