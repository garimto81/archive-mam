#!/usr/bin/env python
"""
로컬 네트워크 파일 브라우저
로컬 및 네트워크 경로에서 비디오 파일을 탐색하고 선택할 수 있는 기능
"""
import os
import sys
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional
import mimetypes
import platform

logger = logging.getLogger(__name__)

class LocalFileBrowser:
    """로컬 파일 시스템 브라우저"""
    
    def __init__(self):
        self.video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.webm', '.wmv', '.m4v', '.3gp'}
        self.max_file_size = 10 * 1024 * 1024 * 1024  # 10GB 제한
        
        # 보안: 제한된 경로 패턴들
        self.restricted_paths = {
            # Windows 시스템 경로
            'windows': [
                r'C:\Windows\System32',
                r'C:\Windows\SysWOW64', 
                r'C:\Program Files\WindowsApps',
                r'C:\$Recycle.Bin',
                r'C:\System Volume Information',
                r'C:\ProgramData\Microsoft\Windows\Start Menu'
            ],
            # Unix/Linux 시스템 경로
            'unix': [
                '/proc', '/sys', '/dev', '/boot',
                '/root', '/etc/passwd', '/etc/shadow',
                '/var/log', '/tmp/.ICE-unix'
            ]
        }
        
        # 위험한 파일명 패턴
        self.dangerous_patterns = [
            r'\.\./',  # 디렉토리 탐색
            r'\.\.\\',  # Windows 디렉토리 탐색
            r'^\.ssh',  # SSH 키
            r'^\.gnupg',  # GPG 키
            r'password', 'passwd', 'shadow',  # 비밀번호 파일
            r'private.*key',  # 개인키
            r'\.pem$', r'\.key$'  # 인증서/키 파일
        ]
        
    def get_drives(self) -> List[Dict[str, Any]]:
        """사용 가능한 드라이브 목록 반환"""
        drives = []
        
        if platform.system() == "Windows":
            # Windows 드라이브
            import string
            for letter in string.ascii_uppercase:
                drive_path = f"{letter}:\\"
                if os.path.exists(drive_path):
                    try:
                        # 드라이브 정보 수집
                        stat = os.statvfs(drive_path) if hasattr(os, 'statvfs') else None
                        total_space = stat.f_frsize * stat.f_blocks if stat else 0
                        free_space = stat.f_frsize * stat.f_bavail if stat else 0
                        
                        drives.append({
                            'name': f"드라이브 {letter}:",
                            'path': drive_path,
                            'type': 'drive',
                            'total_space': total_space,
                            'free_space': free_space
                        })
                    except (OSError, AttributeError):
                        drives.append({
                            'name': f"드라이브 {letter}:",
                            'path': drive_path,
                            'type': 'drive',
                            'total_space': 0,
                            'free_space': 0
                        })
        else:
            # Unix/Linux/Mac 시스템
            drives.append({
                'name': '루트 디렉토리',
                'path': '/',
                'type': 'drive',
                'total_space': 0,
                'free_space': 0
            })
            
            # 일반적인 마운트 포인트들
            common_mounts = ['/home', '/media', '/mnt', '/Volumes']
            for mount in common_mounts:
                if os.path.exists(mount) and os.path.isdir(mount):
                    drives.append({
                        'name': f"마운트 {mount}",
                        'path': mount,
                        'type': 'mount',
                        'total_space': 0,
                        'free_space': 0
                    })
        
        return drives
    
    def _is_dangerous_path(self, path: str) -> bool:
        """위험한 경로인지 검증"""
        import re
        
        # 정규화된 경로로 변환
        normalized_path = os.path.normpath(path).replace('\\', '/')
        
        # 플랫폼별 제한 경로 확인
        current_platform = 'windows' if platform.system() == 'Windows' else 'unix'
        restricted_paths = self.restricted_paths.get(current_platform, [])
        
        for restricted in restricted_paths:
            restricted_normalized = os.path.normpath(restricted).replace('\\', '/')
            if normalized_path.startswith(restricted_normalized):
                return True
        
        # 위험한 패턴 확인
        for pattern in self.dangerous_patterns:
            if re.search(pattern, normalized_path, re.IGNORECASE):
                return True
        
        # 상위 디렉토리 탐색 시도 검증
        if '..' in path:
            # 정당한 상위 디렉토리 접근인지 확인
            parts = path.split(os.sep)
            if parts.count('..') > 1:  # 여러 단계 상위 디렉토리는 제한
                return True
        
        return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """파일명 보안 검증 및 정리"""
        import re
        
        # 위험한 패턴이 포함된 파일명 필터링
        for pattern in self.dangerous_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                logger.warning(f"위험한 파일명 패턴 감지: {filename}")
                return None
        
        return filename
    
    def list_directory(self, path: str, show_hidden: bool = False) -> Dict[str, Any]:
        """디렉토리 내용 나열"""
        try:
            # 보안 검증: 경로 정규화 및 제한
            path = os.path.abspath(path)
            
            # 위험한 경로 패턴 검증
            if self._is_dangerous_path(path):
                raise PermissionError(f"접근이 제한된 경로입니다: {path}")
            
            if not os.path.exists(path):
                raise FileNotFoundError(f"경로를 찾을 수 없습니다: {path}")
            
            if not os.path.isdir(path):
                raise NotADirectoryError(f"디렉토리가 아닙니다: {path}")
            
            items = []
            parent_path = os.path.dirname(path) if path != os.path.dirname(path) else None
            
            # 상위 디렉토리
            if parent_path:
                items.append({
                    'name': '..',
                    'path': parent_path,
                    'type': 'parent',
                    'size': 0,
                    'modified': None,
                    'is_video': False
                })
            
            # 디렉토리 내용
            try:
                entries = os.listdir(path)
                entries.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
                
                for entry in entries:
                    if not show_hidden and entry.startswith('.'):
                        continue
                    
                    # 파일명 보안 검증
                    sanitized_name = self._sanitize_filename(entry)
                    if sanitized_name is None:
                        continue  # 위험한 파일명은 건너뛰기
                    
                    entry_path = os.path.join(path, entry)
                    
                    try:
                        stat_info = os.stat(entry_path)
                        is_dir = os.path.isdir(entry_path)
                        
                        # 파일인 경우 비디오 확장자 확인
                        is_video = False
                        if not is_dir:
                            ext = Path(entry).suffix.lower()
                            is_video = ext in self.video_extensions
                        
                        items.append({
                            'name': entry,
                            'path': entry_path,
                            'type': 'directory' if is_dir else 'file',
                            'size': stat_info.st_size,
                            'modified': stat_info.st_mtime,
                            'is_video': is_video,
                            'extension': Path(entry).suffix.lower() if not is_dir else None
                        })
                        
                    except (OSError, PermissionError) as e:
                        # 접근 권한이 없는 파일/디렉토리
                        logger.warning(f"접근 권한 없음: {entry_path} - {e}")
                        continue
                
            except PermissionError:
                raise PermissionError(f"디렉토리 접근 권한이 없습니다: {path}")
            
            return {
                'current_path': path,
                'parent_path': parent_path,
                'items': items,
                'total_items': len(items),
                'video_count': sum(1 for item in items if item.get('is_video', False))
            }
            
        except Exception as e:
            logger.error(f"디렉토리 탐색 오류: {e}")
            raise
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """파일 상세 정보 반환"""
        try:
            file_path = os.path.abspath(file_path)
            
            # 보안 검증
            if self._is_dangerous_path(file_path):
                raise PermissionError(f"접근이 제한된 파일입니다: {file_path}")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
            
            if not os.path.isfile(file_path):
                raise ValueError(f"파일이 아닙니다: {file_path}")
            
            stat_info = os.stat(file_path)
            path_obj = Path(file_path)
            
            # MIME 타입 확인
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # 비디오 파일 여부 확인
            is_video = path_obj.suffix.lower() in self.video_extensions
            
            # 파일 크기 제한 확인
            size_ok = stat_info.st_size <= self.max_file_size
            
            return {
                'path': file_path,
                'name': path_obj.name,
                'size': stat_info.st_size,
                'size_mb': stat_info.st_size / (1024 * 1024),
                'modified': stat_info.st_mtime,
                'extension': path_obj.suffix.lower(),
                'mime_type': mime_type,
                'is_video': is_video,
                'size_ok': size_ok,
                'readable': os.access(file_path, os.R_OK)
            }
            
        except Exception as e:
            logger.error(f"파일 정보 조회 오류: {e}")
            raise
    
    def validate_video_file(self, file_path: str) -> Dict[str, Any]:
        """비디오 파일 유효성 검사"""
        try:
            file_info = self.get_file_info(file_path)
            
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'file_info': file_info
            }
            
            # 비디오 파일 여부 확인
            if not file_info['is_video']:
                validation_result['valid'] = False
                validation_result['errors'].append('지원되지 않는 비디오 형식')
            
            # 파일 크기 확인
            if not file_info['size_ok']:
                validation_result['valid'] = False
                validation_result['errors'].append(f'파일 크기가 너무 큼 (최대 {self.max_file_size // (1024**3)}GB)')
            
            # 읽기 권한 확인
            if not file_info['readable']:
                validation_result['valid'] = False
                validation_result['errors'].append('파일 읽기 권한 없음')
            
            # 경고사항
            if file_info['size_mb'] > 1024:  # 1GB 이상
                validation_result['warnings'].append('큰 파일은 분석에 시간이 오래 걸릴 수 있습니다')
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f'파일 검증 실패: {str(e)}'],
                'warnings': [],
                'file_info': None
            }
    
    def get_network_paths(self) -> List[Dict[str, Any]]:
        """네트워크 경로 목록 반환"""
        network_paths = []
        
        if platform.system() == "Windows":
            # Windows 네트워크 드라이브
            try:
                import subprocess
                result = subprocess.run(['net', 'use'], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if '\\\\' in line and ':' in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                drive_letter = parts[1]
                                network_path = parts[2]
                                network_paths.append({
                                    'name': f'네트워크 드라이브 {drive_letter}',
                                    'path': f'{drive_letter}\\',
                                    'network_path': network_path,
                                    'type': 'network'
                                })
            except Exception as e:
                logger.warning(f"네트워크 드라이브 조회 실패: {e}")
        
        else:
            # Unix/Linux/Mac 네트워크 마운트
            mount_points = ['/media', '/mnt', '/Volumes']
            for mount_point in mount_points:
                if os.path.exists(mount_point):
                    try:
                        for item in os.listdir(mount_point):
                            item_path = os.path.join(mount_point, item)
                            if os.path.isdir(item_path):
                                network_paths.append({
                                    'name': f'마운트: {item}',
                                    'path': item_path,
                                    'type': 'network'
                                })
                    except PermissionError:
                        continue
        
        return network_paths
    
    def format_file_size(self, size_bytes: int) -> str:
        """파일 크기를 읽기 쉬운 형태로 변환"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.1f} PB"

class NetworkFileBrowser(LocalFileBrowser):
    """네트워크 파일 브라우저 (확장)"""
    
    def __init__(self):
        super().__init__()
        self.smb_available = self._check_smb_support()
    
    def _check_smb_support(self) -> bool:
        """SMB/CIFS 지원 여부 확인"""
        try:
            import smbprotocol
            return True
        except ImportError:
            return False
    
    def list_smb_shares(self, server: str, username: str = None, password: str = None) -> List[Dict[str, Any]]:
        """SMB 공유 목록 조회 (선택적 기능)"""
        if not self.smb_available:
            raise ImportError("SMB 지원을 위해 smbprotocol 패키지가 필요합니다")
        
        # SMB 구현은 복잡하므로 기본 틀만 제공
        # 실제 구현시에는 smbprotocol 라이브러리 사용
        shares = []
        
        try:
            # SMB 연결 및 공유 목록 조회 로직
            # 이 부분은 실제 네트워크 환경에 따라 구현 필요
            pass
        except Exception as e:
            logger.error(f"SMB 공유 조회 실패: {e}")
            raise
        
        return shares

def test_file_browser():
    """파일 브라우저 테스트"""
    browser = LocalFileBrowser()
    
    print("=== 로컬 파일 브라우저 테스트 ===")
    
    # 드라이브 목록
    print("\n1. 사용 가능한 드라이브:")
    drives = browser.get_drives()
    for drive in drives:
        print(f"   {drive['name']} - {drive['path']}")
    
    # 현재 디렉토리 탐색
    print("\n2. 현재 디렉토리 내용:")
    try:
        current_dir = os.getcwd()
        dir_info = browser.list_directory(current_dir)
        print(f"   경로: {dir_info['current_path']}")
        print(f"   총 항목: {dir_info['total_items']}")
        print(f"   비디오 파일: {dir_info['video_count']}")
        
        # 비디오 파일만 표시
        video_files = [item for item in dir_info['items'] if item.get('is_video', False)]
        if video_files:
            print("\n   비디오 파일:")
            for video in video_files[:5]:  # 상위 5개만
                size_str = browser.format_file_size(video['size'])
                print(f"     - {video['name']} ({size_str})")
        
    except Exception as e:
        print(f"   오류: {e}")
    
    # 네트워크 경로
    print("\n3. 네트워크 경로:")
    network_paths = browser.get_network_paths()
    if network_paths:
        for path in network_paths:
            print(f"   {path['name']} - {path['path']}")
    else:
        print("   네트워크 경로 없음")

if __name__ == "__main__":
    test_file_browser()