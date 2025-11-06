import unittest
import sys

from src.utility import (
    generate_range_list,
    parse_matlab_array_input,
    case_insensitive_choice,
    sort_lists_by_first,
    load_config,
    parse_and_process_arguments,
)


class TestUtility(unittest.TestCase):

    def test_generate_range_list(self):
        self.assertEqual(generate_range_list(1, 5), [1, 2, 3, 4, 5])
        self.assertEqual(generate_range_list(5, 1), [5, 4, 3, 2, 1])
        self.assertEqual(generate_range_list(3, 3), [3])

    def test_parse_matlab_array_input(self):
        self.assertEqual(parse_matlab_array_input("[1, 3:5, 8]"), [1, 3, 4, 5, 8])
        self.assertEqual(parse_matlab_array_input("[10, 8:5, 2]"), [10, 8, 7, 6, 5, 2])
        with self.assertRaises(ValueError):
            parse_matlab_array_input("[]")
        with self.assertRaises(ValueError):
            parse_matlab_array_input("[1, 2:3:4, 5]")
        with self.assertRaises(ValueError):
            parse_matlab_array_input("[1, a:4, 5]")

    def test_case_insensitive_choice(self):
        self.assertEqual(case_insensitive_choice("braking"), "Braking")
        self.assertEqual(case_insensitive_choice("Cornering"), "Cornering")
        self.assertEqual(case_insensitive_choice("BRAKING"), "Braking")

    def test_sort_lists_by_first(self):
        list1 = [3, 1, 2]
        list2 = ["c", "a", "b"]
        list3 = [True, False, True]
        sorted_lists = sort_lists_by_first(list1, list2, list3)
        self.assertEqual(
            sorted_lists, [[1, 2, 3], ["a", "b", "c"], [False, True, True]]
        )

    def test_load_config(self):
        config = load_config()
        self.assertIsInstance(config, dict)
        self.assertIn("paths", config)
        self.assertIn("abaqus_settings", config)
        self.assertIn("extraction_details", config)

    def test_parse_and_process_arguments(self):
        # Test valid input
        test_args = ["script_name", "-i", "[1,2,3]", "-t", "Braking"]
        sys_argv_orig = sys.argv
        try:
            sys.argv = test_args
            result_list, sim_type, output_path = parse_and_process_arguments()
            self.assertEqual(result_list, [1, 2, 3])
            self.assertEqual(sim_type, "Braking")
        finally:
            sys.argv = sys_argv_orig

        # Test invalid input (missing required argument)
        test_args = ["script_name", "-i", "[1,2,3]"]
        sys_argv_orig = sys.argv
        with self.assertRaises(SystemExit):
            try:
                sys.argv = test_args
                parse_and_process_arguments()
            finally:
                sys.argv = sys_argv_orig

        # Test invalid input (malformed array)
        test_args = ["script_name", "-i", "[1,a,3]", "-t", "Cornering"]
        sys_argv_orig = sys.argv
        with self.assertRaises(SystemExit):
            try:
                sys.argv = test_args
                parse_and_process_arguments()
            finally:
                sys.argv = sys_argv_orig


if __name__ == "__main__":
    unittest.main()
