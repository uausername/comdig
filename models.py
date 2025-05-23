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
    video_id = Column(String, unique=True, nullable=True)  # YouTube video ID
    youtube_url = Column(String, unique=True, nullable=False)
    title = Column(String)
    channel = Column(String)
    upload_date = Column(String)
    summary = Column(Text)
    transcript = Column(Text)  # Добавляем поле transcript напрямую

    comments = relationship("Comment", back_populates="video")

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
    comment_rank = Column(Float, nullable=True)

    video = relationship("Video", back_populates="comments")

# Transcript теперь является полем в Video, отдельная модель не нужна 