import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from app.database import engine, Base, get_db
from app.jobs.image_processor import ImageProcessorJob
from app.models.post import Post, Match, MatchStatus
from app.services.matching_service import MatchService

# Ensure models are imported so Base.metadata can discover them
from app.models import image, post

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Multimodal Relevance Engine API",
    description="AI-driven backend system for semantic image-to-post matching with a multi-signal mismatch guard.",
    version="1.0.0"
)

@app.get("/", summary="Root Endpoint", tags=["General"])
def read_root():
    return {
        "message": "Welcome to Multimodal Relevance Engine API",
        "status": "online",
        "docs": "/docs"
    }

@app.get("/health", summary="Health Check", tags=["General"])
def health_check():
    return {"status": "ok"}

def run_processing_job(limit: int):
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        job = ImageProcessorJob(db)
        job.process_pending_images(limit=limit)
    finally:
        db.close()

@app.post("/api/jobs/process-images", summary="Trigger Image Processing", tags=["Jobs"])
def trigger_image_processing(background_tasks: BackgroundTasks, limit: int = 10):
    background_tasks.add_task(run_processing_job, limit)
    return {"message": f"Processing job started for up to {limit} images."}

class PostCreate(BaseModel):
    title: str
    content: str

class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    post_id: int
    image_id: Optional[int] = None
    status: str
    reason: str
    human_reviewed: bool

@app.post("/api/posts", summary="Create Blog Post", tags=["Posts"])
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    db_post = Post(title=post.title, content=post.content)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return {"id": db_post.id, "title": db_post.title}

@app.get("/api/posts/{post_id}/images", response_model=MatchResponse, summary="Get Image Match for Post", tags=["Matching"])
def get_post_image_match(post_id: int, db: Session = Depends(get_db)):
    match_service = MatchService(db)
    try:
        match = match_service.process_post_and_match(post_id)
        return match
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/reviews", response_model=List[MatchResponse], summary="List Pending Reviews", tags=["Reviews"])
def list_reviews(db: Session = Depends(get_db)):
    matches = db.query(Match).filter(Match.human_reviewed == False).all()
    return matches

@app.get("/api/reviews/{match_id}", response_model=MatchResponse, summary="Get Match Review Details", tags=["Reviews"])
def get_review(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match

class ReviewDecision(BaseModel):
    approve: bool

@app.post("/api/reviews/{match_id}", response_model=MatchResponse, summary="Submit Review Decision", tags=["Reviews"])
def submit_review(match_id: int, decision: ReviewDecision, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    if decision.approve:
        match.status = MatchStatus.accepted
    else:
        match.status = MatchStatus.rejected

    match.human_reviewed = True
    db.commit()
    db.refresh(match)
    return match
