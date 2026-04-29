import os
from pathlib import Path
import unittest

from src.preprocess import load_config
from src.postprocess import extract_uamp_property, run_abaqus_post


class TestSimulationIO(unittest.TestCase):
    """Test cases for functions in simulation_io.py."""

    def setUp(self):
        """Set up common test data and configuration."""
        self.project_root = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".."
        )
        self.config = load_config(self.project_root)

        self.job_id_str_cornering = "30000"
        self.job_id_str_braking = "30001"
        self.sim_type_cornering = "cornering"
        self.sim_type_braking = "braking"

    def test_extract_uamp_property_braking(self):
        """Test slip ratio extraction for braking simulation."""
        slip_ratio = extract_uamp_property(
            self.job_id_str_braking, self.sim_type_braking, self.config
        )
        self.assertAlmostEqual(float(slip_ratio), -0.3, places=3)

    def test_extract_uamp_property_cornering(self):
        """Test slip angle extraction for cornering simulation."""
        slip_angle = extract_uamp_property(
            self.job_id_str_cornering, self.sim_type_cornering, self.config
        )
        self.assertAlmostEqual(float(slip_angle), -7.0, places=2)

    def test_extract_odb_result(self):
        """Test extraction of results from an ODB file."""
        src_dir = os.path.realpath(os.path.join(self.project_root, "src"))
        output_dir = os.path.realpath(os.path.join(self.project_root, "output"))
        Path(output_dir).mkdir(exist_ok=True)

        extract_data = run_abaqus_post(
            src_dir,
            output_dir,
            self.job_id_str_braking,
            self.sim_type_braking,
            self.config,
        )

        self.assertIn("road_handle_RF3", extract_data)
        self.assertAlmostEqual(
            float(extract_data["road_handle_RF3"][0]), 2075.0, places=1
        )


if __name__ == "__main__":
    unittest.main()
