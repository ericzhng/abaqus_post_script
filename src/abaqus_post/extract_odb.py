import os
import math
from contextlib import contextmanager

import numpy as np

from .common import upgrade_odb_if_needed, get_file_path
from .mylogger import get_logger

logger = get_logger()


def _get_odb_file_path(job_id_str, sim_type, config):
    """Finds the main ODB file path based on job ID and simulation type."""
    try:
        paths = get_file_path(job_id_str, config, file_name_key="odb_main")
    except IOError as e:
        logger.error(str(e))
        return None

    keyword = config["paths"]["solver_sub_folder_keyword"][sim_type].strip()
    if not keyword:
        return paths[0]

    match = next((p for p in paths if keyword in os.path.dirname(p)), None)
    if match:
        return match

    logger.error("No main.odb file found.")
    return None


@contextmanager
def _open_odb(job_id_str, sim_type, config):
    """Context manager to find, upgrade, and open an ODB file."""
    odb_file_path = _get_odb_file_path(job_id_str, sim_type, config)
    if not odb_file_path:
        yield None
        return

    logger.info("Found ODB file: {}".format(odb_file_path))
    odb_file_path_upgraded = upgrade_odb_if_needed(odb_file_path)

    logger.info("Opening ODB file: {}".format(odb_file_path_upgraded))

    from odbAccess import openOdb

    curr_odb = openOdb(odb_file_path_upgraded, readOnly=True)

    try:
        yield curr_odb
    finally:
        curr_odb.close()


def _get_steps_to_process(step_name_list, step_choice):
    """Determines which steps to process based on selection criteria."""
    if not step_name_list:
        return []

    if step_choice == "last":
        return [step_name_list[-1]]
    elif step_choice == "first":
        return step_name_list[:1]
    elif step_choice == "all":
        return step_name_list
    elif step_choice == "all_but_first" and len(step_name_list) > 1:
        return step_name_list[1:]
    else:
        msg = "Invalid or insufficient steps for selection criteria: '{}'".format(
            step_choice
        )
        logger.warning(msg)
        raise UserWarning(msg)


def _initialize_extracted_data(abq_setting, choice, include_runtime=False):
    """Initializes the dictionary to store extracted data."""
    extracted_data = {"step_name": []}
    if include_runtime:
        extracted_data["runtime"] = []

    for output_cat, outputs_list in abq_setting["history_outputs"][choice].items():
        for output_name in outputs_list:
            extracted_data["{}_{}".format(output_cat, output_name)] = []

    return extracted_data


def extract_fm_odb(job_id_str, sim_type, config):
    """
    Extracts specified simulation data from an Abaqus ODB file for FM simulations.

    This function orchestrates the process of finding the ODB file, upgrading it
    if necessary, and then extracting key data points (forces, coordinates, etc.)
    based on the provided configuration.
    """
    logger.info("Starting ODB data extraction for Job ID: {}".format(job_id_str))
    choice = "default"
    abq_setting = config["abaqus_settings"]

    with _open_odb(job_id_str, sim_type, config) as curr_odb:
        if not curr_odb:
            return None

        extracted_data = _initialize_extracted_data(abq_setting, choice)
        step_choice = abq_setting["history_step_selection"]["sim_type_mapping"].get(
            sim_type
        )
        step_name_list = list(curr_odb.steps.keys())

        try:
            steps_to_process = _get_steps_to_process(step_name_list, step_choice)
        except UserWarning as e:
            logger.error(str(e))
            return None

        logger.info(
            "Extracting data from steps: {}".format(", ".join(steps_to_process))
        )

        for step_name in steps_to_process:
            logger.info("Processing step: {}".format(step_name))
            step = curr_odb.steps[step_name]
            current_step_values = {}

            try:
                for region_key, outputs_list in abq_setting["history_outputs"][
                    choice
                ].items():
                    history_region_name = abq_setting["history_regions"][choice].get(
                        region_key
                    )
                    if not history_region_name:
                        msg = "History region '{}' not found in config".format(
                            region_key
                        )
                        logger.error(msg)
                        raise KeyError(msg)

                    history_region = step.historyRegions[history_region_name]
                    for output_name in outputs_list:
                        value = history_region.historyOutputs[output_name].data[-1][1]

                        # change sign for converting from adapted SAE to ISO coordinate system
                        if output_name in ("TM3", "RF2", "RF3"):
                            value *= -1.0
                        elif output_name == "UR1":
                            value = round(value * 180.0 / math.pi, 1)

                        current_step_values["{}_{}".format(region_key, output_name)] = (
                            value
                        )

                rf3_values = [v for k, v in current_step_values.items() if "RF3" in k]
                if rf3_values and rf3_values[0] < 1000:
                    logger.warning(
                        "RF3 is unexpectedly low (RF3 = {:.2f} N). Please verify simulation results.".format(
                            rf3_values[0]
                        )
                    )

                extracted_data["step_name"].append(step_name)
                for key, value in current_step_values.items():
                    extracted_data[key].append(value)
                logger.info(
                    "Successfully extracted data from step: {}".format(step_name)
                )

            except (KeyError, UserWarning) as e:
                logger.warning("Skipping step {} due to error: {}".format(step_name, e))
                continue

        logger.info("Finished ODB data extraction for Job ID: {}".format(job_id_str))
        return extracted_data


