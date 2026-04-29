import os
import sys
import glob
import subprocess

from odbAccess import isUpgradeRequiredForOdb


def get_file_path(job_id_str, config, file_name=None, file_name_key=None):
    """
    Constructs the file path for a given simulation file based on configuration.

    This helper function builds a file path pattern using the job ID, simulation
    type, and configuration details, then searches for a matching file.

    Args:
        job_id_str (str): The job ID.
        config (dict): A dictionary containing configuration parameters.
        file_name (str, optional): The name of the file to locate. Defaults to None.
        file_name_key (str, optional): The key for the file name in the config. Defaults to None.

    Returns:
        str: The absolute path to the located file.

    Raises:
        IOError: If no file matching the constructed pattern is found.
        ValueError: If neither file_name nor file_name_key is provided.
    """
    if file_name is None and file_name_key is None:
        raise ValueError("Either file_name or file_name_key must be provided.")

    platform = "win32" if "win32" in sys.platform.lower() else "linux"
    job_folder = config["paths"]["job_folder"][platform]

    if file_name_key:
        file_name = config["paths"]["file_names"][file_name_key]

    if file_name is None:
        raise ValueError("file_name must not be None when constructing file path.")

    solver_sub_folder = config["paths"]["solver_sub_folder_pattern"]

    file_match_pattern = os.path.join(
        job_folder, job_id_str, solver_sub_folder, file_name
    )

    file_path_list = glob.glob(file_match_pattern)

    if not file_path_list:
        raise IOError("No file found for pattern: {}".format(file_match_pattern))

    return [os.path.abspath(file_path) for file_path in file_path_list]


def unicode_to_str(data):
    """
    Recursively converts dictionary keys and string values from unicode to str
    in a Python 2.7 environment. Acts as a passthrough for Python 3+.
    """
    if sys.version_info[0] >= 3:
        return data

    if isinstance(data, dict):
        return {unicode_to_str(k): unicode_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [unicode_to_str(i) for i in data]
    elif type(data).__name__ == "unicode":
        return data.encode("utf-8")
    else:
        return data


def upgrade_odb_if_needed(odb_file_name):
    """
    Upgrades an Abaqus ODB file to the current version if outdated.

    This function checks if the specified ODB file requires an upgrade to be
    compatible with the current Abaqus version. If an upgrade is needed, it
    runs the Abaqus upgrade utility. An upgraded file with the `_upgraded`
    suffix is created.
    """
    from .mylogger import get_logger

    logger = get_logger()

    logger.info("Checking if ODB upgrade is required for: {}".format(odb_file_name))
    odb_base, _ = os.path.splitext(odb_file_name)
    upgraded_odb_file_name = odb_base + "_upgraded.odb"

    if isUpgradeRequiredForOdb(upgradeRequiredOdbPath=odb_file_name):
        if not os.path.exists(upgraded_odb_file_name):
            logger.info("Upgrading ODB file...")
            command = [
                "abaqus",
                "-upgrade",
                "-job",
                odb_base + "_upgraded",
                "-odb",
                odb_file_name,
            ]
            result = subprocess.call(command)
            if result != 0:
                raise RuntimeError("ODB upgrade failed.")
            else:
                logger.info("ODB upgrade successful.")
        else:
            logger.info("Upgraded ODB file already exists.")
        return upgraded_odb_file_name
    else:
        logger.info("ODB file is up-to-date.")
        return odb_file_name
