"""
Unit tests for FFmpeg utilities
"""
import pytest
from unittest.mock import patch, MagicMock
from app.ffmpeg_utils import FFmpegMetadataExtractor


@pytest.fixture
def mock_ffmpeg_probe():
    """Mock FFmpeg probe response"""
    return {
        'streams': [
            {
                'codec_type': 'video',
                'codec_name': 'h264',
                'width': 1920,
                'height': 1080,
                'r_frame_rate': '30000/1001',
                'avg_frame_rate': '30000/1001'
            },
            {
                'codec_type': 'audio',
                'codec_name': 'aac'
            }
        ],
        'format': {
            'duration': '3600.0',
            'bit_rate': '11520000'
        }
    }


def test_extract_metadata_success(mock_ffmpeg_probe):
    """Test successful metadata extraction"""
    with patch('ffmpeg.probe', return_value=mock_ffmpeg_probe):
        extractor = FFmpegMetadataExtractor()
        metadata = extractor.extract_metadata('/test/video.mp4')

        assert metadata['duration_seconds'] == 3600
        assert metadata['resolution'] == '1920x1080'
        assert metadata['codec'] == 'h264'
        assert metadata['bitrate_kbps'] == 11520
        assert metadata['fps'] > 0


def test_extract_metadata_no_video_stream():
    """Test extraction with no video stream"""
    probe_no_video = {
        'streams': [
            {'codec_type': 'audio', 'codec_name': 'aac'}
        ],
        'format': {'duration': '100.0'}
    }

    with patch('ffmpeg.probe', return_value=probe_no_video):
        extractor = FFmpegMetadataExtractor()

        with pytest.raises(ValueError, match="No video stream found"):
            extractor.extract_metadata('/test/audio.mp4')


def test_extract_metadata_ffmpeg_error():
    """Test handling of FFmpeg errors"""
    with patch('ffmpeg.probe', side_effect=Exception("FFmpeg not found")):
        extractor = FFmpegMetadataExtractor()

        with pytest.raises(RuntimeError):
            extractor.extract_metadata('/test/invalid.mp4')


def test_calculate_fps_r_frame_rate():
    """Test FPS calculation from r_frame_rate"""
    video_stream = {
        'r_frame_rate': '30000/1001'
    }

    fps = FFmpegMetadataExtractor._calculate_fps(video_stream)
    assert 29.9 < fps < 30.0


def test_calculate_fps_avg_frame_rate():
    """Test FPS calculation from avg_frame_rate"""
    video_stream = {
        'avg_frame_rate': '25/1'
    }

    fps = FFmpegMetadataExtractor._calculate_fps(video_stream)
    assert fps == 25.0


def test_calculate_fps_invalid():
    """Test FPS calculation with invalid data"""
    video_stream = {}

    fps = FFmpegMetadataExtractor._calculate_fps(video_stream)
    assert fps == 0.0


def test_validate_video_file_valid(mock_ffmpeg_probe):
    """Test video file validation - valid file"""
    with patch('ffmpeg.probe', return_value=mock_ffmpeg_probe):
        extractor = FFmpegMetadataExtractor()
        is_valid = extractor.validate_video_file('/test/video.mp4')

        assert is_valid is True


def test_validate_video_file_invalid():
    """Test video file validation - invalid file"""
    with patch('ffmpeg.probe', side_effect=Exception("Invalid file")):
        extractor = FFmpegMetadataExtractor()
        is_valid = extractor.validate_video_file('/test/invalid.mp4')

        assert is_valid is False


def test_extract_metadata_missing_fields():
    """Test extraction with missing optional fields"""
    probe_minimal = {
        'streams': [
            {
                'codec_type': 'video',
                'codec_name': 'h264',
                'width': 1280,
                'height': 720
            }
        ],
        'format': {
            'duration': '600.0'
        }
    }

    with patch('ffmpeg.probe', return_value=probe_minimal):
        extractor = FFmpegMetadataExtractor()
        metadata = extractor.extract_metadata('/test/video.mp4')

        assert metadata['duration_seconds'] == 600
        assert metadata['resolution'] == '1280x720'
        assert metadata['codec'] == 'h264'
        assert metadata['bitrate_kbps'] == 0  # Missing bit_rate
