import os
import unittest

from src.utility import load_config
from src.simulation_io import extract_uamp_property, extract_odb_result


class TestSimulationIO(unittest.TestCase):
    """Test cases for functions in simulation_io.py."""

    def setUp(self):
        """Set up common test data and configuration."""
        self.config = load_config()
        self.job_id_str = "12032"
        self.sim_type_braking = "Braking"
        self.sim_type_cornering = "Cornering"

    def test_extract_uamp_property_braking(self):
        """Test slip ratio extraction for braking simulation."""
        slip_ratio = extract_uamp_property(
            self.job_id_str, self.sim_type_braking, self.config
        )
        self.assertAlmostEqual(slip_ratio, -0.3, places=3)

    def test_extract_uamp_property_cornering(self):
        """Test slip angle extraction for cornering simulation."""
        slip_angle = extract_uamp_property(
            self.job_id_str, self.sim_type_cornering, self.config
        )
        self.assertAlmostEqual(slip_angle, -7.0, places=2)

    def test_extract_odb_result(self):
        """Test extraction of results from an ODB file."""
        src_dir = os.path.realpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
        )
        output_dir = os.path.realpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        )
        extract_data = extract_odb_result(
            src_dir, output_dir, self.job_id_str, self.sim_type_braking, self.config
        )
        # Verify that the extracted data contains expected keys and values
        self.assertIn("RF3", extract_data)
        self.assertAlmostEqual(extract_data["RF3"][0], 2075.0, places=1)


if __name__ == "__main__":
    unittest.main()
