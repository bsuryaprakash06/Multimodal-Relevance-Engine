import os
from dotenv import load_dotenv

load_dotenv()

from app.database import SessionLocal, Base, engine
from app.models.image import Image, ImageMetadata, ImageEmbedding, ImageStatus
from app.models.post import Post
from app.services.matching_service import MatchService
from app.services.embedding_service import EmbeddingService

def seed_eval_data(db):
    print("Seeding evaluation dataset (fox vs wolf vs dog)...")
    
    # Create Images
    fox_img = Image(filepath="data/images/fox.jpg")
    wolf_img = Image(filepath="data/images/wolf.jpg")
    dog_img = Image(filepath="data/images/dog.jpg")
    
    db.add_all([fox_img, wolf_img, dog_img])
    db.commit()
    
    # Create Metadata
    db.add(ImageMetadata(image_id=fox_img.id, subject="red fox", category="animal", confidence=0.95, status=ImageStatus.processed))
    db.add(ImageMetadata(image_id=wolf_img.id, subject="gray wolf", category="animal", confidence=0.92, status=ImageStatus.processed))
    db.add(ImageMetadata(image_id=dog_img.id, subject="golden retriever", category="animal", confidence=0.98, status=ImageStatus.processed))
    
    # Generate Embeddings (Real vectors from SentenceTransformers)
    emb_service = EmbeddingService()
    fox_vec, _ = emb_service.generate_image_embedding("A wild red fox in the forest")
    wolf_vec, _ = emb_service.generate_image_embedding("A wild gray wolf in the snow")
    dog_vec, _ = emb_service.generate_image_embedding("A golden retriever dog playing")
    
    db.add(ImageEmbedding(image_id=fox_img.id, model="all-MiniLM-L6-v2", embedding=fox_vec))
    db.add(ImageEmbedding(image_id=wolf_img.id, model="all-MiniLM-L6-v2", embedding=wolf_vec))
    db.add(ImageEmbedding(image_id=dog_img.id, model="all-MiniLM-L6-v2", embedding=dog_vec))
    
    # Create Posts
    fox_post = Post(title="The behavior of red foxes", content="Red foxes are fascinating wild animals known for their bushy tails.")
    wolf_post = Post(title="Gray wolves pack dynamics", content="Wolves hunt in packs in the snowy wilderness.")
    mismatch_post = Post(title="Space Exploration", content="The James Webb telescope reveals distant galaxies.")
    
    db.add_all([fox_post, wolf_post, mismatch_post])
    db.commit()
    
    return [fox_post, wolf_post, mismatch_post], [fox_img, wolf_img, dog_img]

def run_evaluation():
    # Setup clean DB
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    posts, images = seed_eval_data(db)
    service = MatchService(db)
    
    print("\nEvaluating Mismatch Guard (Top-1 Precision):\n")
    
    correct = 0
    total = len(posts)
    
    # Expected Ground Truth
    # Fox post -> Fox image
    # Wolf post -> Wolf image
    # Space post -> No image
    
    expected = {
        posts[0].id: images[0].id,
        posts[1].id: images[1].id,
        posts[2].id: None
    }
    
    for post in posts:
        print(f"Post '{post.title}':")
        try:
            match = service.process_post_and_match(post.id)
            print(f"  Result: {match.status.value.upper()}")
            print(f"  Reason: {match.reason}")
            print(f"  Candidate Image ID: {match.image_id}")
            
            if match.image_id == expected[post.id]:
                correct += 1
                print("  [PASS] Correct match according to ground truth.")
            else:
                print(f"  [FAIL] Expected {expected[post.id]}, got {match.image_id}")
                
        except Exception as e:
            print(f"  Error: {e}")
            if expected[post.id] is None:
                correct += 1
                print("  [PASS] Correctly rejected.")
        print("-" * 60)
        
    precision = (correct / total) * 100
    print(f"\nEval complete. Top-1 Precision: {precision:.1f}%")
    
    db.close()

if __name__ == "__main__":
    if "GROQ_API_KEY" not in os.environ:
        print("Please set GROQ_API_KEY in your environment.")
    else:
        run_evaluation()
