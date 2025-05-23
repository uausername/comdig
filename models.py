import os
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, Float, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

def get_db_session():
    """Создает сессию подключения к базе данных PostgreSQL"""
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "comments")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

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
    rank = Column(Float, nullable=True)

    video = relationship("Video", back_populates="comments")

class Transcript(Base):
    __tablename__ = 'transcripts'

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, unique=True)
    content = Column(Text)

    video = relationship("Video", back_populates="transcript") 