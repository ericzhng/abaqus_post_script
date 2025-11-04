"""
Extracts force and moment data from Abaqus ODB files for braking simulations.

This script is designed to be run in the Abaqus Python environment to post-process
simulation results. It extracts reaction forces, coordinates, and velocities from
ODB files, processes the data, and saves it to a CSV file.

Author: Eric Zhang (zhanghui@bfusa.com)
Date: Nov. 4, 2025

Example Usage:
    /app/abaqusnet/Commands/abq2023hf3 python extract_braking_data.py -i "[<list_of_ids>]"

Example:
    /app/abaqusnet/Commands/abq2023hf3 python extract_braking_data.py -i "[142872, 142879:142894]"
"""

import os
import sys
import glob
import math
import argparse

from odbAccess import openOdb, isUpgradeRequiredForOdb


def generate_range_list(start, end):
    """
    Generates a list of integers from a starting value to an ending value.

    This function creates a list of all integers from `start` to `end`,
    inclusive. It handles both ascending (e.g., 1 to 5) and descending
    (e.g., 5 to 1) ranges.

    Args:
        start (int): The starting integer of the range.
        end (int): The ending integer of the range.

    Returns:
        list: A list of integers from `start` to `end`.
    """
    if start <= end:
        return list(range(start, end + 1))
    else:
        return list(range(start, end - 1, -1))


def parse_matlab_style_input(input_str):
    """
    Parses a MATLAB-style string (e.g., '[a, b:c, d]') into a list of integers.

    Args:
        input_str (str): The input string to parse.

    Returns:
        list: A list of integers.

    Raises:
        ValueError: If the input string is malformed.
    """
    cleaned_str = input_str.strip().strip("[]")
    elements = [e.strip() for e in cleaned_str.split(",") if e.strip()]

    if not elements:
        raise ValueError("Input string is empty or contains only brackets/commas.")

    combined_list = []
    for element in elements:
        try:
            if ":" in element:
                range_parts = element.split(":")
                if len(range_parts) != 2:
                    raise ValueError(
                        f"Range part '{element}' must contain exactly one colon."
                    )
                b = int(range_parts[0].strip())
                c = int(range_parts[1].strip())
                combined_list.extend(generate_range_list(b, c))
            else:
                a = int(element)
                combined_list.append(a)
        except ValueError:
            raise ValueError(
                f"Invalid integer format in element '{element}'. "
                "All numbers must be valid integers."
            )
    return combined_list


def parse_and_process_arguments():
    """
    Sets up the command-line parser and processes user input.

    Returns:
        list: A unique, sorted list of integers from the input string.
    """
    parser = argparse.ArgumentParser(
        description="A CLI tool that processes a MATLAB-style input string to generate a list of integers.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help='Input string in MATLAB-style format: "[a, b:c, d:e, f]".\n    Supports single integers and inclusive ranges (b:c).',
    )
    args = parser.parse_args()
    input_str = args.input

    try:
        result_list = parse_matlab_style_input(input_str)
        unique_list = list(set(result_list))
        return unique_list
    except ValueError as e:
        print(f"\nError processing input: {e}\n")
        sys.exit(1)


def upgrade_odb_if_necessary(odb_file_name):
    """
    Upgrades an Abaqus ODB file to the current version if necessary.

    Args:
        odb_file_name (str): The path to the ODB file.

    Returns:
        str: The path to the upgraded ODB file.
    """
    odb_base, _ = os.path.splitext(odb_file_name)
    upgraded_odb_file_name = odb_base + "_upgraded.odb"

    if isUpgradeRequiredForOdb(upgradeRequiredOdbPath=odb_file_name):
        if not os.path.exists(upgraded_odb_file_name):
            print(" -- Upgrading ODB file...")
            command = [
                "abaqus",
                "-upgrade",
                "-job",
                odb_base + "_upgraded",
                "-odb",
                odb_file_name,
            ]
            import subprocess
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                print(f" -- ODB upgrade failed with error:\n{result.stderr}")
                raise RuntimeError("ODB upgrade failed.")
            else:
                print(" -- ODB upgrade successful.")
        else:
            print(" -- Upgraded ODB file already exists.")
        return upgraded_odb_file_name
    else:
        print(" -- ODB file does not require an upgrade.")
        return odb_file_name


def sort_lists_by_first(list1, *argv):
    """
    Sorts multiple lists based on the sorting order of the first list.

    Args:
        list1 (list): The primary list to sort by.
        *argv (list): Additional lists to sort in conjunction with list1.

    Returns:
        list: A list of sorted lists.
    """
    zipped_lists = zip(list1, *argv)
    sorted_zipped_lists = sorted(zipped_lists, key=lambda x: x[0])
    sorted_lists = [list(t) for t in zip(*sorted_zipped_lists)]
    return sorted_lists


