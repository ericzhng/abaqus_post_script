import unittest
import sys
import os

from src.utility import (
    generate_range_list,
    parse_matlab_array_input,
    case_insensitive_choice,
    sort_lists_by_first,
    load_config,
    parse_arguments,
    get_file_path,
)


class TestUtility(unittest.TestCase):
    """Test cases for general utility functions."""

    def test_generate_range_list(self):
        """Test the generate_range_list function."""
        self.assertEqual(generate_range_list(1, 5), [1, 2, 3, 4, 5])
        self.assertEqual(generate_range_list(5, 1), [5, 4, 3, 2, 1])
        self.assertEqual(generate_range_list(3, 3), [3])

    def test_parse_matlab_array_input(self):
        """Test the parse_matlab_array_input function."""
        self.assertEqual(parse_matlab_array_input("[1, 3:5, 8]"), [1, 3, 4, 5, 8])
        self.assertEqual(parse_matlab_array_input("[10, 8:5, 2]"), [10, 8, 7, 6, 5, 2])
        with self.assertRaises(ValueError):
            parse_matlab_array_input("[]")
        with self.assertRaises(ValueError):
            parse_matlab_array_input("[1, 2:3:4, 5]")
        with self.assertRaises(ValueError):
            parse_matlab_array_input("[1, a:4, 5]")

    def test_case_insensitive_choice(self):
        """Test the case_insensitive_choice function."""
        self.assertEqual(case_insensitive_choice("braking"), "Braking")
        self.assertEqual(case_insensitive_choice("Cornering"), "Cornering")
        self.assertEqual(case_insensitive_choice("BRAKING"), "Braking")

    def test_sort_lists_by_first(self):
        """Test the sort_lists_by_first function."""
        list1 = [3, 1, 2]
        list2 = ["c", "a", "b"]
        list3 = [True, False, True]
        sorted_lists = sort_lists_by_first(list1, list2, list3)
        self.assertEqual(
            sorted_lists, [[1, 2, 3], ["a", "b", "c"], [False, True, True]]
        )

    def test_load_config(self):
        """Test the load_config function."""
        config = load_config()
        self.assertIsInstance(config, dict)
        self.assertIn("paths", config)
        self.assertIn("abaqus_settings", config)
        self.assertIn("extraction_details", config)

    def test_parse_arguments(self):
        """Test the parse_arguments function."""
        original_argv = sys.argv
        try:
            # Test valid input
            sys.argv = ["script_name", "-i", "[1,2,3]", "-t", "Braking"]
            result_list, sim_type, output_path = parse_arguments()
            self.assertEqual(result_list, [1, 2, 3])
            self.assertEqual(sim_type, "Braking")

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


class TestGetFilePath(unittest.TestCase):
    """Test cases for the get_file_path function."""

    def setUp(self):
        """Load the configuration for testing."""
        self.config = load_config()

    def test_get_file_path_success_with_key(self):
        """Test successful file path retrieval using a file name key."""
        file_path = get_file_path(
            "12032", "Braking", self.config, file_name_key="uamp_properties"
        )
        self.assertTrue(os.path.exists(file_path))
        self.assertEqual(os.path.basename(file_path), "uamp-properties.dat")

    def test_get_file_path_success_with_name(self):
        """Test successful file path retrieval using a file name."""
        file_path = get_file_path(
            "12032", "Braking", self.config, file_name="uamp-properties.dat"
        )
        self.assertTrue(os.path.exists(file_path))
        self.assertEqual(os.path.basename(file_path), "uamp-properties.dat")

    def test_get_file_path_not_found(self):
        """Test that FileNotFoundError is raised for a nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            get_file_path("12032", "Braking", self.config, file_name="nonexistent.file")

    def test_get_file_path_no_name_or_key(self):
        """Test that ValueError is raised if no file name or key is provided."""
        with self.assertRaises(ValueError):
            get_file_path("12032", "Braking", self.config)


if __name__ == "__main__":
    unittest.main()
