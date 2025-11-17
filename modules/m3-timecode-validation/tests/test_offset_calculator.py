"""
Unit tests for offset calculation
"""
import unittest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.offset_calculator import OffsetCalculator


class TestOffsetCalculator(unittest.TestCase):
    """Test cases for OffsetCalculator"""

    def setUp(self):
        """Set up test fixtures"""
        self.calculator = OffsetCalculator()

    def test_no_offset_needed_high_score(self):
        """Test that high sync_score doesn't trigger offset calculation"""
        hand_metadata = {
            'duration_seconds': 150
        }

        video_metadata = {
            'duration_seconds': 150
        }

        result = self.calculator.calculate_offset(
            hand_metadata,
            video_metadata,
            sync_score=92.5
        )

        self.assertFalse(result['needs_offset'])
        self.assertEqual(result['offset_seconds'], 0.0)
        self.assertIsNone(result['offset_reason'])

    def test_offset_needed_low_score(self):
        """Test offset calculation for low sync_score"""
        hand_metadata = {
            'duration_seconds': 150
        }

        video_metadata = {
            'duration_seconds': 180  # 30 seconds longer
        }

        result = self.calculator.calculate_offset(
            hand_metadata,
            video_metadata,
            sync_score=65.0
        )

        self.assertTrue(result['needs_offset'])
        # Video is longer, so offset should be negative (video started earlier)
        self.assertLess(result['offset_seconds'], 0)
        self.assertIsNotNone(result['offset_reason'])

    def test_offset_calculation_video_longer(self):
        """Test offset when video is longer than hand"""
        hand_metadata = {
            'duration_seconds': 120
        }

        video_metadata = {
            'duration_seconds': 180  # 60 seconds longer
        }

        result = self.calculator.calculate_offset(
            hand_metadata,
            video_metadata,
            sync_score=70.0
        )

        # Offset should be approximately -30 (half of 60s difference)
        self.assertAlmostEqual(result['offset_seconds'], -30.0, delta=1.0)

    def test_offset_calculation_video_shorter(self):
        """Test offset when video is shorter than hand"""
        hand_metadata = {
            'duration_seconds': 180
        }

        video_metadata = {
            'duration_seconds': 120  # 60 seconds shorter
        }

        result = self.calculator.calculate_offset(
            hand_metadata,
            video_metadata,
            sync_score=70.0
        )

        # Offset should be approximately +30 (half of 60s difference)
        self.assertAlmostEqual(result['offset_seconds'], 30.0, delta=1.0)

    def test_manual_offset_calculation(self):
        """Test manual offset calculation from user-matched timecode"""
        # Hand timestamp: 15:24:15
        hand_timestamp = datetime(2024, 7, 15, 15, 24, 15)

        # User matched to video timecode: 03:24:15 (3 hours, 24 min, 15 sec)
        matched_timecode = "03:24:15"

        offset = self.calculator.calculate_manual_offset(
            hand_timestamp,
            matched_timecode
        )

        # Expected offset: (3*3600 + 24*60 + 15) - (15*3600 + 24*60 + 15)
        # = 12255 - 55455 = -43200 (12 hours difference)
        expected_offset = (3 * 3600 + 24 * 60 + 15) - (15 * 3600 + 24 * 60 + 15)
        self.assertEqual(offset, expected_offset)

    def test_manual_offset_same_time(self):
        """Test manual offset when timestamps match"""
        hand_timestamp = datetime(2024, 7, 15, 10, 30, 45)
        matched_timecode = "10:30:45"

        offset = self.calculator.calculate_manual_offset(
            hand_timestamp,
            matched_timecode
        )

        self.assertEqual(offset, 0.0)

    def test_invalid_timecode_format(self):
        """Test error handling for invalid timecode format"""
        hand_timestamp = datetime(2024, 7, 15, 15, 24, 15)

        with self.assertRaises(ValueError):
            self.calculator.calculate_manual_offset(hand_timestamp, "invalid")

        with self.assertRaises(ValueError):
            self.calculator.calculate_manual_offset(hand_timestamp, "15:24")  # Missing seconds

    def test_offset_reason_generation(self):
        """Test offset reason message generation"""
        reason = self.calculator._determine_offset_reason(
            duration_diff=45.0,
            sync_score=65.0
        )

        self.assertIsInstance(reason, str)
        self.assertGreater(len(reason), 0)
        # Should mention that video started earlier
        self.assertIn('earlier', reason.lower())

    def test_apply_offset_positive(self):
        """Test applying positive offset to timestamp"""
        original_timestamp = datetime(2024, 7, 15, 15, 24, 15)
        offset_seconds = 120.0  # +2 minutes

        adjusted_timestamp = self.calculator.apply_offset(
            original_timestamp,
            offset_seconds
        )

        expected_timestamp = datetime(2024, 7, 15, 15, 26, 15)
        self.assertEqual(adjusted_timestamp, expected_timestamp)

    def test_apply_offset_negative(self):
        """Test applying negative offset to timestamp"""
        original_timestamp = datetime(2024, 7, 15, 15, 24, 15)
        offset_seconds = -120.0  # -2 minutes

        adjusted_timestamp = self.calculator.apply_offset(
            original_timestamp,
            offset_seconds
        )

        expected_timestamp = datetime(2024, 7, 15, 15, 22, 15)
        self.assertEqual(adjusted_timestamp, expected_timestamp)


if __name__ == '__main__':
    unittest.main()
