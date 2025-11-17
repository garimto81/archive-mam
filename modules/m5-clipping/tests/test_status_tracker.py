"""
Tests for status tracker.

Tests request creation, status updates, and statistics.
"""

import pytest
from datetime import datetime

from app.status_tracker import StatusTracker, ClipRequest


@pytest.fixture
def tracker():
    """Create fresh tracker instance."""
    tracker = StatusTracker()
    tracker._requests.clear()
    return tracker


class TestClipRequest:
    """Tests for ClipRequest dataclass."""

    def test_create_clip_request(self):
        """Test creating a clip request."""
        request = ClipRequest(
            request_id='clip-20241117-001',
            hand_id='test_hand',
            nas_video_path='/nas/test.mp4',
            start_seconds=10.0,
            end_seconds=60.0,
            status='queued'
        )

        assert request.request_id == 'clip-20241117-001'
        assert request.hand_id == 'test_hand'
        assert request.status == 'queued'
        assert request.output_quality == 'high'  # default

    def test_to_dict(self):
        """Test converting request to dictionary."""
        request = ClipRequest(
            request_id='clip-20241117-001',
            hand_id='test_hand',
            nas_video_path='/nas/test.mp4',
            start_seconds=10.0,
            end_seconds=60.0,
            status='queued'
        )

        data = request.to_dict()

        assert isinstance(data, dict)
        assert 'request_id' in data
        assert 'hand_id' in data
        assert 'status' in data
        # None values should be excluded
        assert 'error_message' not in data


