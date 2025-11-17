"""
Unit tests for Flask API endpoints
"""
import unittest
import json
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api import app


class TestAPI(unittest.TestCase):
    """Test cases for Flask API"""

    def setUp(self):
        """Set up test client"""
        self.app = app
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True

    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/health')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('dependencies', data)
        self.assertIn('version', data)

    def test_validate_missing_fields(self):
        """Test validation with missing required fields"""
        payload = {
            'hand_id': 'test_hand_001'
            # Missing other required fields
        }

        response = self.client.post(
            '/v1/validate',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('MISSING_FIELD', data['error']['code'])

    def test_validate_success(self):
        """Test successful validation request"""
        payload = {
            'hand_id': 'wsop2024_me_d3_h154',
            'timestamp_start_utc': '2024-07-15T15:24:15Z',
            'timestamp_end_utc': '2024-07-15T15:26:45Z',
            'nas_video_path': '/nas/poker/2024/wsop/main_event_day3.mp4',
            'use_vision_api': False  # Disable for faster test
        }

        response = self.client.post(
            '/v1/validate',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('validation_id', data)
        self.assertIn('hand_id', data)
        self.assertIn('status', data)
        self.assertEqual(data['hand_id'], payload['hand_id'])

    def test_get_validation_result_not_found(self):
        """Test getting result for non-existent validation"""
        response = self.client.get('/v1/validate/invalid_id/result')

        self.assertEqual(response.status_code, 404)

        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('NOT_FOUND', data['error']['code'])

    def test_batch_validate_missing_hand_ids(self):
        """Test batch validation with missing hand_ids"""
        payload = {
            'use_vision_api': True
        }

        response = self.client.post(
            '/v1/validate/batch',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_batch_validate_too_many_hands(self):
        """Test batch validation with too many hands"""
        payload = {
            'hand_ids': [f'hand_{i}' for i in range(1001)],  # 1001 hands
            'use_vision_api': False
        }

        response = self.client.post(
            '/v1/validate/batch',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertIn('TOO_MANY_HANDS', data['error']['code'])

    def test_batch_validate_success(self):
        """Test successful batch validation"""
        payload = {
            'hand_ids': ['hand_001', 'hand_002', 'hand_003'],
            'use_vision_api': False,
            'auto_apply_offset': False
        }

        response = self.client.post(
            '/v1/validate/batch',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('batch_id', data)
        self.assertIn('total_hands', data)
        self.assertEqual(data['total_hands'], 3)
        self.assertIn('status', data)

    def test_manual_match_missing_fields(self):
        """Test manual matching with missing fields"""
        payload = {
            'hand_id': 'test_hand_001'
        }

        response = self.client.post(
            '/v1/manual/match',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_manual_match_invalid_timecode(self):
        """Test manual matching with invalid timecode format"""
        payload = {
            'hand_id': 'wsop2024_me_d3_h154',
            'matched_video_timecode': 'invalid',
            'matched_by_user': 'test@example.com'
        }

        response = self.client.post(
            '/v1/manual/match',
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Should return 400 or 404 (depending on hand existence)
        self.assertIn(response.status_code, [400, 404])

    def test_get_sync_scores(self):
        """Test getting sync scores"""
        response = self.client.get('/v1/sync-scores')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('sync_scores', data)
        self.assertIn('total', data)
        self.assertIsInstance(data['sync_scores'], list)

    def test_get_sync_scores_with_filters(self):
        """Test getting sync scores with filters"""
        response = self.client.get('/v1/sync-scores?event_id=wsop2024_me&min_score=80')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('sync_scores', data)

    def test_get_offsets(self):
        """Test getting offsets"""
        response = self.client.get('/v1/offsets')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('offsets', data)
        self.assertIn('total', data)
        self.assertIsInstance(data['offsets'], list)

    def test_get_offsets_needs_offset_filter(self):
        """Test getting offsets with needs_offset filter"""
        response = self.client.get('/v1/offsets?needs_offset=true')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('offsets', data)

    def test_get_stats(self):
        """Test getting validation statistics"""
        response = self.client.get('/v1/stats')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        # Check for expected stats fields (from mock data)
        self.assertIn('total_hands', data)
        self.assertIn('validated_hands', data)
        self.assertIn('avg_sync_score', data)

    def test_get_stats_with_event_filter(self):
        """Test getting stats filtered by event_id"""
        response = self.client.get('/v1/stats?event_id=wsop2024_me')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('total_hands', data)


if __name__ == '__main__':
    unittest.main()
