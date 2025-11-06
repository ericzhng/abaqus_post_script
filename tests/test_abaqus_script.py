import os
import unittest

# It is assumed that this test is run in an environment where Abaqus modules
# like 'odbAccess' are available.
from src.abaqus_script import (
    _get_file_path,
    _upgrade_odb_if_needed,
    extract_odb_data,
)
from src.utility import load_config


class TestAbaqusScript(unittest.TestCase):
    """Test cases for functions in abaqus_script.py."""

    def setUp(self):
        """Set up common test data."""
        self.config = load_config()
        self.test_dir = r".\data\12032\step-01-Solver_Braking_1.24"

    def test_get_file_path_success(self):
        """Test _get_file_path for successful file finding."""
        job_id = "12032"
        sim_type = "Braking"
        file_path = _get_file_path(job_id, sim_type, self.config, "odb_main")
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(file_path.endswith(".odb"))

    def test_get_file_path_not_found(self):
        """Test _get_file_path when no file is found."""
        job_id = "nonexistent_job"
        sim_type = "Braking"
        with self.assertRaises(IOError):
            _get_file_path(job_id, sim_type, self.config, "nonexistent_key")

    def test_upgrade_odb_if_needed(self):
        """Test _upgrade_odb_if_needed."""
        # This test assumes the ODB file does not need an upgrade.
        test_odb_path = os.path.join(self.test_dir, "main.odb")
        new_odb_path = _upgrade_odb_if_needed(test_odb_path)
        self.assertEqual(os.path.basename(new_odb_path), "main.odb")

    def test_extract_odb_data(self):
        """Test extract_odb_data."""
        job_id = "12032"
        sim_type = "Braking"
        extracted_data = extract_odb_data(job_id, sim_type, self.config)
        self.assertEqual(extracted_data["step_name"], ["Step-3"])


if __name__ == "__main__":
    # Optional: For debugging with debugpy
    try:
        import debugpy

        debugpy.listen(("localhost", 5678))
        print("debugpy is listening on port 5678. Waiting for client to attach...")
        debugpy.wait_for_client()
        print("Client attached. Debugging started.")
    except ImportError:
        print("debugpy not found. Skipping remote debugger attachment.")

    unittest.main(argv=["first-arg-is-ignored"], exit=False)
