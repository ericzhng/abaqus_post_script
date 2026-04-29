import unittest

from src.utility import (
    generate_range_list,
    parse_matlab_array_input,
    sort_lists_by_first,
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

    def test_sort_lists_by_first(self):
        """Test the sort_lists_by_first function."""
        list1 = [3, 1, 2]
        list2 = ["c", "a", "b"]
        list3 = [True, False, True]
        sorted_lists = sort_lists_by_first(list1, list2, list3)
        self.assertEqual(
            sorted_lists, [[1, 2, 3], ["a", "b", "c"], [False, True, True]]
        )


if __name__ == "__main__":
    unittest.main()
