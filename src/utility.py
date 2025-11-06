"""
Utility functions for post-processing Abaqus simulation data.

This module provides helper functions for parsing input, handling files,
and processing data.

Author: Eric Zhang (zhanghui@bfusa.com)
Date: Nov. 5, 2025
"""

import argparse
import os
import sys
import yaml


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


def parse_matlab_array_input(input_str):
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
                        "Range part '{}' must contain exactly one colon.".format(
                            element
                        )
                    )
                b = int(range_parts[0].strip())
                c = int(range_parts[1].strip())
                combined_list.extend(generate_range_list(b, c))
            else:
                a = int(element)
                combined_list.append(a)
        except ValueError:
            raise ValueError(
                "Invalid integer format in element '{}'. ".format(element)
                + "All numbers must be valid integers."
            )
    return combined_list


def case_insensitive_choice(arg_value):
    """Converts the argument value to title case for case-insensitive validation."""
    return arg_value.title()


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


def load_config():
    """Loads the configuration from the config.yaml file."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


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

    parser.add_argument(
        "-t",
        "--type",
        type=case_insensitive_choice,
        required=True,
        choices=["Braking", "Cornering"],
        help="The type of simulation to post-process (e.g., 'Braking', 'Cornering').\n    The input is case-insensitive.",
    )

    args = parser.parse_args()
    input_str = args.input
    sim_type = args.type

    try:
        result_list = parse_matlab_array_input(input_str)
        unique_list = list(set(result_list))
        return unique_list, sim_type

    except ValueError as e:
        print("\nError processing input: {}\n".format(e))
        sys.exit(1)
