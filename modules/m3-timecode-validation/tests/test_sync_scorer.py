"""
Unit tests for sync_score calculation
"""
import unittest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.sync_scorer import SyncScorer


class TestSyncScorer(unittest.TestCase):
    """Test cases for SyncScorer"""

    def setUp(self):
        """Set up test fixtures"""
        self.scorer = SyncScorer()

    def test_perfect_sync_score(self):
        """Test perfect synchronization (all components match)"""
        hand_metadata = {
            'hand_id': 'test_hand_001',
            'duration_seconds': 150,
            'players': ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']
        }

        video_metadata = {
            'video_id': 'test_video_001',
            'duration_seconds': 150
        }

        vision_confidence = 0.95
        detected_player_count = 6

        result = self.scorer.calculate_sync_score(
            hand_metadata,
            video_metadata,
            vision_confidence,
            detected_player_count
        )

        # Perfect sync should be near 100
        self.assertGreaterEqual(result['sync_score'], 95.0)
        self.assertTrue(result['is_synced'])
        self.assertEqual(result['vision_confidence'], 0.95)
        self.assertEqual(result['duration_match'], 1.0)
        self.assertEqual(result['player_count_match'], 1.0)

    def test_good_sync_score(self):
        """Test good synchronization (minor differences)"""
        hand_metadata = {
            'duration_seconds': 150,
            'players': ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']
        }

        video_metadata = {
            'duration_seconds': 155  # 3.3% difference
        }

        vision_confidence = 0.88
        detected_player_count = 7  # 1 player difference

        result = self.scorer.calculate_sync_score(
            hand_metadata,
            video_metadata,
            vision_confidence,
            detected_player_count
        )

        # Should be good sync (80-90)
        self.assertGreaterEqual(result['sync_score'], 80.0)
        self.assertLess(result['sync_score'], 95.0)
        self.assertTrue(result['is_synced'])

    def test_needs_offset_sync_score(self):
        """Test sync that needs offset correction"""
        hand_metadata = {
            'duration_seconds': 150,
            'players': ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']
        }

        video_metadata = {
            'duration_seconds': 180  # 20% difference
        }

        vision_confidence = 0.75
        detected_player_count = 8  # 2 player difference

        result = self.scorer.calculate_sync_score(
            hand_metadata,
            video_metadata,
            vision_confidence,
            detected_player_count
        )

        # Should need offset (60-80)
        self.assertGreaterEqual(result['sync_score'], 60.0)
        self.assertLess(result['sync_score'], 80.0)
        self.assertFalse(result['is_synced'])
        self.assertIn('offset', result['recommendation'].lower())

    def test_poor_sync_score(self):
        """Test poor synchronization (manual matching needed)"""
        hand_metadata = {
            'duration_seconds': 150,
            'players': ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']
        }

        video_metadata = {
            'duration_seconds': 250  # 67% difference
        }

        vision_confidence = 0.40
        detected_player_count = 3  # 3 player difference

        result = self.scorer.calculate_sync_score(
            hand_metadata,
            video_metadata,
            vision_confidence,
            detected_player_count
        )

        # Should need manual matching (< 60)
        self.assertLess(result['sync_score'], 60.0)
        self.assertFalse(result['is_synced'])
        self.assertIn('manual', result['recommendation'].lower())

    def test_duration_match_calculation(self):
        """Test duration match score calculation"""
        # Perfect match
        score = self.scorer._calculate_duration_match(150, 150)
        self.assertEqual(score, 1.0)

        # Within 10% tolerance
        score = self.scorer._calculate_duration_match(150, 160)
        self.assertGreaterEqual(score, 0.9)

        # 20% difference
        score = self.scorer._calculate_duration_match(150, 180)
        self.assertGreater(score, 0.5)
        self.assertLess(score, 1.0)

        # 50%+ difference
        score = self.scorer._calculate_duration_match(150, 250)
        self.assertEqual(score, 0.0)

    def test_player_count_match_calculation(self):
        """Test player count match score calculation"""
        hand_players = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']

        # Perfect match
        score = self.scorer._calculate_player_count_match(hand_players, 6)
        self.assertEqual(score, 1.0)

        # Within tolerance (±1)
        score = self.scorer._calculate_player_count_match(hand_players, 7)
        self.assertGreaterEqual(score, 0.7)

        # Within tolerance (±2)
        score = self.scorer._calculate_player_count_match(hand_players, 8)
        self.assertGreaterEqual(score, 0.5)

        # Beyond tolerance
        score = self.scorer._calculate_player_count_match(hand_players, 10)
        self.assertLess(score, 0.5)

    def test_zero_duration_handling(self):
        """Test handling of zero/invalid duration"""
        hand_metadata = {
            'duration_seconds': 0,
            'players': []
        }

        video_metadata = {
            'duration_seconds': 150
        }

        result = self.scorer.calculate_sync_score(
            hand_metadata,
            video_metadata,
            0.9,
            6
        )

        # Duration match should be 0
        self.assertEqual(result['duration_match'], 0.0)
        # But vision and player scores should work
        self.assertGreater(result['vision_confidence'], 0.0)

    def test_no_player_data_handling(self):
        """Test handling of missing player data"""
        hand_metadata = {
            'duration_seconds': 150,
            'players': []
        }

        video_metadata = {
            'duration_seconds': 150
        }

        result = self.scorer.calculate_sync_score(
            hand_metadata,
            video_metadata,
            0.9,
            0
        )

        # Player count match should be neutral (0.5)
        self.assertEqual(result['player_count_match'], 0.5)


if __name__ == '__main__':
    unittest.main()
