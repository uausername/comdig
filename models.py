from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Video(Base):
    __tablename__ = 'videos'

    id = Column(Integer, primary_key=True)
    youtube_url = Column(String, unique=True, nullable=False)
    title = Column(String)
    channel = Column(String)
    upload_date = Column(String)
    summary = Column(Text)

    comments = relationship("Comment", back_populates="video")
    transcript = relationship("Transcript", uselist=False, back_populates="video")

class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)
    comment_id = Column(String, unique=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    author = Column(String)
    text = Column(Text)
    likes = Column(Integer)
    published_at = Column(DateTime)
    parent_id = Column(String, nullable=True)

    video = relationship("Video", back_populates="comments")

class Transcript(Base):
    __tablename__ = 'transcripts'

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, unique=True)
    content = Column(Text)

    video = relationship("Video", back_populates="transcript") 