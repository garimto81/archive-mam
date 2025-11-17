"""
Unit tests for Vision API detector (using mock)
"""
import unittest

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.vision_detector import MockVisionDetector


class TestVisionDetector(unittest.TestCase):
    """Test cases for Vision Detector (using mock)"""

    def setUp(self):
        """Set up test fixtures"""
        self.detector = MockVisionDetector()

    def test_detect_poker_scene_valid(self):
        """Test poker scene detection with valid frame"""
        gcs_path = "gs://test-bucket/valid_poker_frame.jpg"

        confidence, objects = self.detector.detect_poker_scene(gcs_path)

        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        self.assertIsInstance(objects, list)
        # Should detect poker-related objects
        self.assertGreater(len(objects), 0)

    def test_detect_poker_scene_partial(self):
        """Test poker scene detection with partial match"""
        gcs_path = "gs://test-bucket/partial_poker_frame.jpg"

        confidence, objects = self.detector.detect_poker_scene(gcs_path)

        # Partial match should have lower confidence
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLess(confidence, 1.0)

    def test_detect_player_count(self):
        """Test player count detection"""
        gcs_path = "gs://test-bucket/poker_table.jpg"

        player_count = self.detector.detect_player_count(gcs_path)

        # Should return reasonable player count (6-9 for poker)
        self.assertGreaterEqual(player_count, 0)
        self.assertLessEqual(player_count, 10)

    def test_upload_frame_to_gcs(self):
        """Test frame upload to GCS"""
        local_path = "/tmp/test_frame.jpg"
        blob_name = "validation-frames/test_001.jpg"

        gcs_uri = self.detector.upload_frame_to_gcs(local_path, blob_name)

        # Should return valid GCS URI
        self.assertTrue(gcs_uri.startswith('gs://'))
        self.assertIn(blob_name, gcs_uri)


if __name__ == '__main__':
    unittest.main()
