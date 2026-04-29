# unittests designed for newer abaqus 2024+, may not work for older versions

import os
import unittest

from src.abaqus_post.common import upgrade_odb_if_needed
from src.abaqus_post.extract_odb import extract_fm_odb
from src.preprocess import load_config


class TestAbaqusPython(unittest.TestCase):
    """Test cases for functions in abaqus_script.py."""

    def setUp(self):
        """Set up common test data."""
        project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        self.config = load_config(project_root)
        self.test_dir = os.path.join(
            project_root, "data", "12032", "step-01-Solver_Braking_1.24"
        )

    def test_upgrade_odb_if_needed(self):
        """Test _upgrade_odb_if_needed."""
        # This test assumes the ODB file does not need an upgrade.
        test_odb_path = os.path.join(self.test_dir, "main.odb")
        new_odb_path = upgrade_odb_if_needed(test_odb_path)
        self.assertEqual(os.path.basename(new_odb_path), "main.odb")

    def test_extract_odb_data(self):
        """Test extract_odb_data."""
        job_id = "123000"
        sim_type = "braking"
        extracted_data = extract_fm_odb(job_id, sim_type, self.config)
        self.assertEqual(extracted_data["step_name"], ["Step-3"])


if __name__ == "__main__":
    try:
        import debugpy

        debugpy.listen(("localhost", 5678))
        print("debugpy is listening on port 5678. Waiting for client to attach...")
        debugpy.wait_for_client()
        print("Client attached. Debugging started.")
    except ImportError:
        print("debugpy not found. Skipping remote debugger attachment.")

    unittest.main(argv=["first-arg-is-ignored"], exit=False)
