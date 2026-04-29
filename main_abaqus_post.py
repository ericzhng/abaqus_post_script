"""
Extracts force and moment data from Abaqus ODB files for post-processing.

This script is designed to be run in the Abaqus Python environment to post-process
simulation results. It extracts reaction forces, coordinates, and velocities from
ODB files, processes the data, and saves it to a CSV file.

Author: Eric Zhang (zhanghui@bfusa.com)
Date: Nov. 5, 2025

Example Usage:
    /app/abaqusnet/Commands/abq2023hf3 python main_abaqus_post.py -i "[<list_of_ids>]" -t "braking" -o "/path/to/output"

Example:
    /app/abaqusnet/Commands/abq2023hf3 python main_abaqus_post.py -i "[142872, 142879:142894]" -t "cleat_drum" -o "./output"
"""

import os

from src import parse_arguments, load_config, process_fm_data, process_cleat_data
from src import get_logger

logger = get_logger()


def main():
    logger.info("=================================")
    logger.info("     ABAQUS POST-PROCESSING      ")
    logger.info("=================================")

    try:
        # Parse command-line arguments
        unique_list, sim_type, output_path = parse_arguments()

        # Load configuration
        config = load_config(os.path.dirname(__file__))

        # Run the main post-processing function
        if sim_type in ["braking", "cornering", "freerolling"]:
            process_fm_data(unique_list, sim_type, config, output_path)
        elif "cleat" in sim_type:
            process_cleat_data(unique_list, sim_type, config, output_path)
        else:
            raise ValueError(f"Unknown sim_type: {sim_type}")

    except Exception as e:
        logger.error(f"A critical error occurred: {e}")

    finally:
        logger.info("=================================")
        logger.info("  All operations have concluded.   ")
        logger.info("=================================")


if __name__ == "__main__":
    main()
