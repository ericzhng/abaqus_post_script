import os
import sys
import unittest

from src.preprocess import case_insensitive_choice, load_config, parse_arguments


class TestPreprocess(unittest.TestCase):
    """Test cases for general utility functions."""

    def test_case_insensitive_choice(self):
        """Test the case_insensitive_choice function."""
        self.assertEqual(case_insensitive_choice("braking"), "braking")
        self.assertEqual(case_insensitive_choice("Cornering"), "cornering")
        self.assertEqual(case_insensitive_choice("BRAKING"), "braking")

    def test_load_config(self):
        """Test the load_config function."""
        project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        config = load_config(project_root)
        self.assertIsInstance(config, dict)
        self.assertIn("paths", config)
        self.assertIn("abaqus_settings", config)
        self.assertIn("extraction_details", config)

    def test_parse_arguments(self):
        """Test the parse_arguments function."""
        original_argv = sys.argv
        try:
            # Test valid input
            sys.argv = ["script_name", "-i", "[1,2,3]", "-t", "braking"]
            result_list, sim_type, output_path = parse_arguments()
            self.assertEqual(result_list, [1, 2, 3])
            self.assertEqual(sim_type, "braking")

            # Test invalid input (missing required argument)
            sys.argv = ["script_name", "-i", "[1,2,3]"]
            with self.assertRaises(SystemExit):
                parse_arguments()

            # Test invalid input (malformed array)
            sys.argv = ["script_name", "-i", "[1,a,3]", "-t", "Cornering"]
            with self.assertRaises(SystemExit):
                parse_arguments()
        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    unittest.main()