def extract_odb_data(brake_id_str):
    """
    Extracts simulation data from an Abaqus ODB file.

    Args:
        brake_id_str (str): The braking job ID used to locate the ODB file.

    Returns:
        tuple: A tuple containing the extracted data (RF3, RF1, IA, Coord3, Vx).
    """
    if "win32" in sys.platform.lower():
        job_folder = r"C:\Temp"
    elif "linux" in sys.platform.lower():
        job_folder = r"/mnt/Pure/jobfolder"
    else:
        raise Exception("Platform not identified, cannot continue.")

    brake_solver_sub_folder = "step-*-Solver_Braking_*"
    odb_file_name = "main.odb"
    brake_solver_odb_match = os.path.join(
        job_folder, brake_id_str, brake_solver_sub_folder, odb_file_name
    )
    odb_file_path = glob.glob(brake_solver_odb_match)

    if not odb_file_path:
        raise Exception("glob cannot find any odb file in the specified folder name pattern")

    # Upgrade ODB file if necessary
    odb_file_path_upgraded = upgrade_odb_if_necessary(odb_file_path[0])

    print(f"  Open odb file: {odb_file_path_upgraded}")
    curr_odb = openOdb(odb_file_path_upgraded, readOnly=True)

    rf3, rf1, ia, coord3, vx = None, None, None, None, None

    print("  extract last step in odb file")
    step_name = list(curr_odb.steps.keys())[-1]
    step = list(curr_odb.steps.values())[-1]
    print(f"   -- extract {step_name}")

    # ROAD for displacement and velocity
    # ** Road Node: No boundary conditions are applied to this node. This node is
    # **      controlled through the connector ROAD_HANDLE_CONNECTOR. This node is
    # **      the reference node for the road rigid body
    try:
        history_road = step.historyRegions["Node PART-1-1.99111004"]
        vx = history_road.historyOutputs["V1"].data[-1][1]
        coord3 = history_road.historyOutputs["COOR3"].data[-1][1]
    except KeyError:
        raise UserWarning("Failed to extract COOR3 or V1 data from the ODB file.")

    # ROAD_HANDLE for reaction forces
    # ** Road Handle: This node is the handle for applying rotations and moments to
    # **      the road. Forces and displacements should not be applied to this node.
    # **      Because forces and displacements are ALWAYS in the global coordinate
    # **      system and the global coordinate system does not rotate as the rigid body
    # **      rotates. Hence, we use a connector whose coordinate system is updated
    # **      as the rigid body rotates for applying forces and displacements.
    try:
        history_road_handle = step.historyRegions["Node PART-1-1.99111005"]
        rf3 = history_road_handle.historyOutputs["RF3"].data[-1][1] * -1.0
        rf1 = history_road_handle.historyOutputs["RF1"].data[-1][1]
    except KeyError:
        raise UserWarning("Failed to extract RF3 or RF1 data from the ODB file.")

    # use rim handle to obtain camber, camber is applied on tire instead of road
    # ** Rim Handle: This node is the handle for applying rotations and moments to the
    # **      wheel. Forces and displacements should not be applied to this node.
    # **      Because forces and displacements are ALWAYS in the global coordinate
    # **      system and this coordinate system does not rotate as the rigid body
    # **      rotates. Hence, we use a connector whose coordinate system is updated
    # **      as the rigid body rotates for applying forces and displacement.
    # **      Exception: Wheel torque is not applied to this node but at the connector
    try:
        history_rim_handle = step.historyRegions["Node PART-1-1.99222000"]
        ia = round(
            history_rim_handle.historyOutputs["UR1"].data[-1][1] * 180 / math.pi,
            2,
        )
    except KeyError:
        raise UserWarning("Failed to extract UR1 data from the ODB file.")

    if rf3 is not None and rf3 < 1000:
        print(f"  RF3 is too small (RF3 = {rf3:.2f} N). Please check the simulation.")

    return rf3, rf1, ia, coord3, vx

def main(brake_br_hpc_ids):
    """
    Main function to extract braking data and write it to a CSV file.

    Args:
        brake_br_hpc_ids (list): A list of brake BR HPC IDs to process.
    """
    sr_array, rf1_array, crd3_array, vx_array = [], [], [], []
    sr_hist = [
        -0.3, -0.25, -0.2, -0.15, -0.1, -0.05, -0.02, -0.01, 0.0,
        0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3,
    ]

    rf3, ia = None, None
    for i, brake_id in enumerate(brake_br_hpc_ids):
        brake_id_str = str(brake_id)
        print("=================================")
        print(f"Extracting data for {brake_id_str}")
        try:
            rf3_val, rf1_val, ia_val, coord3_val, vx_val = extract_odb_data(brake_id_str)
            if any(v is None for v in [rf3_val, rf1_val, ia_val, coord3_val, vx_val]):
                print(f"  Skipping brake ID {brake_id_str} due to missing data.")
                continue
            
            rf3, ia = rf3_val, ia_val
            sr_array.append(sr_hist[i])
            rf1_array.append(rf1_val)
            crd3_array.append(coord3_val)
            vx_array.append(vx_val)
        except (UserWarning, Exception) as e:
            print(f"  Skipping brake ID {brake_id_str} due to an error: {e}")
            continue

    if not sr_array:
        print("No data was extracted. Exiting.")
        return

    sorted_lists = sort_lists_by_first(sr_array, rf1_array, crd3_array, vx_array)
    sr_array, rf1_array, crd3_array, vx_array = sorted_lists

    brake_data_file = f"SR_Sweep_{rf3:.0f}N_{ia:.0f}deg.csv"
    print(f'  Formatting and writing data to "{brake_data_file}"')

    cwd = os.getcwd()
    with open(os.path.join(cwd, brake_data_file), "w") as disp_file:
        disp_file.write("SR, FX, LR, VX\n")
        for i in range(len(sr_array)):
            disp_file.write(
                f"{sr_array[i]:8.5f}, {rf1_array[i]:12.5f}, "
                f"{crd3_array[i]:12.5f}, {vx_array[i]:12.5f}\n"
            )

    print("=================================")
    print("Data written successfully!")


if __name__ == "__main__":
    try:
        import debugpy
        debugpy.listen(("localhost", 5678))
        print("debugpy is listening on port 5678. Waiting for client to attach...")
        debugpy.wait_for_client()
        print("Client attached. Debugging started.")
        debuypy.breakpoint()
    except ImportError:
        print("debugpy not found. Skipping remote debugger attachment.")

    unique_sorted_list = parse_and_process_arguments()
    main(unique_sorted_list)