def extract_cleat_odb(job_id_str, sim_type, config):
    """
    Extracts specified simulation data from an Abaqus ODB file for Cleat simulations.

    This function orchestrates the process of finding the ODB file, upgrading it
    if necessary, and then extracting key data points (forces, coordinates, etc.)
    based on the provided configuration.
    """
    logger.info("Starting ODB data extraction for Job ID: {}".format(job_id_str))
    abq_setting = config["abaqus_settings"]

    with _open_odb(job_id_str, sim_type, config) as curr_odb:
        if not curr_odb:
            return None

        extracted_data = _initialize_extracted_data(
            abq_setting, sim_type, include_runtime=True
        )
        step_choice = abq_setting["history_step_selection"]["sim_type_mapping"].get(
            sim_type
        )
        step_name_list = list(curr_odb.steps.keys())

        try:
            steps_to_process = _get_steps_to_process(step_name_list, step_choice)
        except UserWarning as e:
            logger.error(str(e))
            return None

        logger.info(
            "Extracting data from steps: {}".format(", ".join(steps_to_process))
        )

        for step_name in steps_to_process:
            logger.info("Processing step: {}".format(step_name))
            step = curr_odb.steps[step_name]
            current_step_values = {}

            try:
                # extract runtime for cleat simulation
                hist_regions = list(step.historyRegions.values())
                if hist_regions:
                    hist_outputs = list(hist_regions[0].historyOutputs.values())
                    if hist_outputs:
                        tuple2d = hist_outputs[0].data
                        value2d = np.array(tuple2d)
                        extracted_data["runtime"].extend(value2d[:, 0].tolist())

                # extract history data
                for region_key, outputs_list in abq_setting["history_outputs"][
                    sim_type
                ].items():
                    history_region_name = abq_setting["history_regions"][sim_type].get(
                        region_key
                    )
                    if not history_region_name:
                        msg = "History region '{}' not found in config".format(
                            region_key
                        )
                        logger.error(msg)
                        raise KeyError(msg)

                    history_region = step.historyRegions[history_region_name]
                    for output_name in outputs_list:
                        tuple2d = history_region.historyOutputs[output_name].data
                        value2d = np.array(tuple2d)
                        value = value2d[:, -1]
                        current_step_values["{}_{}".format(region_key, output_name)] = (
                            value.tolist()
                        )

                extracted_data["step_name"].append(step_name)
                for key, value in current_step_values.items():
                    extracted_data[key].extend(value)
                logger.info(
                    "Successfully extracted data from step: {}".format(step_name)
                )

            except (KeyError, UserWarning) as e:
                logger.warning("Skipping step {} due to error: {}".format(step_name, e))
                continue

        logger.info("Finished ODB data extraction for Job ID: {}".format(job_id_str))
        return extracted_data
