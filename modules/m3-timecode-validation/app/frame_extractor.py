"""
FFmpeg Frame Extractor for Vision API Analysis
"""
import logging
import subprocess
import os
import tempfile
from typing import Optional

from . import config

logger = logging.getLogger(__name__)


class FrameExtractor:
    """
    Extract video frames using FFmpeg for Vision API processing
    """

    def __init__(self):
        self.ffmpeg_path = config.FFMPEG_PATH
        self.quality = config.FRAME_EXTRACT_QUALITY
        logger.info(f"FrameExtractor initialized (ffmpeg: {self.ffmpeg_path})")

    def extract_frame(
        self,
        video_path: str,
        timestamp_seconds: float,
        output_path: Optional[str] = None
    ) -> str:
        """
        Extract a single frame from video at specified timestamp

        Args:
            video_path: Path to video file (can be GCS path or local)
            timestamp_seconds: Timestamp to extract frame (seconds)
            output_path: Optional output path (defaults to temp file)

        Returns:
            Path to extracted frame (JPEG)
        """
        if output_path is None:
            # Create temporary file
            temp_fd, output_path = tempfile.mkstemp(suffix='.jpg', prefix='frame_')
            os.close(temp_fd)

        try:
            # FFmpeg command to extract frame
            # -ss: seek to timestamp
            # -i: input file
            # -frames:v 1: extract 1 frame
            # -q:v: quality (1-31, lower is better)
            cmd = [
                self.ffmpeg_path,
                '-ss', str(timestamp_seconds),
                '-i', video_path,
                '-frames:v', '1',
                '-q:v', str(self.quality),
                '-y',  # Overwrite output file
                output_path
            ]

            logger.debug(f"Extracting frame: {' '.join(cmd)}")

            # Run FFmpeg
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,  # 30 second timeout
                check=False
            )

            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                logger.error(f"FFmpeg failed: {error_msg}")
                raise RuntimeError(f"FFmpeg extraction failed: {error_msg}")

            # Verify file exists and has content
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise RuntimeError("Extracted frame is empty or missing")

            logger.info(
                f"Frame extracted: {output_path} (size: {os.path.getsize(output_path)} bytes)"
            )

            return output_path

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg extraction timed out")
            raise RuntimeError("Frame extraction timed out")
        except Exception as e:
            logger.error(f"Frame extraction error: {e}")
            # Clean up temp file on error
            if output_path and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            raise

    def extract_multiple_frames(
        self,
        video_path: str,
        timestamps_seconds: list,
        output_dir: Optional[str] = None
    ) -> list:
        """
        Extract multiple frames from video

        Args:
            video_path: Path to video file
            timestamps_seconds: List of timestamps to extract
            output_dir: Optional output directory (defaults to temp dir)

        Returns:
            List of paths to extracted frames
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix='frames_')

        extracted_frames = []

        for i, timestamp in enumerate(timestamps_seconds):
            output_path = os.path.join(output_dir, f'frame_{i:04d}.jpg')

            try:
                frame_path = self.extract_frame(video_path, timestamp, output_path)
                extracted_frames.append(frame_path)
            except Exception as e:
                logger.error(f"Failed to extract frame at {timestamp}s: {e}")
                continue

        logger.info(f"Extracted {len(extracted_frames)}/{len(timestamps_seconds)} frames")

        return extracted_frames

    def download_gcs_video(
        self,
        gcs_path: str,
        local_path: Optional[str] = None
    ) -> str:
        """
        Download video from GCS to local temp file

        Args:
            gcs_path: GCS path (gs://bucket/path/video.mp4)
            local_path: Optional local path (defaults to temp file)

        Returns:
            Local path to downloaded video
        """
        from google.cloud import storage

        # Parse GCS path
        if not gcs_path.startswith('gs://'):
            raise ValueError(f"Invalid GCS path: {gcs_path}")

        path_parts = gcs_path[5:].split('/', 1)
        bucket_name = path_parts[0]
        blob_name = path_parts[1] if len(path_parts) > 1 else ''

        if local_path is None:
            # Create temp file
            suffix = os.path.splitext(blob_name)[1] or '.mp4'
            temp_fd, local_path = tempfile.mkstemp(suffix=suffix, prefix='video_')
            os.close(temp_fd)

        try:
            # Download from GCS
            client = storage.Client(project=config.PROJECT_ID)
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            logger.info(f"Downloading {gcs_path} to {local_path}")

            blob.download_to_filename(local_path)

            logger.info(
                f"Downloaded video: {local_path} "
                f"(size: {os.path.getsize(local_path)} bytes)"
            )

            return local_path

        except Exception as e:
            logger.error(f"Failed to download video from GCS: {e}")
            # Clean up temp file on error
            if local_path and os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except:
                    pass
            raise


class MockFrameExtractor:
    """
    Mock Frame Extractor for testing without FFmpeg
    """

    def __init__(self):
        logger.info("MockFrameExtractor initialized")

    def extract_frame(
        self,
        video_path: str,
        timestamp_seconds: float,
        output_path: Optional[str] = None
    ) -> str:
        """Mock frame extraction"""
        if output_path is None:
            temp_fd, output_path = tempfile.mkstemp(suffix='.jpg', prefix='mock_frame_')
            os.close(temp_fd)

        # Create a dummy JPEG file
        with open(output_path, 'wb') as f:
            # Minimal JPEG header
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF')
            f.write(b'\x00' * 100)  # Padding
            f.write(b'\xff\xd9')  # JPEG end marker

        logger.info(f"[MOCK] Frame extracted: {output_path}")
        return output_path

    def extract_multiple_frames(
        self,
        video_path: str,
        timestamps_seconds: list,
        output_dir: Optional[str] = None
    ) -> list:
        """Mock multiple frame extraction"""
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix='mock_frames_')

        extracted_frames = []
        for i in range(len(timestamps_seconds)):
            output_path = os.path.join(output_dir, f'mock_frame_{i:04d}.jpg')
            frame_path = self.extract_frame(video_path, timestamps_seconds[i], output_path)
            extracted_frames.append(frame_path)

        logger.info(f"[MOCK] Extracted {len(extracted_frames)} frames")
        return extracted_frames

    def download_gcs_video(
        self,
        gcs_path: str,
        local_path: Optional[str] = None
    ) -> str:
        """Mock GCS video download"""
        if local_path is None:
            temp_fd, local_path = tempfile.mkstemp(suffix='.mp4', prefix='mock_video_')
            os.close(temp_fd)

        # Create a dummy video file
        with open(local_path, 'wb') as f:
            f.write(b'MOCK VIDEO DATA')

        logger.info(f"[MOCK] Video downloaded: {local_path}")
        return local_path
