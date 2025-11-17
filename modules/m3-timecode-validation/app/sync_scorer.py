"""
sync_score Calculation Algorithm
Formula: vision_confidence * 50 + duration_match * 30 + player_count * 20
"""
import logging
from typing import Dict, Any

from . import config

logger = logging.getLogger(__name__)


class SyncScorer:
    """
    Calculate synchronization score between hand and video
    """

    def __init__(self):
        self.weights = config.SYNC_SCORE_WEIGHTS
        logger.info(f"SyncScorer initialized with weights: {self.weights}")

    def calculate_sync_score(
        self,
        hand_metadata: Dict[str, Any],
        video_metadata: Dict[str, Any],
        vision_confidence: float,
        detected_player_count: int = 0
    ) -> Dict[str, Any]:
        """
        Calculate sync_score for hand-video pair

        Args:
            hand_metadata: Hand metadata from BigQuery
            video_metadata: Video metadata from BigQuery
            vision_confidence: Vision API confidence (0.0-1.0)
            detected_player_count: Number of players detected by Vision API

        Returns:
            {
                'sync_score': 0-100,
                'vision_confidence': 0-1,
                'duration_match': 0-1,
                'player_count_match': 0-1,
                'is_synced': bool,
                'recommendation': str
            }
        """

        # 1. Vision API confidence (50% weight)
        vision_score = vision_confidence

        # 2. Duration match (30% weight)
        duration_match = self._calculate_duration_match(
            hand_metadata.get('duration_seconds', 0),
            video_metadata.get('duration_seconds', 0)
        )

        # 3. Player count match (20% weight)
        player_count_match = self._calculate_player_count_match(
            hand_metadata.get('players', []),
            detected_player_count
        )

        # Calculate weighted sync_score
        sync_score = (
            vision_score * self.weights['vision'] +
            duration_match * self.weights['duration'] +
            player_count_match * self.weights['player_count']
        )

        # Round to 2 decimal places
        sync_score = round(sync_score, 2)

        # Determine sync status
        is_synced = sync_score >= config.GOOD_SYNC_THRESHOLD
        recommendation = self._get_recommendation(sync_score)

        result = {
            'sync_score': sync_score,
            'vision_confidence': round(vision_score, 2),
            'duration_match': round(duration_match, 2),
            'player_count_match': round(player_count_match, 2),
            'is_synced': is_synced,
            'recommendation': recommendation
        }

        logger.info(
            f"Calculated sync_score: {sync_score:.2f} "
            f"(vision={vision_score:.2f}, duration={duration_match:.2f}, "
            f"player={player_count_match:.2f})"
        )

        return result

    def _calculate_duration_match(
        self,
        hand_duration: float,
        video_duration: float
    ) -> float:
        """
        Calculate duration match score (0.0-1.0)

        Allows ±10% tolerance
        """
        if hand_duration <= 0 or video_duration <= 0:
            logger.warning(f"Invalid duration: hand={hand_duration}, video={video_duration}")
            return 0.0

        # Calculate percentage difference
        duration_diff = abs(hand_duration - video_duration)
        duration_ratio = duration_diff / hand_duration

        # Score decreases linearly from 1.0 (perfect match) to 0.0 (>50% diff)
        if duration_ratio <= 0.1:
            # Within 10% tolerance: perfect score
            match_score = 1.0
        elif duration_ratio >= 0.5:
            # More than 50% difference: zero score
            match_score = 0.0
        else:
            # Linear interpolation between 10% and 50%
            match_score = 1.0 - ((duration_ratio - 0.1) / 0.4)

        logger.debug(
            f"Duration match: hand={hand_duration}s, video={video_duration}s, "
            f"diff={duration_ratio:.1%}, score={match_score:.2f}"
        )

        return match_score

    def _calculate_player_count_match(
        self,
        hand_players: list,
        detected_player_count: int
    ) -> float:
        """
        Calculate player count match score (0.0-1.0)

        Allows ±2 players tolerance
        """
        if not hand_players:
            logger.warning("No hand players data available")
            return 0.5  # Neutral score when data unavailable

        hand_player_count = len(hand_players)

        if detected_player_count == 0:
            logger.warning("No players detected by Vision API")
            return 0.5  # Neutral score when Vision API fails

        # Calculate difference
        player_diff = abs(hand_player_count - detected_player_count)

        # Score decreases with difference
        if player_diff == 0:
            # Perfect match
            match_score = 1.0
        elif player_diff <= 2:
            # Within tolerance (±2 players)
            match_score = 1.0 - (player_diff * 0.25)  # 0.75 for ±1, 0.5 for ±2
        else:
            # Beyond tolerance
            match_score = max(0.0, 0.5 - ((player_diff - 2) * 0.1))

        logger.debug(
            f"Player count match: hand={hand_player_count}, detected={detected_player_count}, "
            f"diff={player_diff}, score={match_score:.2f}"
        )

        return match_score

    def _get_recommendation(self, sync_score: float) -> str:
        """
        Get recommendation based on sync_score

        Args:
            sync_score: Calculated sync score (0-100)

        Returns:
            Recommendation string
        """
        if sync_score >= config.PERFECT_SYNC_THRESHOLD:
            return "Perfect sync - ready for production"
        elif sync_score >= config.GOOD_SYNC_THRESHOLD:
            return "Good sync - acceptable for use"
        elif sync_score >= config.NEEDS_OFFSET_THRESHOLD:
            return "Needs offset calculation - auto-correction recommended"
        else:
            return "Manual matching required - sync_score too low"
