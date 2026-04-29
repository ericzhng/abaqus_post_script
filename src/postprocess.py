import os
import json

import numpy as np

from .simulation_io import extract_uamp_property, run_abaqus_post
from .abaqus_post.mylogger import get_logger

logger = get_logger()


def process_fm_data(job_ids, sim_type, config, output_path):
    """
    Main function to extract simulation data and write it to a CSV file.

    This function iterates through a list of job IDs, extracts simulation data
    for each, and compiles the results. The extracted data is then sorted and
    saved to a CSV file in the specified output directory.

    Args:
        job_ids (list): A list of job IDs to process.
        sim_type (str): The type of simulation (e.g., 'Braking', 'Cornering', 'Freerolling', 'Cleat').
        config (dict): Configuration dictionary with paths and settings.
        output_path (str): The directory where the output CSV file will be saved.
    """
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
    os.makedirs(output_path, exist_ok=True)

    results = []
    logger.info(f"Starting data extraction for {len(job_ids)} jobs...")

    for job_id in job_ids:
        job_id_str = str(job_id)
        logger.info("=================================")
        logger.info(f"  Processing job ID: {job_id_str}")

        try:
            # Extract control variable and results from the simulation output
            control_variable = extract_uamp_property(job_id_str, sim_type, config)

            extract_data = run_abaqus_post(
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
                logger.warning(
                    f"  Size mismatch for job ID {job_id_str}: "
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

            logger.info(f"  Successfully extracted data for job ID: {job_id_str}")

        except FileNotFoundError as e:
            logger.warning(f"  Skipping job ID {job_id_str}: File not found - {e}")
        except (UserWarning, ValueError, KeyError) as e:
            logger.warning(f"  Skipping job ID {job_id_str}: Data error - {e}")
        except Exception as e:
            logger.error(f"  Skipping job ID {job_id_str}: Unexpected error - {e}")

    logger.info("Finished data extraction.")
    logger.info("=================================")

    if not results:
        logger.warning("No data was extracted. Exiting.")
        return

    # Define the data structure for the structured numpy array

    logger.info("Processing and sorting extracted data...")
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
    logger.info("Data sorted successfully by 'Slip'.")

    # Prepare for file writing
    fz_val = data_array["FZ"][0]
    ia_val = data_array["IA"][0]
    simulation_data_file = f"{sim_type}_sweep_{fz_val:.0f}N_{ia_val:.0f}deg.csv"
    output_file_path = os.path.join(output_path, simulation_data_file)

    logger.info(f'Formatting and writing data to "{simulation_data_file}"...')

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

    logger.info("=================================")
    logger.info("Workflow completed successfully!")
    logger.info(f"Output file saved to: {output_file_path}")


def process_cleat_data(job_ids, sim_type, config, output_path):
    """
    Main function to extract simulation data and write it to a CSV file.

    This function iterates through a list of job IDs, extracts simulation data
    for each, and compiles the results. The extracted data is then sorted and
    saved to a CSV file in the specified output directory.

    Args:
        job_ids (list): A list of job IDs to process.
        sim_type (str): The type of simulation (e.g., 'Braking', 'Cornering', 'Freerolling', 'Cleat').
        config (dict): Configuration dictionary with paths and settings.
        output_path (str): The directory where the output CSV file will be saved.
    """
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
    os.makedirs(output_path, exist_ok=True)

    logger.info(f"Starting data extraction for {len(job_ids)} jobs...")

    for job_id in job_ids:
        job_id_str = str(job_id)
        logger.info("=================================")
        logger.info(f"  Processing job ID: {job_id_str}")

        try:
            extract_data = run_abaqus_post(
                src_dir, output_path, job_id_str, sim_type, config
            )
            logger.info(f"  Successfully extracted data for job ID: {job_id_str}")

            # extract load and velocity
            omega = extract_data["drum_spindle_connector_CVR1"][-1]
            R_drum = 1000.0  # mm
            Vx = round(omega * R_drum * 3.6)  # kph
            fz = round(extract_data["rim_handle_RF3_ANTIALIASING"][0], -2)
            fy = np.max(np.abs(extract_data["rim_handle_RF2_ANTIALIASING"]))

            if fy > 0.1 * fz:
                cleat_type = "oblique"
            else:
                cleat_type = "transverse"

            output_file_path = os.path.join(
                output_path,
                f"{cleat_type}_cleat_{fz:.0f}N_{Vx:.0f}kph_{job_id_str}.json",
            )
            with open(output_file_path, "w") as f:
                json.dump(extract_data, f)

            logger.info(f"Output file saved to: {output_file_path}")

        except FileNotFoundError as e:
            logger.warning(f"  Skipping job ID {job_id_str}: File not found - {e}")
        except (UserWarning, ValueError, KeyError) as e:
            logger.warning(f"  Skipping job ID {job_id_str}: Data error - {e}")
        except Exception as e:
            logger.error(f"  Skipping job ID {job_id_str}: Unexpected error - {e}")

    logger.info("Finished data extraction.")
    logger.info("=================================")

    logger.info("=================================")
    logger.info("Workflow completed successfully!")
