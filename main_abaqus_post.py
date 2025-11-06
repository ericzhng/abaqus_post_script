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
import numpy as np

from src.utility import (
    parse_and_process_arguments,
    load_config,
)

from src.simulation_io import extract_uamp_property, extract_odb_result


def main(job_ids, sim_type, config, output_path):
    """
    Main function to extract simulation data and write it to a CSV file.

    Args:
        job_ids (list): A list of job IDs to process.
    """
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")

    os.makedirs(output_path, exist_ok=True)

    control_variable_list = []
    result_list = []

    for i, job_id in enumerate(job_ids):
        job_id_str = str(job_id)
        print("=================================")
        print("Extracting data for {}".format(job_id_str))

        try:
            control_variable = extract_uamp_property(job_id_str, sim_type, config)
            extract_data = extract_odb_result(
                src_dir, output_path, job_id_str, sim_type, config
            )
            control_variable_list.append(control_variable)
            result_list.append(extract_data)

        except (UserWarning, Exception) as e:
            print("  Skipping job ID {} due to an error: {}".format(job_id_str, e))
            continue

    if not control_variable_list:
        print("No data was extracted. Exiting.")
        return

    # Flatten lists and sort by control variable
    cv_array = np.array(control_variable_list)

    FZ_array = np.array([value for list in result_list for value in list["RF3"]])
    FX_array = np.array([value for list in result_list for value in list["RF1"]])
    FY_array = np.array([value for list in result_list for value in list["RF2"]])

    MX_array = np.array([value for list in result_list for value in list["TM1"]])
    MZ_array = np.array([value for list in result_list for value in list["TM3"]])

    IA_array = np.array([value for list in result_list for value in list["UR1"]])
    LR_array = np.array([value for list in result_list for value in list["COOR3"]])

    VX_array = np.array([value for list in result_list for value in list["V1"]])
    VY_array = np.array([value for list in result_list for value in list["V2"]])

    simulation_data_file = (
        f"{sim_type}_Sweep_{FZ_array[0]:.0f}N_{IA_array[0]:.0f}deg.csv"
    )
    print('  Formatting and writing data to "{}"'.format(simulation_data_file))

    with open(os.path.join(output_path, simulation_data_file), "w") as disp_file:
        disp_file.write("Slip, FX, FY, MX, MZ, LR, VX, VY\n")

        # write the above numpy arrays to csv file
        for i in range(len(cv_array)):
            disp_file.write(
                "{:4.1f},{:6.2f},{:6.2f},{:6.2f},{:6.2f},{:6.2f},{:6.2f},{:6.2f}\n".format(
                    cv_array[i],
                    FX_array[i],
                    FY_array[i],
                    MX_array[i],
                    MZ_array[i],
                    LR_array[i],
                    VX_array[i],
                    VY_array[i],
                )
            )

    print("=================================")
    print("Data written successfully!")


if __name__ == "__main__":
    # parse command-line arguments
    unique_list, sim_type, output_path = parse_and_process_arguments()

    config = load_config()
    main(unique_list, sim_type, config, output_path)

    print("All done!")
