"""
FFmpeg video clipper for M5 Clipping Service.

Handles video clipping using FFmpeg with codec copy (no re-encoding).
Supports both development (mock) and production modes.
"""

import logging
import os
import subprocess
import tempfile
from typing import Tuple
import ffmpeg

logger = logging.getLogger(__name__)


class FFmpegClipper:
    """FFmpeg-based video clipper."""

    def __init__(self, is_development: bool = False):
        self.is_development = is_development
        self._verify_ffmpeg()

    def _verify_ffmpeg(self):
        """Verify FFmpeg is installed."""
        if self.is_development:
            logger.info("FFmpeg verification skipped (development mode)")
            return

        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("FFmpeg is not available")

            logger.info(f"FFmpeg verified: {result.stdout.split()[2]}")

        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg not found. Please install FFmpeg: "
                "https://ffmpeg.org/download.html"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg verification timed out")

    def clip_video(
        self,
        input_path: str,
        output_path: str,
        start_seconds: float,
        end_seconds: float,
        quality: str = 'high'
    ) -> Tuple[str, dict]:
        """
        Clip a video using FFmpeg.

        Args:
            input_path: Path to input video file
            output_path: Path to save output clip
            start_seconds: Start time in seconds
            end_seconds: End time in seconds
            quality: Output quality ('high' = codec copy, 'medium' = re-encode)

        Returns:
            Tuple of (output_path, metadata_dict)

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If FFmpeg command fails
        """
        if self.is_development:
            return self._mock_clip(input_path, output_path, start_seconds, end_seconds)

        # Validate input file exists
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input video not found: {input_path}")

        # Calculate duration
        duration = end_seconds - start_seconds

        if duration <= 0:
            raise ValueError("end_seconds must be greater than start_seconds")

        logger.info(
            f"Clipping video: input={input_path}, "
            f"start={start_seconds}s, duration={duration}s, quality={quality}"
        )

        try:
            # Create output directory if needed
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Build FFmpeg command based on quality
            if quality == 'high':
                # High quality: codec copy (no re-encoding, fast)
                stream = (
                    ffmpeg
                    .input(input_path, ss=start_seconds, t=duration)
                    .output(
                        output_path,
                        vcodec='copy',
                        acodec='copy',
                        avoid_negative_ts='make_zero'
                    )
                    .overwrite_output()
                )
            else:
                # Medium quality: H.264 re-encode (smaller file size)
                stream = (
                    ffmpeg
                    .input(input_path, ss=start_seconds, t=duration)
                    .output(
                        output_path,
                        vcodec='libx264',
                        acodec='aac',
                        video_bitrate='2M',
                        audio_bitrate='128k',
                        preset='fast'
                    )
                    .overwrite_output()
                )

            # Run FFmpeg
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)

            # Get output file metadata
            metadata = self._get_video_metadata(output_path)

            logger.info(
                f"Clipping completed: output={output_path}, "
                f"size={metadata['file_size_bytes']} bytes"
            )

            return output_path, metadata

        except ffmpeg.Error as e:
            error_message = e.stderr.decode('utf-8') if e.stderr else str(e)
            logger.error(f"FFmpeg clipping failed: {error_message}")
            raise RuntimeError(f"FFmpeg error: {error_message}")

        except Exception as e:
            logger.error(f"Unexpected error during clipping: {e}")
            raise

    def _mock_clip(
        self,
        input_path: str,
        output_path: str,
        start_seconds: float,
        end_seconds: float
    ) -> Tuple[str, dict]:
        """Mock clipping for development mode."""
        duration = end_seconds - start_seconds

        # Create output directory
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Create a small dummy video file (empty MP4)
        with open(output_path, 'wb') as f:
            # Write minimal MP4 header (just enough to be recognized)
            f.write(b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00')
            f.write(b'isomiso2mp41' + b'\x00' * 100)

        metadata = {
            'file_size_bytes': os.path.getsize(output_path),
            'duration_seconds': duration,
            'format': 'mp4',
            'video_codec': 'mock',
            'audio_codec': 'mock'
        }

        logger.info(
            f"[MOCK] Clipping completed: input={input_path}, "
            f"output={output_path}, duration={duration}s"
        )

        return output_path, metadata

    def _get_video_metadata(self, video_path: str) -> dict:
        """
        Extract video metadata using FFprobe.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary containing metadata
        """
        try:
            probe = ffmpeg.probe(video_path)

            # Extract video stream info
            video_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'video'),
                None
            )
            audio_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'audio'),
                None
            )

            metadata = {
                'file_size_bytes': os.path.getsize(video_path),
                'duration_seconds': float(probe['format']['duration']),
                'format': probe['format']['format_name'],
                'video_codec': video_stream['codec_name'] if video_stream else None,
                'audio_codec': audio_stream['codec_name'] if audio_stream else None,
            }

            return metadata

        except Exception as e:
            logger.warning(f"Failed to get video metadata: {e}")
            # Return basic metadata if probe fails
            return {
                'file_size_bytes': os.path.getsize(video_path),
                'duration_seconds': None,
                'format': 'unknown'
            }

    def validate_video(self, video_path: str) -> bool:
        """
        Validate that a video file is readable by FFmpeg.

        Args:
            video_path: Path to video file

        Returns:
            True if valid, False otherwise
        """
        if self.is_development:
            return os.path.exists(video_path)

        try:
            probe = ffmpeg.probe(video_path)
            return 'streams' in probe and len(probe['streams']) > 0

        except Exception as e:
            logger.error(f"Video validation failed: {e}")
            return False

    def get_video_duration(self, video_path: str) -> float:
        """
        Get video duration in seconds.

        Args:
            video_path: Path to video file

        Returns:
            Duration in seconds

        Raises:
            RuntimeError: If unable to get duration
        """
        if self.is_development:
            return 3600.0  # Mock: 1 hour

        try:
            probe = ffmpeg.probe(video_path)
            duration = float(probe['format']['duration'])
            return duration

        except Exception as e:
            logger.error(f"Failed to get video duration: {e}")
            raise RuntimeError(f"Unable to get video duration: {str(e)}")
