"""
720p Proxy Generator using FFmpeg
"""
import os
import logging
import ffmpeg
from typing import Dict, Optional
from .config import config

logger = logging.getLogger(__name__)


class ProxyGenerator:
    """Generate 720p video proxies for web streaming"""

    def __init__(self):
        self.resolution = config.PROXY_RESOLUTION
        self.preset = config.PROXY_PRESET
        self.crf = config.PROXY_CRF

    def generate_720p_proxy(
        self,
        input_path: str,
        output_path: str,
        quality: str = "medium"
    ) -> Dict:
        """
        Generate 720p H.264 proxy video

        Args:
            input_path: Path to source video
            output_path: Path for output proxy video
            quality: Quality preset ('high', 'medium', 'low')
                - high: CRF 18 (high quality, larger file)
                - medium: CRF 23 (balanced)
                - low: CRF 28 (low quality, smaller file)

        Returns:
            Dictionary with:
                - output_path: Path to generated proxy
                - output_size_bytes: Size of proxy file
                - duration_seconds: Processing duration

        Raises:
            RuntimeError: If FFmpeg encoding fails
        """
        if not os.path.exists(input_path):
            raise ValueError(f"Input file does not exist: {input_path}")

        # Map quality to CRF values
        crf_map = {
            'high': 18,
            'medium': 23,
            'low': 28,
        }
        crf = crf_map.get(quality, 23)

        logger.info(f"Generating 720p proxy: {input_path} -> {output_path} (quality={quality}, CRF={crf})")

        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # FFmpeg transcoding
            stream = ffmpeg.input(input_path)
            stream = ffmpeg.output(
                stream,
                output_path,
                vcodec='libx264',           # H.264 video codec
                acodec='aac',               # AAC audio codec
                vf='scale=-2:720',          # Scale to 720p (width auto-calculated)
                preset=self.preset,         # Encoding speed preset
                crf=crf,                    # Constant Rate Factor (quality)
                movflags='faststart',       # Enable web streaming
                audio_bitrate='128k',       # Audio bitrate
                **{'b:v': '2M'}            # Video bitrate 2 Mbps
            )

            # Run FFmpeg
            ffmpeg.run(
                stream,
                overwrite_output=True,
                capture_stdout=True,
                capture_stderr=True,
                quiet=True
            )

            # Get output file size
            if not os.path.exists(output_path):
                raise RuntimeError("Proxy file was not created")

            output_size = os.path.getsize(output_path)

            logger.info(f"Proxy generated successfully: {output_path} ({output_size / 1024 / 1024:.2f} MB)")

            return {
                'output_path': output_path,
                'output_size_bytes': output_size,
            }

        except ffmpeg.Error as e:
            stderr = e.stderr.decode('utf-8') if e.stderr else str(e)
            error_msg = f"FFmpeg encoding error: {stderr}"
            logger.error(error_msg)

            # Clean up failed output file
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass

            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Error generating proxy: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def generate_proxy_filename(self, video_id: str, resolution: str = "720p") -> str:
        """
        Generate proxy filename from video ID

        Args:
            video_id: Original video ID (e.g., "wsop2024_me_d1_t1")
            resolution: Target resolution (default "720p")

        Returns:
            Proxy filename (e.g., "wsop2024_me_d1_t1_720p.mp4")
        """
        return f"{video_id}_{resolution}.mp4"

    def generate_gcs_blob_name(self, video_id: str, event_id: str, resolution: str = "720p") -> str:
        """
        Generate GCS blob name for proxy

        Args:
            video_id: Original video ID
            event_id: Event ID (e.g., "wsop2024_me")
            resolution: Target resolution

        Returns:
            GCS blob path (e.g., "wsop2024/me/d1_t1_720p.mp4")
        """
        # Extract event components
        # event_id format: wsop2024_me -> wsop2024/me/
        parts = event_id.split('_', 1)
        if len(parts) == 2:
            event_year = parts[0]
            event_type = parts[1]
            folder = f"{event_year}/{event_type}/"
        else:
            folder = f"{event_id}/"

        # Generate filename
        filename = self.generate_proxy_filename(video_id, resolution)

        return f"{folder}{filename}"
