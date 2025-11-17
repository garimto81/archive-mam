"""
Unit tests for NAS Scanner
"""
import os
import pytest
import tempfile
from pathlib import Path
from app.scanner import NASScanner


@pytest.fixture
def temp_nas_structure():
    """Create temporary NAS directory structure"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create structure: /nas/poker/2024/wsop/day1/table1.mp4
        nas_path = Path(tmpdir) / "nas" / "poker" / "2024" / "wsop" / "day1"
        nas_path.mkdir(parents=True, exist_ok=True)

        # Create dummy video files
        (nas_path / "table1.mp4").touch()
        (nas_path / "table2.mp4").touch()
        (nas_path / "readme.txt").touch()  # Non-video file

        # Create day2 directory
        day2_path = nas_path.parent / "day2"
        day2_path.mkdir(exist_ok=True)
        (day2_path / "table1.mp4").touch()

        yield str(Path(tmpdir) / "nas" / "poker" / "2024" / "wsop")


def test_scanner_initialization():
    """Test scanner initialization"""
    scanner = NASScanner(base_path="/test/path")
    assert scanner.base_path == "/test/path"
    assert ".mp4" in scanner.supported_extensions


def test_scan_directory_recursive(temp_nas_structure):
    """Test recursive directory scanning"""
    scanner = NASScanner()
    videos = scanner.scan_directory(temp_nas_structure, recursive=True)

    assert len(videos) == 3  # table1, table2, day2/table1
    assert all(v['file_name'].endswith('.mp4') for v in videos)


def test_scan_directory_non_recursive(temp_nas_structure):
    """Test non-recursive scanning"""
    scanner = NASScanner()
    day1_path = os.path.join(temp_nas_structure, "day1")
    videos = scanner.scan_directory(day1_path, recursive=False)

    assert len(videos) == 2  # Only day1/table1 and day1/table2
    assert all('day1' in v['nas_file_path'] for v in videos)


def test_scan_invalid_path():
    """Test scanning invalid path"""
    scanner = NASScanner()

    with pytest.raises(ValueError, match="Path does not exist"):
        scanner.scan_directory("/nonexistent/path")


def test_extract_event_id():
    """Test event ID extraction"""
    scanner = NASScanner()

    path_parts = ('/', 'nas', 'poker', '2024', 'wsop', 'day1', 'table1.mp4')
    event_id = scanner._extract_event_id(path_parts)

    assert 'wsop' in event_id.lower()
    assert '2024' in event_id


def test_extract_day_number():
    """Test day number extraction"""
    scanner = NASScanner()

    path_parts = ('/', 'nas', 'poker', '2024', 'wsop', 'day1', 'table1.mp4')
    day = scanner._extract_day_number(path_parts)

    assert day == 1


def test_extract_table_number():
    """Test table number extraction"""
    scanner = NASScanner()

    # Test various filename formats
    assert scanner._extract_table_number("table1.mp4") == 1
    assert scanner._extract_table_number("table10.mp4") == 10
    assert scanner._extract_table_number("t5.mp4") == 5
    assert scanner._extract_table_number("unknown.mp4") == 0


def test_generate_video_id():
    """Test video ID generation"""
    scanner = NASScanner()

    video_id = scanner._generate_video_id("wsop2024_me", 1, 5)
    assert video_id == "wsop2024_me_d1_t5"


def test_process_file_video(temp_nas_structure):
    """Test processing a video file"""
    scanner = NASScanner()
    day1_path = os.path.join(temp_nas_structure, "day1")
    filename = "table1.mp4"

    file_info = scanner._process_file(day1_path, filename)

    assert file_info is not None
    assert file_info['file_name'] == filename
    assert 'video_id' in file_info
    assert 'event_id' in file_info
    assert 'file_size_bytes' in file_info


def test_process_file_non_video(temp_nas_structure):
    """Test processing a non-video file"""
    scanner = NASScanner()
    day1_path = os.path.join(temp_nas_structure, "day1")
    filename = "readme.txt"

    file_info = scanner._process_file(day1_path, filename)

    assert file_info is None  # Should ignore non-video files


def test_video_metadata_structure(temp_nas_structure):
    """Test that scanned videos have required metadata"""
    scanner = NASScanner()
    videos = scanner.scan_directory(temp_nas_structure, recursive=True)

    for video in videos:
        assert 'video_id' in video
        assert 'event_id' in video
        assert 'tournament_day' in video
        assert 'table_number' in video
        assert 'nas_file_path' in video
        assert 'file_name' in video
        assert 'file_size_bytes' in video
        assert 'created_at' in video
        assert 'scanned_at' in video
