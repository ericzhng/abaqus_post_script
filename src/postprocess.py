from collections import defaultdict
import os
import json

import numpy as np

from .simulation_io import extract_uamp_property, run_abaqus_post
from .abaqus_post.mylogger import get_logger

logger = get_logger()


def process_fm_data(job_ids, sim_type, config, output_path):
    """
    Main function to extract simulation data and save it to a JSON file.

    This function iterates through a list of job IDs, extracts simulation data
    for each, and saves the results to JSON files in the specified output directory.

    Args:
        job_ids (list): A list of job IDs to process.
        sim_type (str): The type of simulation (e.g., 'braking', 'cornering', 'freerolling', 'cleat_drum').
        config (dict): Configuration dictionary with paths and settings.
        output_path (str): The directory where the output files will be saved.
    """
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(output_path, exist_ok=True)

    logger.info(f"Starting data extraction for {len(job_ids)} job(s)...")

    results = defaultdict(list)

    for i, job_id in enumerate(job_ids, start=1):
        job_id_str = str(job_id)
        logger.info("-" * 60)
        logger.info(f"[{i}/{len(job_ids)}] Processing Job ID: {job_id_str}")

        try:
            # Extract control variable and results from the simulation output
            control_variable = extract_uamp_property(job_id_str, sim_type, config)

            extract_data: dict = run_abaqus_post(
                src_dir, output_path, job_id_str, sim_type, config
            )

            # Depending on whether there are multiple steps in a single odb
            if control_variable.size == 1:
                if len(next(iter(extract_data.values()))) == 1:
                    results["slip"].append(control_variable[0].tolist())
                    for key, val in extract_data.items():
                        results[key].append(val[0])
            else:
                if len(next(iter(extract_data.values()))) != control_variable.size:
                    msg = (
                        f"Unmatched number of entries: "
                        f"UAMP: #{control_variable.size} entries, "
                        f"ODB:  #{len(next(iter(extract_data.values())))} entries."
                    )
                    logger.error(msg)
                    raise ValueError(msg)

                results["slip"].extend(control_variable.tolist())
                for key, val in extract_data.items():
                    results[key].extend(val)

            logger.info(f"  Successfully extracted data for job ID: {job_id_str}")

        except FileNotFoundError as e:
            logger.warning(f"  Skipping job ID {job_id_str}: File not found - {e}")
        except (UserWarning, ValueError, KeyError) as e:
            logger.warning(f"  Skipping job ID {job_id_str}: Data error - {e}")
        except Exception as e:
            logger.error(f"  Skipping job ID {job_id_str}: Unexpected error - {e}")

    if not results:
        logger.warning("No data was extracted. Exiting.")
        return

    # Prepare for file writing
    fz_val = results["road_handle_RF3"][0]
    ia_val = np.rad2deg(results["rim_handle_UR1"][0]).tolist()
    simulation_data_file = f"{sim_type}_sweep_{fz_val:.0f}N_{ia_val:.0f}deg.json"
    json_file_path = os.path.join(output_path, simulation_data_file)

    with open(json_file_path, "w") as f:
        json.dump(results, f, indent=4)
    logger.info(f"  -> Output file saved to: {json_file_path}")

    logger.info("-" * 60)
    logger.info("Finished data extraction across all jobs.")
    logger.info("")

    logger.info("Workflow completed successfully!")


def process_cleat_data(job_ids, sim_type, config, output_path):
    """
    Main function to extract simulation data and write it to a JSON file.

    This function iterates through a list of job IDs, extracts simulation data
    for each, and saves it to JSON files in the specified output directory.

    Args:
        job_ids (list): A list of job IDs to process.
        sim_type (str): The type of simulation (e.g., 'Braking', 'Cornering', 'Freerolling', 'Cleat').
        config (dict): Configuration dictionary with paths and settings.
        output_path (str): The directory where the output JSON file will be saved.
    """
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(output_path, exist_ok=True)

    logger.info(f"Starting data extraction for {len(job_ids)} job(s)...")

    for i, job_id in enumerate(job_ids, start=1):
        job_id_str = str(job_id)
        logger.info("-" * 60)
        logger.info(f"[{i}/{len(job_ids)}] Processing Job ID: {job_id_str}")

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

            logger.info(f"  -> Output file saved to: {output_file_path}")

        except FileNotFoundError as e:
            logger.warning(f"  Skipping job ID {job_id_str}: File not found - {e}")
        except (UserWarning, ValueError, KeyError) as e:
            logger.warning(f"  Skipping job ID {job_id_str}: Data error - {e}")
        except Exception as e:
            logger.error(f"  Skipping job ID {job_id_str}: Unexpected error - {e}")

    logger.info("-" * 60)
    logger.info("Finished data extraction across all jobs.")
    logger.info("")

    logger.info("Workflow completed successfully!")
