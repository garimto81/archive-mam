"""
Unit tests for Proxy Generator
"""
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from app.proxy_generator import ProxyGenerator


@pytest.fixture
def temp_files():
    """Create temporary input/output files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "input.mp4")
        output_file = os.path.join(tmpdir, "output_720p.mp4")

        # Create dummy input file
        with open(input_file, 'wb') as f:
            f.write(b'fake video data')

        yield input_file, output_file


def test_proxy_generator_initialization():
    """Test proxy generator initialization"""
    gen = ProxyGenerator()

    assert gen.resolution == '720p'
    assert gen.preset == 'fast'
    assert gen.crf == 23


@patch('ffmpeg.run')
def test_generate_720p_proxy_success(mock_ffmpeg_run, temp_files):
    """Test successful proxy generation"""
    input_file, output_file = temp_files

    # Create output file to simulate FFmpeg success
    with open(output_file, 'wb') as f:
        f.write(b'proxy video data')

    gen = ProxyGenerator()
    result = gen.generate_720p_proxy(input_file, output_file, quality='medium')

    assert result['output_path'] == output_file
    assert result['output_size_bytes'] > 0
    assert os.path.exists(output_file)
    mock_ffmpeg_run.assert_called_once()


def test_generate_720p_proxy_input_not_exists():
    """Test proxy generation with missing input file"""
    gen = ProxyGenerator()

    with pytest.raises(ValueError, match="Input file does not exist"):
        gen.generate_720p_proxy('/nonexistent/input.mp4', '/tmp/output.mp4')


@patch('ffmpeg.run')
def test_generate_720p_proxy_quality_levels(mock_ffmpeg_run, temp_files):
    """Test different quality levels"""
    input_file, output_file = temp_files

    # Create output file
    with open(output_file, 'wb') as f:
        f.write(b'proxy')

    gen = ProxyGenerator()

    for quality in ['high', 'medium', 'low']:
        result = gen.generate_720p_proxy(input_file, output_file, quality=quality)
        assert result is not None


@patch('ffmpeg.run', side_effect=Exception("FFmpeg encoding failed"))
def test_generate_720p_proxy_ffmpeg_error(mock_ffmpeg_run, temp_files):
    """Test handling of FFmpeg errors"""
    input_file, output_file = temp_files

    gen = ProxyGenerator()

    with pytest.raises(RuntimeError):
        gen.generate_720p_proxy(input_file, output_file)


def test_generate_proxy_filename():
    """Test proxy filename generation"""
    gen = ProxyGenerator()

    filename = gen.generate_proxy_filename("wsop2024_me_d1_t1", resolution="720p")
    assert filename == "wsop2024_me_d1_t1_720p.mp4"

    filename_480p = gen.generate_proxy_filename("wsop2024_me_d1_t1", resolution="480p")
    assert filename_480p == "wsop2024_me_d1_t1_480p.mp4"


def test_generate_gcs_blob_name():
    """Test GCS blob name generation"""
    gen = ProxyGenerator()

    blob_name = gen.generate_gcs_blob_name(
        video_id="wsop2024_me_d1_t1",
        event_id="wsop2024_me",
        resolution="720p"
    )

    assert "wsop2024" in blob_name
    assert "me" in blob_name
    assert "720p.mp4" in blob_name


def test_generate_gcs_blob_name_single_part_event():
    """Test GCS blob name with single-part event ID"""
    gen = ProxyGenerator()

    blob_name = gen.generate_gcs_blob_name(
        video_id="unknown_d1_t1",
        event_id="unknown",
        resolution="720p"
    )

    assert "unknown/" in blob_name
    assert "720p.mp4" in blob_name
