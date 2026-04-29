import os
import sys
import yaml
import argparse

from .utility import parse_matlab_array_input
from .abaqus_post.mylogger import get_logger

logger = get_logger()


def load_config(config_dir):
    """Loads the configuration from the config.yaml file."""
    config_path = os.path.join(config_dir, "config.yaml")
    logger.info(f"Loading configuration from:  {config_path}")
    logger.info("")

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def case_insensitive_choice(arg_value):
    """Converts the argument value to lower case for case-insensitive validation."""
    return arg_value.lower()


def parse_arguments():
    """
    Sets up the command-line parser and processes user input.

    Returns:
        tuple: A tuple containing:
            - list: A unique, sorted list of integers from the input string.
            - str: The simulation type.
            - str: The output path.
    """
    logger.info("Parsing and validating arguments...")

    parser = argparse.ArgumentParser(
        description="A CLI tool that processes a MATLAB-style input string to generate a list of integers.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help='Input string in MATLAB-style: "[a, b:c, d:e, f]".\n    Supports single integers and inclusive ranges (b:c).',
    )

    parser.add_argument(
        "-t",
        "--type",
        type=case_insensitive_choice,
        required=True,
        choices=["braking", "cornering", "freerolling", "cleat_drum", "cleat_road"],
        help="Type of simulation (e.g., 'braking', 'cornering', 'FreeRolling, 'cleat_drum').\n    Input is case-insensitive.",
    )

    parser.add_argument(
        "-o", "--output", type=str, required=False, help="Output result directory."
    )

    args = parser.parse_args()
    input_str = args.input
    sim_type = args.type.lower()

    if args.output is None:
        output_path = os.getcwd()
    else:
        output_path = args.output

    try:
        result_list = parse_matlab_array_input(input_str)
        unique_list = sorted(list(set(result_list)))

        logger.info(f"  -> Simulation Type: {sim_type}")
        logger.info(f"  -> Output Path: {output_path}")
        logger.info(f"  -> Target Jobs: {len(unique_list)} job(s) identified.")
        logger.info("")

        return unique_list, sim_type, output_path

    except ValueError as e:
        logger.error(f"Invalid input provided: {e}")
        sys.exit(1)
