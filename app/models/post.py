from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from app.models.image import Base
import enum

class MatchStatus(str, enum.Enum):
    accepted = "accepted"
    rejected = "rejected"
    flagged = "flagged"
    no_match = "no_match"
    pending = "pending"

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    expected_subject = Column(String, nullable=True)
    expected_category = Column(String, nullable=True)
    embedding = Column(JSON, nullable=True)

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=True)
    status = Column(SQLEnum(MatchStatus), default=MatchStatus.pending)
    reason = Column(Text, nullable=True)
    human_reviewed = Column(Boolean, default=False)
    
    post = relationship("Post", backref="matches")
    image = relationship("Image", backref="matches")
