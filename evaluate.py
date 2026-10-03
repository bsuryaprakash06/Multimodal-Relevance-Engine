import os
from dotenv import load_dotenv

load_dotenv()

from app.database import SessionLocal
from app.models.post import Post
from app.services.matching_service import MatchService

def run_evaluation():
    db = SessionLocal()
    
    posts = db.query(Post).all()
    if not posts:
        print("No posts found in database. Seed data first before evaluating.")
        return
        
    service = MatchService(db)
    total_posts = len(posts)
    
    print(f"Evaluating {total_posts} posts against the Mismatch Guard...\n")
    
    for post in posts:
        print(f"Post '{post.title}' (ID: {post.id}):")
        try:
            match = service.process_post_and_match(post.id)
            print(f"  Result: {match.status.value.upper()}")
            print(f"  Reason: {match.reason}")
            print(f"  Candidate Image ID: {match.image_id}")
        except Exception as e:
            print(f"  Error: {e}")
        print("-" * 60)
        
    print("\nEval complete. Verify accepted Image IDs against your labeled correct pairs to calculate Top-1 Precision.")

if __name__ == "__main__":
    if "GEMINI_API_KEY" not in os.environ:
        print("Please set GEMINI_API_KEY in your environment.")
    else:
        run_evaluation()
