"""
Timecode Offset Calculator
Calculates time offset between ATI timestamp and NAS video timecode
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from . import config

logger = logging.getLogger(__name__)


class OffsetCalculator:
    """
    Calculate timecode offset for sync improvement
    """

    def __init__(self):
        logger.info("OffsetCalculator initialized")

    def calculate_offset(
        self,
        hand_metadata: Dict[str, Any],
        video_metadata: Dict[str, Any],
        sync_score: float
    ) -> Dict[str, Any]:
        """
        Calculate offset between hand timestamp and video timecode

        Args:
            hand_metadata: Hand metadata
            video_metadata: Video metadata
            sync_score: Current sync score

        Returns:
            {
                'offset_seconds': float,
                'offset_reason': str,
                'needs_offset': bool
            }
        """

        # Check if offset is needed
        needs_offset = sync_score < config.GOOD_SYNC_THRESHOLD

        if not needs_offset:
            logger.info(f"sync_score {sync_score:.2f} is good, no offset needed")
            return {
                'offset_seconds': 0.0,
                'offset_reason': None,
                'needs_offset': False
            }

        # Calculate duration-based offset
        hand_duration = hand_metadata.get('duration_seconds', 0)
        video_duration = video_metadata.get('duration_seconds', 0)

        if hand_duration <= 0 or video_duration <= 0:
            logger.warning("Invalid duration for offset calculation")
            return {
                'offset_seconds': 0.0,
                'offset_reason': 'Invalid duration data',
                'needs_offset': True
            }

        # Calculate offset based on duration mismatch
        duration_diff = video_duration - hand_duration

        # Offset estimation logic:
        # - If video is longer: likely started earlier (negative offset)
        # - If video is shorter: likely started later (positive offset)
        estimated_offset = -duration_diff / 2.0  # Assume offset is half the difference

        offset_reason = self._determine_offset_reason(
            duration_diff,
            sync_score
        )

        result = {
            'offset_seconds': round(estimated_offset, 2),
            'offset_reason': offset_reason,
            'needs_offset': True
        }

        logger.info(
            f"Calculated offset: {estimated_offset:.2f}s, reason: {offset_reason}"
        )

        return result

    def _determine_offset_reason(
        self,
        duration_diff: float,
        sync_score: float
    ) -> str:
        """
        Determine reason for offset calculation

        Args:
            duration_diff: Difference in duration (video - hand)
            sync_score: Current sync score

        Returns:
            Reason string
        """
        reasons = []

        if abs(duration_diff) > 30:
            if duration_diff > 0:
                reasons.append(f"Video started {abs(duration_diff):.1f}s earlier")
            else:
                reasons.append(f"Video started {abs(duration_diff):.1f}s later")

        if sync_score < config.NEEDS_OFFSET_THRESHOLD:
            reasons.append("Low sync score requires offset correction")

        if not reasons:
            reasons.append("Duration mismatch detected")

        return "; ".join(reasons)

    def apply_offset(
        self,
        timestamp_utc: datetime,
        offset_seconds: float
    ) -> datetime:
        """
        Apply offset to timestamp

        Args:
            timestamp_utc: Original timestamp
            offset_seconds: Offset to apply (seconds)

        Returns:
            Adjusted timestamp
        """
        adjusted_timestamp = timestamp_utc + timedelta(seconds=offset_seconds)

        logger.debug(
            f"Applied offset {offset_seconds:.2f}s: "
            f"{timestamp_utc.isoformat()} -> {adjusted_timestamp.isoformat()}"
        )

        return adjusted_timestamp

    def calculate_manual_offset(
        self,
        hand_timestamp_utc: datetime,
        matched_video_timecode: str
    ) -> float:
        """
        Calculate offset from manual matching

        Args:
            hand_timestamp_utc: ATI hand timestamp
            matched_video_timecode: User-matched video timecode (HH:MM:SS)

        Returns:
            Calculated offset in seconds
        """
        # Parse video timecode (HH:MM:SS)
        try:
            time_parts = matched_video_timecode.split(':')
            hours = int(time_parts[0])
            minutes = int(time_parts[1])
            seconds = int(time_parts[2])

            video_seconds = hours * 3600 + minutes * 60 + seconds

            # Offset = video_timecode - hand_timestamp
            # (Negative offset means video is behind hand timestamp)
            hand_seconds = (
                hand_timestamp_utc.hour * 3600 +
                hand_timestamp_utc.minute * 60 +
                hand_timestamp_utc.second
            )

            offset = video_seconds - hand_seconds

            logger.info(
                f"Manual offset calculated: {offset:.2f}s "
                f"(video={matched_video_timecode}, hand={hand_timestamp_utc.time()})"
            )

            return float(offset)

        except (ValueError, IndexError) as e:
            logger.error(f"Failed to parse video timecode: {e}")
            raise ValueError(f"Invalid video timecode format: {matched_video_timecode}")
