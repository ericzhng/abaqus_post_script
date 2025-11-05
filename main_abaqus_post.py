"""
Extracts force and moment data from Abaqus ODB files for post-processing.

This script is designed to be run in the Abaqus Python environment to post-process
simulation results. It extracts reaction forces, coordinates, and velocities from
ODB files, processes the data, and saves it to a CSV file.

Author: Eric Zhang (zhanghui@bfusa.com)
Date: Nov. 5, 2025

Example Usage:
    /app/abaqusnet/Commands/abq2023hf3 python post_simulation_data.py -i "[<list_of_ids>]" -t "Braking"

Example:
    /app/abaqusnet/Commands/abq2023hf3 python post_simulation_data.py -i "[142872, 142879:142894]" -t "Braking"
"""

import os
import sys
import glob
import math
import argparse

from utility import (
    parse_and_process_arguments,
    sort_lists_by_first,
    load_config,
)

from simulation_io import extract_uamp_property, extract_odb_data


def main(job_ids, sim_type, config):
    """
    Main function to extract simulation data and write it to a CSV file.

    Args:
        job_ids (list): A list of job IDs to process.
    """
    control_variable_array, rf1_array, crd3_array, vx_array = [], [], [], []

    rf3, ia = None, None

    for i, job_id in enumerate(job_ids):
        job_id_str = str(job_id)
        print("=================================")
        print("Extracting data for {}".format(job_id_str))

        try:
            control_variable = extract_uamp_property(job_id_str, sim_type, config)
            rf3_val, rf1_val, ia_val, coord3_val, vx_val = extract_odb_data(
                job_id_str, sim_type, config
            )

            if any(v is None for v in [rf3_val, rf1_val, ia_val, coord3_val, vx_val]):
                print("  Skipping job ID {} due to missing data.".format(job_id_str))
                continue

            rf3, ia = rf3_val, ia_val
            control_variable_array.append(control_variable)
            rf1_array.append(rf1_val)
            crd3_array.append(coord3_val)
            vx_array.append(vx_val)

        except (UserWarning, Exception) as e:
            print("  Skipping job ID {} due to an error: {}".format(job_id_str, e))
            continue

    if not control_variable_array:
        print("No data was extracted. Exiting.")
        return

    sorted_lists = sort_lists_by_first(
        control_variable_array, rf1_array, crd3_array, vx_array
    )

    control_variable_array, rf1_array, crd3_array, vx_array = sorted_lists

    simulation_data_file = "{}_Sweep_{:.0f}N_{:.0f}deg.csv".format(sim_type, rf3, ia)
    print('  Formatting and writing data to "{}"'.format(simulation_data_file))

    cwd = os.getcwd()

    with open(os.path.join(cwd, simulation_data_file), "w") as disp_file:
        disp_file.write("Control_Variable, FX, LR, VX\n")

        for i in range(len(control_variable_array)):
            disp_file.write(
                "{sr:8.5f}, {rf1:12.5f}, ".format(
                    sr=control_variable_array[i], rf1=rf1_array[i]
                )
                + "{crd3:12.5f}, {vx:12.5f}\n".format(
                    crd3=crd3_array[i], vx=vx_array[i]
                )
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
        debugpy.breakpoint()

    except ImportError:
        print("debugpy not found. Skipping remote debugger attachment.")

    config = load_config()
    unique_list, sim_type = parse_and_process_arguments()
    main(unique_list, sim_type)