class TestStatusTracker:
    """Tests for StatusTracker class."""

    def test_create_request(self, tracker):
        """Test creating a new request."""
        request = tracker.create_request(
            request_id='clip-20241117-001',
            hand_id='test_hand',
            nas_video_path='/nas/test.mp4',
            start_seconds=0,
            end_seconds=10
        )

        assert request.request_id == 'clip-20241117-001'
        assert request.status == 'queued'
        assert request.queue_position == 1

    def test_create_duplicate_request(self, tracker):
        """Test that duplicate request_id raises error."""
        tracker.create_request(
            request_id='clip-20241117-001',
            hand_id='test_hand',
            nas_video_path='/nas/test.mp4',
            start_seconds=0,
            end_seconds=10
        )

        with pytest.raises(ValueError):
            tracker.create_request(
                request_id='clip-20241117-001',
                hand_id='test_hand_2',
                nas_video_path='/nas/test2.mp4',
                start_seconds=0,
                end_seconds=10
            )

    def test_get_request(self, tracker):
        """Test getting a request by ID."""
        created = tracker.create_request(
            request_id='clip-20241117-001',
            hand_id='test_hand',
            nas_video_path='/nas/test.mp4',
            start_seconds=0,
            end_seconds=10
        )

        retrieved = tracker.get_request('clip-20241117-001')

        assert retrieved is created
        assert retrieved.request_id == 'clip-20241117-001'

    def test_get_nonexistent_request(self, tracker):
        """Test getting a non-existent request."""
        request = tracker.get_request('nonexistent')
        assert request is None

    def test_update_status_to_processing(self, tracker):
        """Test updating status to processing."""
        tracker.create_request(
            request_id='clip-20241117-001',
            hand_id='test_hand',
            nas_video_path='/nas/test.mp4',
            start_seconds=0,
            end_seconds=10
        )

        updated = tracker.update_status(
            'clip-20241117-001',
            status='processing',
            progress_percent=50
        )

        assert updated.status == 'processing'
        assert updated.progress_percent == 50
        assert updated.started_at is not None

    def test_update_status_to_completed(self, tracker):
        """Test updating status to completed."""
        tracker.create_request(
            request_id='clip-20241117-001',
            hand_id='test_hand',
            nas_video_path='/nas/test.mp4',
            start_seconds=0,
            end_seconds=10
        )

        # First set to processing
        tracker.update_status('clip-20241117-001', status='processing')

        # Then complete
        updated = tracker.update_status(
            'clip-20241117-001',
            status='completed',
            output_gcs_path='gs://bucket/test.mp4',
            file_size_bytes=1024000
        )

        assert updated.status == 'completed'
        assert updated.output_gcs_path == 'gs://bucket/test.mp4'
        assert updated.file_size_bytes == 1024000
        assert updated.completed_at is not None
        assert updated.processing_time_seconds is not None

    def test_update_status_to_failed(self, tracker):
        """Test updating status to failed."""
        tracker.create_request(
            request_id='clip-20241117-001',
            hand_id='test_hand',
            nas_video_path='/nas/test.mp4',
            start_seconds=0,
            end_seconds=10
        )

        updated = tracker.update_status(
            'clip-20241117-001',
            status='failed',
            error_message='FFmpeg error: invalid codec'
        )

        assert updated.status == 'failed'
        assert updated.error_message == 'FFmpeg error: invalid codec'
        assert updated.completed_at is not None

    def test_get_all_requests(self, tracker):
        """Test getting all requests."""
        for i in range(5):
            tracker.create_request(
                request_id=f'clip-20241117-{i:03d}',
                hand_id=f'hand_{i}',
                nas_video_path='/nas/test.mp4',
                start_seconds=0,
                end_seconds=10
            )

        all_requests = tracker.get_all_requests()

        assert len(all_requests) == 5
        # Should be ordered by creation time (newest first)
        assert all_requests[0].request_id == 'clip-20241117-004'

    def test_get_all_requests_with_limit(self, tracker):
        """Test getting requests with limit."""
        for i in range(10):
            tracker.create_request(
                request_id=f'clip-20241117-{i:03d}',
                hand_id=f'hand_{i}',
                nas_video_path='/nas/test.mp4',
                start_seconds=0,
                end_seconds=10
            )

        requests = tracker.get_all_requests(limit=5)

        assert len(requests) == 5

    def test_get_requests_by_status(self, tracker):
        """Test getting requests by status."""
        # Create some requests with different statuses
        for i in range(5):
            tracker.create_request(
                request_id=f'clip-20241117-{i:03d}',
                hand_id=f'hand_{i}',
                nas_video_path='/nas/test.mp4',
                start_seconds=0,
                end_seconds=10
            )

        # Update some to different statuses
        tracker.update_status('clip-20241117-000', 'completed')
        tracker.update_status('clip-20241117-001', 'completed')
        tracker.update_status('clip-20241117-002', 'failed')

        # Get by status
        completed = tracker.get_requests_by_status('completed')
        failed = tracker.get_requests_by_status('failed')
        queued = tracker.get_requests_by_status('queued')

        assert len(completed) == 2
        assert len(failed) == 1
        assert len(queued) == 2

    def test_get_queue_depth(self, tracker):
        """Test getting queue depth."""
        # Create queued requests
        for i in range(3):
            tracker.create_request(
                request_id=f'clip-20241117-{i:03d}',
                hand_id=f'hand_{i}',
                nas_video_path='/nas/test.mp4',
                start_seconds=0,
                end_seconds=10
            )

        assert tracker.get_queue_depth() == 3

        # Complete one
        tracker.update_status('clip-20241117-000', 'completed')
        assert tracker.get_queue_depth() == 2

    def test_get_stats(self, tracker):
        """Test getting statistics."""
        # Create requests
        for i in range(10):
            tracker.create_request(
                request_id=f'clip-20241117-{i:03d}',
                hand_id=f'hand_{i}',
                nas_video_path='/nas/test.mp4',
                start_seconds=0,
                end_seconds=10
            )

        # Update statuses
        for i in range(7):
            tracker.update_status(f'clip-20241117-{i:03d}', 'processing')
            tracker.update_status(
                f'clip-20241117-{i:03d}',
                'completed',
                file_size_bytes=1024000,
                processing_time_seconds=30 + i  # Variable processing times
            )

        tracker.update_status('clip-20241117-007', 'failed')
        tracker.update_status('clip-20241117-008', 'failed')

        # Get stats
        stats = tracker.get_stats(period_hours=24)

        assert stats['total_requests'] == 10
        assert stats['completed'] == 7
        assert stats['failed'] == 2
        assert stats['queued'] == 1
        assert stats['success_rate'] == 0.7
        assert stats['avg_processing_time_sec'] > 0
        assert stats['p95_processing_time_sec'] > 0
        assert stats['total_output_bytes'] == 7 * 1024000

    def test_clear_old_requests(self, tracker):
        """Test clearing old requests."""
        # Create some requests
        for i in range(5):
            tracker.create_request(
                request_id=f'clip-20241117-{i:03d}',
                hand_id=f'hand_{i}',
                nas_video_path='/nas/test.mp4',
                start_seconds=0,
                end_seconds=10
            )

        # Clear requests older than 0 hours (all of them)
        cleared = tracker.clear_old_requests(hours=0)

        assert cleared == 5
        assert len(tracker._requests) == 0

    def test_thread_safety(self, tracker):
        """Test thread-safe operations."""
        import threading

        def create_requests():
            for i in range(10):
                try:
                    tracker.create_request(
                        request_id=f'clip-{threading.current_thread().name}-{i:03d}',
                        hand_id=f'hand_{i}',
                        nas_video_path='/nas/test.mp4',
                        start_seconds=0,
                        end_seconds=10
                    )
                except ValueError:
                    pass  # Duplicate ID, expected in concurrent test

        threads = [threading.Thread(target=create_requests, name=f'T{i}') for i in range(3)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should have created some requests without crashing
        assert len(tracker._requests) > 0
