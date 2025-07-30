
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql.schema import ForeignKey
import datetime
import enum

# SQLite database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# Create the SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

# Enum for video processing status
class VideoStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Define the Video model
class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    file_path = Column(String)
    upload_date = Column(DateTime, default=datetime.datetime.now)
    status = Column(Enum(VideoStatus), default=VideoStatus.PENDING)
    task_id = Column(String, nullable=True)  # Celery task ID
    error_message = Column(String, nullable=True)
    
    # Relationship to hands
    hands = relationship("Hand", back_populates="video")

# Define the Hand model
class Hand(Base):
    __tablename__ = "hands"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), index=True)
    video_filename = Column(String, index=True)
    start_time_s = Column(Float)
    end_time_s = Column(Float, nullable=True)
    pot_size_history = Column(JSON) # Store as JSON string
    participating_players = Column(JSON) # Store as JSON string
    analysis_date = Column(DateTime, default=datetime.datetime.now)
    
    # Relationship to video
    video = relationship("Video", back_populates="hands")

# Function to create database tables
def create_db_tables():
    Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
