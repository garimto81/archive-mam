from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Any, Optional
import os
import shutil
import json
from pathlib import Path

from . import database, schemas
from .database import Base, engine, get_db, Video, Hand, VideoStatus
from .tasks import analyze_video_task, generate_clip_task
from .celery_app import celery_app

app = FastAPI(title="Poker MAM API", version="1.0.0")

# Create necessary directories
UPLOAD_DIR = Path("uploads")
CLIPS_DIR = Path("clips")
UPLOAD_DIR.mkdir(exist_ok=True)
CLIPS_DIR.mkdir(exist_ok=True)

# Create database tables on startup
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to Poker MAM API", "version": "1.0.0"}

# Video endpoints
@app.post("/videos/upload", response_model=schemas.Video, tags=["Videos"])
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a video file for analysis"""
    # Check if video already exists
    existing = db.query(Video).filter(Video.filename == file.filename).first()
    if existing:
        raise HTTPException(status_code=400, detail="Video already exists")
    
    # Save uploaded file
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create video record
    db_video = Video(
        filename=file.filename,
        file_path=str(file_path),
        status=VideoStatus.PENDING
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    
    # Start async analysis task
    task = analyze_video_task.delay(str(file_path), db_video.id)
    
    # Update video with task ID
    db_video.task_id = task.id
    db.commit()
    
    return db_video

@app.get("/videos/", response_model=List[schemas.Video], tags=["Videos"])
def get_videos(
    skip: int = 0,
    limit: int = 100,
    status: Optional[VideoStatus] = None,
    db: Session = Depends(get_db)
):
    """Get list of videos"""
    query = db.query(Video)
    if status:
        query = query.filter(Video.status == status)
    return query.offset(skip).limit(limit).all()

@app.get("/videos/{video_id}", response_model=schemas.Video, tags=["Videos"])
def get_video(video_id: int, db: Session = Depends(get_db)):
    """Get video details"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@app.get("/videos/{video_id}/status", tags=["Videos"])
def get_video_status(video_id: int, db: Session = Depends(get_db)):
    """Get video processing status"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    result = {"status": video.status}
    
    if video.task_id and video.status == VideoStatus.PROCESSING:
        # Get Celery task status
        task = celery_app.AsyncResult(video.task_id)
        result["task_state"] = task.state
        result["task_info"] = task.info
    
    return result

# Hand endpoints
@app.post("/hands/", response_model=schemas.Hand, tags=["Hands"])
def create_hand(hand: schemas.HandCreate, db: Session = Depends(get_db)):
    """Create a new hand record"""
    db_hand = Hand(**hand.dict())
    db.add(db_hand)
    db.commit()
    db.refresh(db_hand)
    return db_hand

@app.get("/hands/", response_model=List[schemas.Hand], tags=["Hands"])
def get_hands(
    skip: int = 0,
    limit: int = 100,
    video_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get list of hands"""
    query = db.query(Hand)
    if video_id:
        query = query.filter(Hand.video_id == video_id)
    return query.offset(skip).limit(limit).all()

@app.get("/hands/{hand_id}", response_model=schemas.Hand, tags=["Hands"])
def get_hand(hand_id: int, db: Session = Depends(get_db)):
    """Get hand details"""
    hand = db.query(Hand).filter(Hand.id == hand_id).first()
    if not hand:
        raise HTTPException(status_code=404, detail="Hand not found")
    return hand

@app.post("/hands/search", response_model=List[schemas.Hand], tags=["Hands"])
def search_hands(
    filters: schemas.HandSearchFilter,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Search hands with filters"""
    query = db.query(Hand)
    
    # Filter by video filename
    if filters.video_filename:
        query = query.filter(Hand.video_filename.contains(filters.video_filename))
    
    # Filter by player name
    if filters.player_name:
        query = query.filter(
            Hand.participating_players.contains(f'"{filters.player_name}"')
        )
    
    # Filter by pot size
    hands = query.offset(skip).limit(limit).all()
    
    # Post-process for pot size filtering (since it's stored as JSON)
    if filters.min_pot_size is not None or filters.max_pot_size is not None:
        filtered_hands = []
        for hand in hands:
            max_pot = 0
            for pot_entry in hand.pot_size_history:
                if 'pot' in pot_entry:
                    max_pot = max(max_pot, pot_entry['pot'])
            
            if filters.min_pot_size and max_pot < filters.min_pot_size:
                continue
            if filters.max_pot_size and max_pot > filters.max_pot_size:
                continue
            
            filtered_hands.append(hand)
        
        return filtered_hands
    
    return hands

# Clip endpoints
@app.post("/clips/generate", tags=["Clips"])
async def generate_clip(
    clip_request: schemas.ClipRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate a video clip for a specific hand"""
    # Get hand details
    hand = db.query(Hand).filter(Hand.id == clip_request.hand_id).first()
    if not hand:
        raise HTTPException(status_code=404, detail="Hand not found")
    
    # Get video details
    video = db.query(Video).filter(Video.id == hand.video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Define output path
    output_filename = f"hand_{hand.id}_clip.{clip_request.format}"
    output_path = CLIPS_DIR / output_filename
    
    # Start clip generation task
    task = generate_clip_task.delay(
        video.file_path,
        hand.start_time_s,
        hand.end_time_s or hand.start_time_s + 60,  # Default 60s if no end time
        str(output_path)
    )
    
    return {
        "task_id": task.id,
        "hand_id": hand.id,
        "output_filename": output_filename
    }

@app.get("/clips/{filename}", tags=["Clips"])
async def download_clip(filename: str):
    """Download a generated clip"""
    file_path = CLIPS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Clip not found")
    
    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=filename
    )

@app.get("/clips/status/{task_id}", tags=["Clips"])
def get_clip_status(task_id: str):
    """Get clip generation task status"""
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "state": task.state,
        "info": task.info
    }

# Statistics endpoint
@app.get("/stats", tags=["Statistics"])
def get_statistics(db: Session = Depends(get_db)):
    """Get system statistics"""
    total_videos = db.query(Video).count()
    total_hands = db.query(Hand).count()
    videos_by_status = {}
    
    for status in VideoStatus:
        count = db.query(Video).filter(Video.status == status).count()
        videos_by_status[status.value] = count
    
    return {
        "total_videos": total_videos,
        "total_hands": total_hands,
        "videos_by_status": videos_by_status,
        "average_hands_per_video": total_hands / total_videos if total_videos > 0 else 0
    }