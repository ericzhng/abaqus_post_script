import os
import unittest

from src.utility import load_config
from src.simulation_io import _get_file_path, extract_uamp_property, extract_odb_result


class TestSimulationIO(unittest.TestCase):

    def setUp(self):
        """Set up common test data and temporary directory for file system tests."""
        self.config = load_config()
        self.job_id_str = "12032"
        self.sim_type_braking = "Braking"
        self.sim_type_cornering = "Cornering"

    def test_get_file_path_success(self):
        file_path = _get_file_path(
            self.job_id_str,
            self.sim_type_braking,
            self.config,
            self.config["uamp_file_name"],
        )
        self.assertEqual(os.path.basename(file_path), self.config["uamp_file_name"])

    def test_get_file_path_not_found(self):
        with self.assertRaises(FileNotFoundError):
            _get_file_path(
                self.job_id_str,
                self.sim_type_braking,
                self.config,
                "non_existent_file.dat",
            )

    def test_extract_uamp_property_braking(self):
        slip_ratio = extract_uamp_property(
            self.job_id_str, self.sim_type_braking, self.config
        )
        self.assertAlmostEqual(slip_ratio, -0.3, places=3)

    def test_extract_uamp_property_cornering(self):
        slip_angle = extract_uamp_property(
            self.job_id_str, self.sim_type_cornering, self.config
        )
        self.assertAlmostEqual(slip_angle, -7.0, places=2)

    def test_extract_odb_result(self):
        src_dir = os.path.realpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
        )
        output_dir = os.path.realpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        )
        extract_data = extract_odb_result(
            src_dir, output_dir, self.job_id_str, self.sim_type_braking, self.config
        )
        print(extract_data)
        self.assertAlmostEqual(extract_data["RF3"], 400.0)


if __name__ == "__main__":
    unittest.main()
