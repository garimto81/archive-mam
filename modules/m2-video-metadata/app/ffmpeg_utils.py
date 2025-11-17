"""
FFmpeg utilities for metadata extraction
"""
import ffmpeg
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class FFmpegMetadataExtractor:
    """Extract video metadata using FFmpeg"""

    @staticmethod
    def extract_metadata(video_path: str) -> Dict:
        """
        Extract metadata from video file using FFmpeg

        Args:
            video_path: Path to video file

        Returns:
            Dictionary containing:
                - duration_seconds: Video duration in seconds
                - resolution: Video resolution (e.g., "1920x1080")
                - codec: Video codec name (e.g., "h264")
                - bitrate_kbps: Video bitrate in kbps
                - fps: Frames per second

        Raises:
            RuntimeError: If FFmpeg fails to probe the file
        """
        try:
            logger.info(f"Extracting metadata from {video_path}")

            # Probe video file
            probe = ffmpeg.probe(video_path)

            # Find video stream
            video_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'video'),
                None
            )

            if not video_stream:
                raise ValueError("No video stream found in file")

            # Extract duration
            duration = float(probe['format'].get('duration', 0))

            # Extract resolution
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            resolution = f"{width}x{height}"

            # Extract codec
            codec = video_stream.get('codec_name', 'unknown')

            # Extract bitrate (convert to kbps)
            bitrate = int(probe['format'].get('bit_rate', 0))
            bitrate_kbps = bitrate // 1000 if bitrate else 0

            # Extract FPS
            fps = FFmpegMetadataExtractor._calculate_fps(video_stream)

            metadata = {
                'duration_seconds': int(duration),
                'resolution': resolution,
                'codec': codec,
                'bitrate_kbps': bitrate_kbps,
                'fps': round(fps, 2),
            }

            logger.info(f"Metadata extracted: {metadata}")
            return metadata

        except ffmpeg.Error as e:
            stderr = e.stderr.decode('utf-8') if e.stderr else str(e)
            error_msg = f"FFmpeg error while probing {video_path}: {stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Error extracting metadata from {video_path}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    @staticmethod
    def _calculate_fps(video_stream: Dict) -> float:
        """
        Calculate FPS from video stream metadata

        Args:
            video_stream: FFmpeg video stream dictionary

        Returns:
            Frames per second as float
        """
        try:
            # Try r_frame_rate first (most accurate)
            if 'r_frame_rate' in video_stream:
                num, den = map(int, video_stream['r_frame_rate'].split('/'))
                if den > 0:
                    return num / den

            # Fallback to avg_frame_rate
            if 'avg_frame_rate' in video_stream:
                num, den = map(int, video_stream['avg_frame_rate'].split('/'))
                if den > 0:
                    return num / den

            # Default
            return 0.0
        except (ValueError, ZeroDivisionError, KeyError):
            return 0.0

    @staticmethod
    def validate_video_file(video_path: str) -> bool:
        """
        Validate that a file is a readable video

        Args:
            video_path: Path to video file

        Returns:
            True if valid video, False otherwise
        """
        try:
            probe = ffmpeg.probe(video_path)
            video_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'video'),
                None
            )
            return video_stream is not None
        except Exception as e:
            logger.warning(f"Video validation failed for {video_path}: {e}")
            return False
