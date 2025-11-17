"""
Request status tracking for M5 Clipping Service.

Development: In-memory storage (thread-safe)
Production: Can be extended to use BigQuery or Cloud SQL
"""

import threading
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict, field


@dataclass
class ClipRequest:
    """Represents a clipping request and its status."""
    request_id: str
    hand_id: str
    nas_video_path: str
    start_seconds: float
    end_seconds: float
    status: str  # queued, processing, completed, failed
    output_quality: str = 'high'
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output_gcs_path: Optional[str] = None
    download_url: Optional[str] = None
    download_url_expires_at: Optional[str] = None
    file_size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    processing_time_seconds: Optional[int] = None
    progress_percent: Optional[int] = None
    error_message: Optional[str] = None
    queue_position: Optional[int] = None
    estimated_duration_sec: int = 45

    def to_dict(self) -> Dict:
        """Convert to dictionary, excluding None values."""
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}


class StatusTracker:
    """Thread-safe in-memory status tracker."""

    def __init__(self):
        self._requests: Dict[str, ClipRequest] = {}
        self._lock = threading.RLock()

    def create_request(
        self,
        request_id: str,
        hand_id: str,
        nas_video_path: str,
        start_seconds: float,
        end_seconds: float,
        output_quality: str = 'high'
    ) -> ClipRequest:
        """Create a new clipping request."""
        with self._lock:
            if request_id in self._requests:
                raise ValueError(f"Request {request_id} already exists")

            request = ClipRequest(
                request_id=request_id,
                hand_id=hand_id,
                nas_video_path=nas_video_path,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
                output_quality=output_quality,
                status='queued',
                queue_position=self._get_queue_depth() + 1
            )

            self._requests[request_id] = request
            return request

    def get_request(self, request_id: str) -> Optional[ClipRequest]:
        """Get request by ID."""
        with self._lock:
            return self._requests.get(request_id)

    def update_status(
        self,
        request_id: str,
        status: str,
        **kwargs
    ) -> Optional[ClipRequest]:
        """Update request status and optional fields."""
        with self._lock:
            request = self._requests.get(request_id)
            if not request:
                return None

            request.status = status

            # Update timestamps based on status
            if status == 'processing' and not request.started_at:
                request.started_at = datetime.utcnow().isoformat() + 'Z'
            elif status in ('completed', 'failed'):
                request.completed_at = datetime.utcnow().isoformat() + 'Z'

                # Calculate processing time
                if request.started_at:
                    started = datetime.fromisoformat(request.started_at.replace('Z', ''))
                    completed = datetime.fromisoformat(request.completed_at.replace('Z', ''))
                    request.processing_time_seconds = int((completed - started).total_seconds())

            # Update additional fields
            for key, value in kwargs.items():
                if hasattr(request, key):
                    setattr(request, key, value)

            return request

    def get_all_requests(self, limit: int = 100) -> List[ClipRequest]:
        """Get all requests, ordered by creation time (newest first)."""
        with self._lock:
            requests = sorted(
                self._requests.values(),
                key=lambda r: r.created_at,
                reverse=True
            )
            return requests[:limit]

    def get_requests_by_status(self, status: str) -> List[ClipRequest]:
        """Get all requests with a specific status."""
        with self._lock:
            return [r for r in self._requests.values() if r.status == status]

    def _get_queue_depth(self) -> int:
        """Get number of queued requests."""
        return len([r for r in self._requests.values() if r.status == 'queued'])

    def get_queue_depth(self) -> int:
        """Get current queue depth (public method)."""
        with self._lock:
            return self._get_queue_depth()

    def get_stats(self, period_hours: int = 24) -> Dict:
        """Get clipping statistics for a time period."""
        with self._lock:
            cutoff_time = datetime.utcnow().timestamp() - (period_hours * 3600)

            recent_requests = [
                r for r in self._requests.values()
                if datetime.fromisoformat(r.created_at.replace('Z', '')).timestamp() > cutoff_time
            ]

            total = len(recent_requests)
            completed = len([r for r in recent_requests if r.status == 'completed'])
            failed = len([r for r in recent_requests if r.status == 'failed'])
            queued = len([r for r in recent_requests if r.status == 'queued'])

            # Calculate average processing time
            processing_times = [
                r.processing_time_seconds
                for r in recent_requests
                if r.processing_time_seconds is not None
            ]
            avg_processing_time = (
                sum(processing_times) / len(processing_times)
                if processing_times else 0
            )

            # Calculate p95 processing time
            if processing_times:
                sorted_times = sorted(processing_times)
                p95_index = int(len(sorted_times) * 0.95)
                p95_processing_time = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
            else:
                p95_processing_time = 0

            # Calculate total output bytes
            total_output_bytes = sum(
                r.file_size_bytes or 0
                for r in recent_requests
                if r.file_size_bytes
            )

            return {
                'period': f'{period_hours}h',
                'total_requests': total,
                'completed': completed,
                'failed': failed,
                'queued': queued,
                'success_rate': completed / total if total > 0 else 0,
                'avg_processing_time_sec': round(avg_processing_time, 1),
                'p95_processing_time_sec': p95_processing_time,
                'total_output_bytes': total_output_bytes
            }

    def clear_old_requests(self, hours: int = 168):
        """Clear requests older than specified hours (default 7 days)."""
        with self._lock:
            cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)

            old_request_ids = [
                request_id
                for request_id, request in self._requests.items()
                if datetime.fromisoformat(request.created_at.replace('Z', '')).timestamp() < cutoff_time
            ]

            for request_id in old_request_ids:
                del self._requests[request_id]

            return len(old_request_ids)


# Global tracker instance
_tracker = StatusTracker()


def get_tracker() -> StatusTracker:
    """Get the global status tracker instance."""
    return _tracker
