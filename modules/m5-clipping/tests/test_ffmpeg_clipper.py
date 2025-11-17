"""
Tests for FFmpeg video clipper.

Tests both development (mock) and production modes.
"""

import os
import pytest
import tempfile
from unittest.mock import Mock, patch

from local_agent.ffmpeg_clipper import FFmpegClipper


@pytest.fixture
def dev_clipper():
    """Create clipper in development mode."""
    return FFmpegClipper(is_development=True)


@pytest.fixture
def prod_clipper():
    """Create clipper in production mode (mocked)."""
    with patch('local_agent.ffmpeg_clipper.subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout='ffmpeg version 6.0')
        clipper = FFmpegClipper(is_development=False)
        yield clipper


class TestFFmpegClipperDevelopment:
    """Tests for FFmpeg clipper in development mode."""

    def test_init_development(self, dev_clipper):
        """Test initialization in development mode."""
        assert dev_clipper.is_development is True

    def test_clip_video_mock(self, dev_clipper):
        """Test video clipping in mock mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'output.mp4')

            result_path, metadata = dev_clipper.clip_video(
                input_path='/fake/input.mp4',
                output_path=output_path,
                start_seconds=10,
                end_seconds=60,
                quality='high'
            )

            # Check output file was created
            assert os.path.exists(result_path)
            assert result_path == output_path

            # Check metadata
            assert 'file_size_bytes' in metadata
            assert metadata['file_size_bytes'] > 0
            assert metadata['duration_seconds'] == 50  # 60 - 10

    def test_validate_video_mock(self, dev_clipper):
        """Test video validation in mock mode."""
        with tempfile.NamedTemporaryFile() as tmp:
            # File exists -> valid
            assert dev_clipper.validate_video(tmp.name) is True

        # File doesn't exist -> invalid
        assert dev_clipper.validate_video('/nonexistent/file.mp4') is False

    def test_get_video_duration_mock(self, dev_clipper):
        """Test getting video duration in mock mode."""
        duration = dev_clipper.get_video_duration('/fake/video.mp4')
        assert duration == 3600.0  # Mock returns 1 hour


class TestFFmpegClipperProduction:
    """Tests for FFmpeg clipper in production mode (mocked)."""

    def test_init_production(self, prod_clipper):
        """Test initialization in production mode."""
        assert prod_clipper.is_development is False

    @patch('local_agent.ffmpeg_clipper.ffmpeg.run')
    @patch('local_agent.ffmpeg_clipper.ffmpeg.probe')
    def test_clip_video_high_quality(self, mock_probe, mock_run, prod_clipper):
        """Test clipping with high quality (codec copy)."""
        # Mock FFprobe response
        mock_probe.return_value = {
            'format': {
                'duration': '50.0',
                'format_name': 'mp4'
            },
            'streams': [
                {'codec_type': 'video', 'codec_name': 'h264'},
                {'codec_type': 'audio', 'codec_name': 'aac'}
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.mp4')
            output_path = os.path.join(tmpdir, 'output.mp4')

            # Create fake input file
            with open(input_path, 'wb') as f:
                f.write(b'fake video data')

            # Create fake output file (FFmpeg would create this)
            with open(output_path, 'wb') as f:
                f.write(b'fake clipped video')

            result_path, metadata = prod_clipper.clip_video(
                input_path=input_path,
                output_path=output_path,
                start_seconds=10,
                end_seconds=60,
                quality='high'
            )

            # Verify FFmpeg was called
            mock_run.assert_called_once()

            # Check metadata
            assert 'file_size_bytes' in metadata
            assert metadata['duration_seconds'] == 50.0
            assert metadata['format'] == 'mp4'

    @patch('local_agent.ffmpeg_clipper.ffmpeg.run')
    @patch('local_agent.ffmpeg_clipper.ffmpeg.probe')
    def test_clip_video_medium_quality(self, mock_probe, mock_run, prod_clipper):
        """Test clipping with medium quality (re-encode)."""
        mock_probe.return_value = {
            'format': {
                'duration': '30.0',
                'format_name': 'mp4'
            },
            'streams': [
                {'codec_type': 'video', 'codec_name': 'h264'}
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.mp4')
            output_path = os.path.join(tmpdir, 'output.mp4')

            with open(input_path, 'wb') as f:
                f.write(b'fake video')

            with open(output_path, 'wb') as f:
                f.write(b'fake output')

            prod_clipper.clip_video(
                input_path=input_path,
                output_path=output_path,
                start_seconds=0,
                end_seconds=30,
                quality='medium'
            )

            # Verify FFmpeg was called
            mock_run.assert_called_once()

    def test_clip_video_invalid_input(self, prod_clipper):
        """Test clipping with non-existent input file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'output.mp4')

            with pytest.raises(FileNotFoundError):
                prod_clipper.clip_video(
                    input_path='/nonexistent/input.mp4',
                    output_path=output_path,
                    start_seconds=0,
                    end_seconds=10
                )

    def test_clip_video_invalid_time_range(self, prod_clipper):
        """Test clipping with invalid time range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.mp4')
            output_path = os.path.join(tmpdir, 'output.mp4')

            with open(input_path, 'wb') as f:
                f.write(b'fake video')

            with pytest.raises(ValueError):
                prod_clipper.clip_video(
                    input_path=input_path,
                    output_path=output_path,
                    start_seconds=100,
                    end_seconds=50  # End before start
                )

    @patch('local_agent.ffmpeg_clipper.ffmpeg.probe')
    def test_validate_video_success(self, mock_probe, prod_clipper):
        """Test successful video validation."""
        mock_probe.return_value = {
            'streams': [
                {'codec_type': 'video'}
            ]
        }

        with tempfile.NamedTemporaryFile() as tmp:
            assert prod_clipper.validate_video(tmp.name) is True

    @patch('local_agent.ffmpeg_clipper.ffmpeg.probe')
    def test_validate_video_failure(self, mock_probe, prod_clipper):
        """Test video validation failure."""
        mock_probe.side_effect = Exception("Invalid video")

        assert prod_clipper.validate_video('/fake/video.mp4') is False

    @patch('local_agent.ffmpeg_clipper.ffmpeg.probe')
    def test_get_video_duration(self, mock_probe, prod_clipper):
        """Test getting video duration."""
        mock_probe.return_value = {
            'format': {
                'duration': '125.5'
            }
        }

        duration = prod_clipper.get_video_duration('/fake/video.mp4')
        assert duration == 125.5

    @patch('local_agent.ffmpeg_clipper.ffmpeg.probe')
    def test_get_video_duration_failure(self, mock_probe, prod_clipper):
        """Test getting duration when probe fails."""
        mock_probe.side_effect = Exception("Probe failed")

        with pytest.raises(RuntimeError):
            prod_clipper.get_video_duration('/fake/video.mp4')

    @patch('local_agent.ffmpeg_clipper.ffmpeg.probe')
    def test_get_metadata(self, mock_probe, prod_clipper):
        """Test extracting video metadata."""
        mock_probe.return_value = {
            'format': {
                'duration': '120.0',
                'format_name': 'mov,mp4,m4a'
            },
            'streams': [
                {'codec_type': 'video', 'codec_name': 'h264'},
                {'codec_type': 'audio', 'codec_name': 'aac'}
            ]
        }

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b'fake video data')
            tmp.flush()

            metadata = prod_clipper._get_video_metadata(tmp.name)

            assert metadata['duration_seconds'] == 120.0
            assert metadata['format'] == 'mov,mp4,m4a'
            assert metadata['video_codec'] == 'h264'
            assert metadata['audio_codec'] == 'aac'
            assert 'file_size_bytes' in metadata

    @patch('local_agent.ffmpeg_clipper.ffmpeg.probe')
    def test_get_metadata_no_audio(self, mock_probe, prod_clipper):
        """Test metadata extraction for video without audio."""
        mock_probe.return_value = {
            'format': {
                'duration': '60.0',
                'format_name': 'mp4'
            },
            'streams': [
                {'codec_type': 'video', 'codec_name': 'h264'}
            ]
        }

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b'data')
            tmp.flush()

            metadata = prod_clipper._get_video_metadata(tmp.name)

            assert metadata['video_codec'] == 'h264'
            assert metadata['audio_codec'] is None

    @patch('local_agent.ffmpeg_clipper.ffmpeg.probe')
    def test_get_metadata_probe_failure(self, mock_probe, prod_clipper):
        """Test metadata extraction when probe fails."""
        mock_probe.side_effect = Exception("Probe failed")

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b'data')
            tmp.flush()

            metadata = prod_clipper._get_video_metadata(tmp.name)

            # Should return basic metadata
            assert 'file_size_bytes' in metadata
            assert metadata['format'] == 'unknown'
