import os
import unittest

# The abaqus_script needs to be imported after the path is set.
# We are now assuming this test will be run in an environment where
# Abaqus modules like 'odbAccess' are available.
from src.abaqus_script import (
    _get_file_path,
    _upgrade_odb_if_need,
    extract_odb_data,
)

from src.utility import load_config


class TestAbaqusScript(unittest.TestCase):
    """Integration test cases for functions in abaqus_script.py."""

    def setUp(self):
        """Set up common test data and temporary directory for file system tests."""
        self.config = load_config()
        self.test_dir = r".\data\12032\step-01-Solver_Braking_1.24"

    def tearDown(self):
        pass

    def test_get_file_path_success(self):
        """Integration test for _get_file_path function for successful file finding."""
        job_id = "12032"
        sim_type = "Braking"
        odb_file_name = self.config["odb_file_name"]
        uamp_file_name = self.config["uamp_file_name"]

        file_path = _get_file_path(job_id, sim_type, self.config, odb_file_name)
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(file_path.endswith(".odb"))

    def test_get_file_path_not_found(self):
        """Integration test for _get_file_path function when no file is found."""
        job_id = "nonexistent_job"
        sim_type = "Braking"
        file_name = "nonexistent.odb"

        with self.assertRaises(IOError):
            _get_file_path(job_id, sim_type, self.config, file_name)

    def test_upgrade_odb_if_need(self):
        """Integration test for _upgrade_odb_if_need."""

        test_odb_path = os.path.join(self.test_dir, "main.odb")
        new_odb_path = _upgrade_odb_if_need(test_odb_path)
        self.assertEqual(os.path.basename(new_odb_path), "main.odb")

    def test_extract_odb_data(self):
        """
        Integration test for extract_odb_data.
        """
        job_id = "12032"
        sim_type = "Braking"
        extracted_data = extract_odb_data(job_id, sim_type, self.config)
        self.assertEqual(extracted_data["step_name"], ["Step-3"])


if __name__ == "__main__":
    try:
        import debugpy

        debugpy.listen(("localhost", 5678))
        print("debugpy is listening on port 5678. Waiting for client to attach...")
        debugpy.wait_for_client()
        print("Client attached. Debugging started.")
        debugpy.breakpoint()

    except ImportError:
        print("debugpy not found. Skipping remote debugger attachment.")

    unittest.main(argv=["first-arg-is-ignored"], exit=False)
