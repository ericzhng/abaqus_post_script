import os
import unittest

from src.abaqus_post.common import get_file_path
from src.preprocess import load_config


class TestGetFilePath(unittest.TestCase):
    """Test cases for the get_file_path function."""

    def setUp(self):
        """Load the configuration for testing."""
        self.project_root = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".."
        )
        self.config = load_config(self.project_root)

    def test_get_file_path_success_with_key(self):
        """Test successful file path retrieval using a file name key."""
        file_paths = get_file_path(
            "10000", self.config, file_name_key="uamp_properties"
        )

        self.assertTrue(os.path.exists(file_paths[0]))
        self.assertEqual(os.path.basename(file_paths[0]), "uamp-properties.dat")

    def test_get_file_path_success_with_name(self):
        """Test successful file path retrieval using a file name."""
        file_paths = get_file_path(
            "10000", self.config, file_name="uamp-properties.dat"
        )
        self.assertTrue(os.path.exists(file_paths[0]))
        self.assertEqual(os.path.basename(file_paths[0]), "uamp-properties.dat")

    def test_get_file_path_not_found(self):
        """Test that IOError is raised for a nonexistent file."""
        with self.assertRaises(IOError):
            get_file_path("10000", self.config, file_name="nonexistent.file")

    def test_get_file_path_no_name_or_key(self):
        """Test that ValueError is raised if no file name or key is provided."""
        with self.assertRaises(ValueError):
            get_file_path("10000", self.config)


if __name__ == "__main__":
    unittest.main()
