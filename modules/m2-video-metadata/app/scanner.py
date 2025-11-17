"""
NAS Scanner - Recursively scan NAS directories for video files
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from .config import config

logger = logging.getLogger(__name__)


class NASScanner:
    """Scan NAS directories for video files"""

    def __init__(self, base_path: str = None):
        self.base_path = base_path or config.NAS_BASE_PATH
        self.supported_extensions = config.SUPPORTED_EXTENSIONS

    def scan_directory(self, path: str, recursive: bool = True) -> List[Dict]:
        """
        Scan directory for video files

        Args:
            path: Directory path to scan
            recursive: Whether to scan subdirectories

        Returns:
            List of video file metadata dictionaries
        """
        if not os.path.exists(path):
            raise ValueError(f"Path does not exist: {path}")

        if not os.path.isdir(path):
            raise ValueError(f"Path is not a directory: {path}")

        video_files = []

        logger.info(f"Starting scan of {path} (recursive={recursive})")

        if recursive:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_info = self._process_file(root, file)
                    if file_info:
                        video_files.append(file_info)
        else:
            for item in os.listdir(path):
                if os.path.isfile(os.path.join(path, item)):
                    file_info = self._process_file(path, item)
                    if file_info:
                        video_files.append(file_info)

        logger.info(f"Scan complete. Found {len(video_files)} video files")
        return video_files

    def _process_file(self, root: str, filename: str) -> Optional[Dict]:
        """
        Process a single file

        Args:
            root: Directory containing the file
            filename: File name

        Returns:
            File metadata dict or None if not a video file
        """
        file_path = os.path.join(root, filename)

        # Check if it's a supported video file
        if not any(filename.lower().endswith(ext) for ext in self.supported_extensions):
            return None

        try:
            stat = os.stat(file_path)

            # Extract metadata from path structure
            # Expected: /nas/poker/{year}/{event}/{day}/table{n}.mp4
            # Example: /nas/poker/2024/wsop/main_event/day1/table1.mp4
            path_parts = Path(file_path).parts

            # Parse event_id, tournament_day, table_number from path
            event_id = self._extract_event_id(path_parts)
            tournament_day = self._extract_day_number(path_parts)
            table_number = self._extract_table_number(filename)

            # Generate video_id
            video_id = self._generate_video_id(event_id, tournament_day, table_number)

            return {
                'video_id': video_id,
                'event_id': event_id,
                'tournament_day': tournament_day,
                'table_number': table_number,
                'nas_file_path': file_path,
                'file_name': filename,
                'file_size_bytes': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'scanned_at': datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return None

    def _extract_event_id(self, path_parts: tuple) -> str:
        """
        Extract event ID from path parts

        Expected structure: /nas/poker/{year}/{event}/...
        Returns: {year}_{event} (e.g., wsop2024_me)
        """
        try:
            # Find 'poker' in path and get next 2 parts
            poker_idx = next(i for i, part in enumerate(path_parts) if 'poker' in part.lower())
            if poker_idx + 2 < len(path_parts):
                year = path_parts[poker_idx + 1]
                event = path_parts[poker_idx + 2]
                # Clean event name (remove underscores, spaces)
                event_clean = event.replace('_', '').replace(' ', '').lower()
                return f"{event}{year}" if event else f"unknown{year}"
            return "unknown"
        except (StopIteration, IndexError):
            return "unknown"

    def _extract_day_number(self, path_parts: tuple) -> int:
        """
        Extract tournament day number from path

        Looks for 'day{n}' or 'd{n}' in path
        """
        try:
            for part in reversed(path_parts):
                part_lower = part.lower()
                if part_lower.startswith('day'):
                    day_str = part_lower.replace('day', '')
                    return int(day_str) if day_str.isdigit() else 0
                elif part_lower.startswith('d') and len(part_lower) <= 3:
                    day_str = part_lower[1:]
                    if day_str.isdigit():
                        return int(day_str)
            return 0
        except (ValueError, IndexError):
            return 0

    def _extract_table_number(self, filename: str) -> int:
        """
        Extract table number from filename

        Looks for 'table{n}' or 't{n}' in filename
        """
        try:
            name_lower = filename.lower()
            # Remove extension
            name_no_ext = os.path.splitext(name_lower)[0]

            if 'table' in name_no_ext:
                table_str = name_no_ext.split('table')[-1]
                # Extract digits
                digits = ''.join(filter(str.isdigit, table_str))
                return int(digits) if digits else 0
            elif name_no_ext.startswith('t') and len(name_no_ext) <= 4:
                table_str = name_no_ext[1:]
                digits = ''.join(filter(str.isdigit, table_str))
                if digits:
                    return int(digits)
            return 0
        except (ValueError, IndexError):
            return 0

    def _generate_video_id(self, event_id: str, day: int, table: int) -> str:
        """
        Generate unique video ID

        Format: {event_id}_d{day}_t{table}
        Example: wsop2024_me_d1_t1
        """
        return f"{event_id}_d{day}_t{table}"
