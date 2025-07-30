from celery import Task
from .celery_app import celery_app
from .integrate_analysis import analyze_video as analyze_video_sync
from .database import SessionLocal, Hand
from sqlalchemy.orm import Session
import os
import json
import logging

logger = logging.getLogger(__name__)

class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        """Success handler"""
        logger.info(f"Task {task_id} succeeded with result: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Error handler"""
        logger.error(f"Task {task_id} failed with exception: {exc}")

@celery_app.task(base=CallbackTask, bind=True)
def analyze_video_task(self, video_path: str, video_id: int):
    """
    Asynchronous task to analyze poker video
    """
    try:
        # Update task state
        self.update_state(state='PROCESSING', meta={'current': 0, 'total': 100})
        
        # Check if video file exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Analyze video
        logger.info(f"Starting analysis for video: {video_path}")
        
        # Update progress
        self.update_state(state='PROCESSING', meta={'current': 20, 'total': 100})
        
        # Run the analysis
        result_file = analyze_video_sync(video_path)
        
        # Update progress
        self.update_state(state='PROCESSING', meta={'current': 80, 'total': 100})
        
        # Load analysis results
        if result_file and os.path.exists(result_file):
            with open(result_file, 'r') as f:
                analysis_results = json.load(f)
            
            # Save results to database
            db = SessionLocal()
            try:
                video_filename = os.path.basename(video_path)
                
                for hand_data in analysis_results:
                    hand = Hand(
                        video_filename=video_filename,
                        start_time_s=hand_data['start_time_s'],
                        end_time_s=hand_data.get('end_time_s'),
                        pot_size_history=hand_data.get('pot_size_history', []),
                        participating_players=hand_data.get('participating_players', [])
                    )
                    db.add(hand)
                
                db.commit()
                logger.info(f"Saved {len(analysis_results)} hands to database")
                
            finally:
                db.close()
            
            # Update progress
            self.update_state(state='PROCESSING', meta={'current': 100, 'total': 100})
            
            return {
                'status': 'completed',
                'video_id': video_id,
                'hands_detected': len(analysis_results),
                'result_file': result_file
            }
        else:
            raise Exception("Analysis failed - no result file generated")
            
    except Exception as e:
        logger.error(f"Error analyzing video: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'exc_type': type(e).__name__, 'exc_message': str(e)}
        )
        raise

@celery_app.task
def generate_clip_task(video_path: str, start_time: float, end_time: float, output_path: str):
    """
    Generate a video clip from the original video
    """
    import subprocess
    
    try:
        # Use ffmpeg to extract the clip
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-ss', str(start_time),
            '-to', str(end_time),
            '-c', 'copy',
            '-avoid_negative_ts', '1',
            output_path,
            '-y'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
        
        return {
            'status': 'success',
            'output_path': output_path
        }
        
    except Exception as e:
        logger.error(f"Error generating clip: {str(e)}")
        raise