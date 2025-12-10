"""
Extracts force and moment data from Abaqus ODB files for post-processing.

This script is designed to be run in the Abaqus Python environment to post-process
simulation results. It extracts reaction forces, coordinates, and velocities from
ODB files, processes the data, and saves it to a CSV file.

Author: Eric Zhang (zhanghui@bfusa.com)
Date: Nov. 5, 2025

Example Usage:
    /app/abaqusnet/Commands/abq2023hf3 python post_simulation_data.py -i "[<list_of_ids>]" -t "Braking" -o "/path/to/output"

Example:
    /app/abaqusnet/Commands/abq2023hf3 python post_simulation_data.py -i "[142872, 142879:142894]" -t "Braking" -o "./output"
"""

import os
import numpy as np

from src.utility import parse_arguments, load_config
from src.simulation_io import extract_uamp_property, extract_odb_result


def main(job_ids, sim_type, config, output_path):
    """
    Main function to extract simulation data and write it to a CSV file.

    This function iterates through a list of job IDs, extracts simulation data
    for each, and compiles the results. The extracted data is then sorted and
    saved to a CSV file in the specified output directory.

    Args:
        job_ids (list): A list of job IDs to process.
        sim_type (str): The type of simulation (e.g., 'Braking', 'Cornering').
        config (dict): Configuration dictionary with paths and settings.
        output_path (str): The directory where the output CSV file will be saved.
    """
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
    os.makedirs(output_path, exist_ok=True)

    results = []
    print(f"Starting data extraction for {len(job_ids)} jobs...\n")

    for job_id in job_ids:
        job_id_str = str(job_id)
        print("=================================")
        print(f"  Processing job ID: {job_id_str}")

        try:
            # Extract control variable and results from the simulation output
            control_variable = extract_uamp_property(job_id_str, sim_type, config)
            extract_data = extract_odb_result(
                src_dir, output_path, job_id_str, sim_type, config
            )

            # Append all relevant data for this job_id as a tuple
            if len(extract_data["RF1"]) == control_variable.size:
                for k in range(control_variable.size):
                    results.append(
                        (
                            control_variable[k],
                            extract_data["RF1"][k],  # FX
                            extract_data["RF2"][k],  # FY
                            extract_data["RF3"][k],  # FZ
                            extract_data["TM1"][k],  # MX
                            extract_data["TM3"][k],  # MZ
                            extract_data["UR1"][k],  # IA
                            extract_data["COOR3"][k],  # LR
                            extract_data["V1"][k],  # VX
                            extract_data["V2"][k],  # VY
                        )
                    )
            else:
                print(
                    f"  [WARNING] Size mismatch for job ID {job_id_str}: "
                    f"Control variable size {control_variable.size} vs "
                    f"Extracted data size {len(extract_data['RF1'])}. "
                    "Using first value only."
                )
                results.append(
                    (
                        control_variable[0],
                        extract_data["RF1"][0],  # FX
                        extract_data["RF2"][0],  # FY
                        extract_data["RF3"][0],  # FZ
                        extract_data["TM1"][0],  # MX
                        extract_data["TM3"][0],  # MZ
                        extract_data["UR1"][0],  # IA
                        extract_data["COOR3"][0],  # LR
                        extract_data["V1"][0],  # VX
                        extract_data["V2"][0],  # VY
                    )
                )
            print(f"  Successfully extracted data for job ID: {job_id_str}")

        except FileNotFoundError as e:
            print(f"  [WARNING] Skipping job ID {job_id_str}: File not found - {e}")
        except (UserWarning, ValueError, KeyError) as e:
            print(f"  [WARNING] Skipping job ID {job_id_str}: Data error - {e}")
        except Exception as e:
            print(f"  [ERROR] Skipping job ID {job_id_str}: Unexpected error - {e}")

    print("\nFinished data extraction.")
    print("=================================\n")

    if not results:
        print("No data was extracted. Exiting.")
        return

    # Define the data structure for the structured numpy array
    print("Processing and sorting extracted data...")
    dtype = [
        ("Slip", "f8"),
        ("FX", "f8"),
        ("FY", "f8"),
        ("FZ", "f8"),
        ("MX", "f8"),
        ("MZ", "f8"),
        ("IA", "f8"),
        ("LR", "f8"),
        ("VX", "f8"),
        ("VY", "f8"),
    ]
    data_array = np.array(results, dtype=dtype)

    # Sort the array by the control variable ('Slip')
    data_array = np.sort(data_array, order="Slip")
    print("Data sorted successfully by 'Slip'.")

    # Prepare for file writing
    fz_val = data_array["FZ"][0]
    ia_val = data_array["IA"][0]
    simulation_data_file = f"{sim_type}_Sweep_{fz_val:.0f}N_{ia_val:.0f}deg.csv"
    output_file_path = os.path.join(output_path, simulation_data_file)

    print(f'\nFormatting and writing data to "{simulation_data_file}"...')

    # Define header and format for the CSV file
    columns_to_save = ["Slip", "FX", "FY", "FZ", "MX", "MZ", "IA", "LR", "VX", "VY"]
    header = ",".join(columns_to_save)

    # Use numpy.savetxt for efficient and clean CSV writing
    np.savetxt(
        output_file_path,
        data_array[columns_to_save],
        delimiter=",",
        header=header,
        comments="",
        fmt="%.3f",
    )

    print("=================================\n")
    print("Workflow completed successfully!")
    print(f"Output file saved to: {output_file_path}")


if __name__ == "__main__":
    print("=================================")
    print("     ABAQUS POST-PROCESSING      ")
    print("=================================")

    try:
        # Parse command-line arguments
        unique_list, sim_type, output_path = parse_arguments()

        # Load configuration
        config = load_config(os.path.dirname(__file__))

        # Run the main post-processing function
        main(unique_list, sim_type, config, output_path)

    except Exception as e:
        print(f"[ERROR] A critical error occurred: {e}")

    finally:
        print("\n=================================")
        print("  All operations have concluded.   ")
        print("=================================")
