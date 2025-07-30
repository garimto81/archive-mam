
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import datetime
from enum import Enum

class VideoStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoBase(BaseModel):
    filename: str
    file_path: str

class VideoCreate(VideoBase):
    pass

class VideoUpload(BaseModel):
    filename: str

class Video(VideoBase):
    id: int
    upload_date: datetime.datetime
    status: VideoStatus
    task_id: Optional[str] = None
    error_message: Optional[str] = None
    
    class Config:
        orm_mode = True

class HandBase(BaseModel):
    video_filename: str
    start_time_s: float
    end_time_s: Optional[float] = None
    pot_size_history: List[Dict[str, Any]]
    participating_players: List[str]

class HandCreate(HandBase):
    video_id: Optional[int] = None

class Hand(HandBase):
    id: int
    video_id: Optional[int] = None
    analysis_date: datetime.datetime

    class Config:
        orm_mode = True

class HandSearchFilter(BaseModel):
    min_pot_size: Optional[int] = None
    max_pot_size: Optional[int] = None
    player_name: Optional[str] = None
    video_filename: Optional[str] = None
    
class ClipRequest(BaseModel):
    hand_id: int
    format: Optional[str] = "mp4"
