import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

class ImageStatus(str, enum.Enum):
    pending = "pending"
    processed = "processed"
    flagged = "flagged"
    failed = "failed"

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    filepath = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    metadata_info = relationship("ImageMetadata", backref="image", uselist=False)
    embedding_info = relationship("ImageEmbedding", backref="image", uselist=False)

class ImageMetadata(Base):
    __tablename__ = "image_metadata"
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False, unique=True)
    subject = Column(String, nullable=True)
    category = Column(String, nullable=True)
    attributes = Column(JSON, nullable=True)
    caption = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    status = Column(SQLEnum(ImageStatus), default=ImageStatus.pending)

class ImageEmbedding(Base):
    __tablename__ = "image_embeddings"
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False, unique=True)
    embedding = Column(JSON, nullable=False)
    model = Column(String, nullable=False)

class AIUsage(Base):
    __tablename__ = "ai_usage"
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=True)
    operation = Column(String, nullable=False) # e.g. "vision" or "embedding"
    model = Column(String, nullable=False)
    tokens = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
