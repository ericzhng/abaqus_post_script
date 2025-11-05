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

from odbAccess import openOdb
from utility import upgrade_odb_if_necessary


def _get_file_path(job_id_str, sim_type, config, file_name):
    """
    Constructs the file path for a given simulation file.

    Args:
        job_id_str (str): The job ID.
        sim_type (str): The simulation type.
        config (dict): The configuration dictionary.
        file_name (str): The name of the file.

    Returns:
        str: The full path to the file.
    """
    platform = "win32" if "win32" in sys.platform.lower() else "linux"
    job_folder = config["job_folder"][platform]

    solver_sub_folder = config["solver_sub_folder"].format(sim_type=sim_type)
    file_match_pattern = os.path.join(
        job_folder, job_id_str, solver_sub_folder, file_name
    )
    file_path_list = glob.glob(file_match_pattern)

    if not file_path_list:
        raise FileNotFoundError(
            f"No file found for pattern: {file_match_pattern}"
        )
    return file_path_list[0]


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
    uamp_file_path = _get_file_path(job_id_str, sim_type, config, config["uamp_file_name"])
    uamp_properties = {}
    uamp_keys = config["uamp_keys"][sim_type]

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
                            raise ValueError(f"Could not convert value for {key} to float.")
                else:
                    raise ValueError(f"{key} found, but no properties line followed.")

    if sim_type == "braking":
        if "RIMSRY" not in uamp_properties:
            raise ValueError("RIMSRY not found in uamp-properties.dat file for braking.")
        return uamp_properties["RIMSRY"]
    elif sim_type == "cornering":
        if "ROADVX" not in uamp_properties or "ROADVY" not in uamp_properties:
            raise ValueError("ROADVX or ROADVY not found in uamp-properties.dat for cornering.")
        vx = uamp_properties["ROADVX"]
        vy = uamp_properties["ROADVY"]
        slip_angle = math.degrees(math.atan2(vy, vx))
        return slip_angle
    else:
        raise ValueError(f"Unknown sim_type: {sim_type}")


def extract_odb_data(job_id_str, str_type, config):
    """
    Extracts simulation data from an Abaqus ODB file.

    Args:
        job_id_str (str): The simulation job ID used to locate the ODB file.
        str_type (str): The type of simulation.
        config (dict): The configuration dictionary.

    Returns:
        tuple: A tuple containing the extracted data (RF3, RF1, IA, Coord3, Vx).
    """
    odb_file_path = _get_file_path(job_id_str, str_type, config, config["odb_file_name"])

    # Upgrade ODB file if necessary
    odb_file_path_upgraded = upgrade_odb_if_necessary(odb_file_path)

    print(f"  Open odb file: {odb_file_path_upgraded}")
    curr_odb = openOdb(odb_file_path_upgraded, readOnly=True)

    print("  extract steps in above odb file")
    for step_name, step in curr_odb.steps.items():
        print(f"extract {step_name} in odb file")

        try:
            history_road = step.historyRegions[config["history_regions"]["road"]]
            vx = history_road.historyOutputs[config["history_outputs"]["road"][0]].data[-1][1]
            vy = history_road.historyOutputs[config["history_outputs"]["road"][1]].data[-1][1]
            coord3 = history_road.historyOutputs[config["history_outputs"]["road"][2]].data[-1][1]
        except KeyError:
            raise UserWarning("Failed to extract V or COOR3 data from the ODB file.")

        try:
            history_road_handle = step.historyRegions[
                config["history_regions"]["road_handle"]
            ]
            rf1 = history_road_handle.historyOutputs[
                config["history_outputs"]["road_handle"][0]
            ].data[-1][1]
            rf3 = (
                history_road_handle.historyOutputs[
                    config["history_outputs"]["road_handle"][2]
                ].data[-1][1]
                * -1.0
            )
        except KeyError:
            raise UserWarning("Failed to extract RF data from the ODB file.")

        try:
            history_rim_handle = step.historyRegions[
                config["history_regions"]["rim_handle"]
            ]
            ia = round(
                history_rim_handle.historyOutputs[
                    config["history_outputs"]["rim_handle"][0]
                ].data[-1][1]
                * 180
                / math.pi,
                1,
            )
        except KeyError:
            raise UserWarning("Failed to extract UR1 data from the ODB file.")

        if rf3 is not None and rf3 < 1000:
            print(
                f"  RF3 is too small (RF3 = {rf3:.2f} N). Please check the simulation."
            )

    return rf3, rf1, ia, coord3, vx
