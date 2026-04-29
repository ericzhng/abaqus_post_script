"""
:project: FlatTrac Friction Tool
:author: Eric Zhang <zhanghui@bfusa.com>
:copyright: (c) 2025 Bridgestone Americas Inc.
:license: See LICENSE.md for details.

.. module:: mylogger
   :platform: Unix, Windows
   :synopsis: Configures and returns a logger instance.
"""

import os
import sys
import logging

# Global variable to persist the log path across different calls
_global_log_path = "."


def get_logger(
    log_name="ericlog",
    log_path=None,
    log_file="run.log",
    log_file_debug="run_debug.log",
    force_configure=False,
):
    """Configures and returns a logger instance.

    Args:
        log_name (str): The unique name for the logger instance.
        log_path (str, optional): The directory where the log files will be stored.
                                  If provided, updates the global default path.
                                  If None, uses the current global default path.
        log_file (str): The name of the info-level log file.
        log_file_debug (str): The name of the debug-level log file.
        force_configure (bool): If True, clears existing handlers and reconfigures the logger.

    Returns:
        Logger: A configured logger instance.
    """
    global _global_log_path

    # If a path is explicitly provided, update the global setting
    if log_path is not None:
        _global_log_path = log_path

    # Use the current global path
    current_path = _global_log_path

    # Get a logger instance by name, which ensures that it's a singleton.
    logger = logging.getLogger(log_name)

    # If force_configure is True or a new path is provided, remove all existing handlers to allow reconfiguration.
    if (force_configure or log_path is not None) and logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()

    # Check if the logger has already been configured to avoid adding duplicate handlers.
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # Ensure the log directory exists.
        if not os.path.exists(current_path):
            os.makedirs(current_path)

        # Define formatters.
        file_formatter = logging.Formatter(
            "%(asctime)s %(levelname)s > %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        stream_formatter = logging.Formatter("%(levelname)s > %(message)s")

        # Create and add file handler for INFO level.
        info_log_handler = logging.FileHandler(
            os.path.join(current_path, log_file),
            mode="a",
            encoding="utf-8",
            delay=True,
        )
        info_log_handler.setFormatter(file_formatter)
        info_log_handler.setLevel(logging.INFO)
        logger.addHandler(info_log_handler)

        # Create and add file handler for DEBUG level.
        debug_log_handler = logging.FileHandler(
            os.path.join(current_path, log_file_debug),
            mode="a",
            encoding="utf-8",
            delay=True,
        )
        debug_log_handler.setFormatter(file_formatter)
        debug_log_handler.setLevel(logging.DEBUG)
        logger.addHandler(debug_log_handler)

        # Create and add stream handler to print logs to the console.
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(stream_formatter)
        stream_handler.setLevel(logging.INFO)  # Set console to INFO level
        logger.addHandler(stream_handler)

        # Prevent propagation to the root logger to avoid duplicate output.
        logger.propagate = False

    return logger
