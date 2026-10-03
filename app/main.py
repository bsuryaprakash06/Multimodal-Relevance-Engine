import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.database import engine, Base, get_db
from app.jobs.image_processor import ImageProcessorJob
from app.models.post import Post, Match, MatchStatus
from app.services.matching_service import MatchService

# Ensure models are imported so Base.metadata can discover them
from app.models import image, post

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Image Matching Engine")

def run_processing_job(limit: int):
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        job = ImageProcessorJob(db)
        job.process_pending_images(limit=limit)
    finally:
        db.close()

@app.post("/api/jobs/process-images")
def trigger_image_processing(background_tasks: BackgroundTasks, limit: int = 10):
    background_tasks.add_task(run_processing_job, limit)
    return {"message": f"Processing job started for up to {limit} images."}

class PostCreate(BaseModel):
    title: str
    content: str

class MatchResponse(BaseModel):
    id: int
    post_id: int
    image_id: int | None
    status: str
    reason: str
    human_reviewed: bool
    
    class Config:
        from_attributes = True

@app.post("/api/posts")
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    db_post = Post(title=post.title, content=post.content)
    db.add(db_post)
    db.commit()
    return {"id": db_post.id}

@app.get("/api/posts/{post_id}/images", response_model=MatchResponse)
def get_post_image_match(post_id: int, db: Session = Depends(get_db)):
    match_service = MatchService(db)
    try:
        match = match_service.process_post_and_match(post_id)
        return match
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/reviews", response_model=List[MatchResponse])
def list_reviews(db: Session = Depends(get_db)):
    matches = db.query(Match).filter(Match.human_reviewed == False).all()
    return matches

@app.get("/api/reviews/{match_id}", response_model=MatchResponse)
def get_review(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match

class ReviewDecision(BaseModel):
    approve: bool

@app.post("/api/reviews/{match_id}", response_model=MatchResponse)
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
    return match
