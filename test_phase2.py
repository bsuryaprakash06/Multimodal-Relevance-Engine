import os
from dotenv import load_dotenv

load_dotenv()

from app.database import engine, Base, SessionLocal
from app.models.image import Image, ImageMetadata, AIUsage, ImageEmbedding
from app.jobs.image_processor import ImageProcessorJob

def run_test():
    # Reset and Setup DB
    print("Setting up Database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # We will seed one image into the DB for testing
    os.makedirs("data/images", exist_ok=True)
    test_image_path = "data/images/test_image.jpg"
    
    if not os.path.exists(test_image_path):
        print(f"\n[!] Please place a real image at '{test_image_path}' to run a successful end-to-end vision test.")
        print("Creating an empty placeholder file for now, which will intentionally cause a 'failed' status due to Gemini validation...")
        with open(test_image_path, "wb") as f:
            f.write(b"") 
            
    # Insert image into DB
    img = Image(filepath=test_image_path)
    db.add(img)
    db.commit()
    
    print("\nRunning Image Processor Job...")
    job = ImageProcessorJob(db)
    results = job.process_pending_images(limit=1)
    
    print("\n--- JOB RESULTS ---")
    print(results)
    
    metadata = db.query(ImageMetadata).first()
    if metadata:
        print("\n--- METADATA ---")
        print(f"Subject: {metadata.subject}")
        print(f"Category: {metadata.category}")
        print(f"Confidence: {metadata.confidence}")
        print(f"Status: {metadata.status.value}")
        
    embedding = db.query(ImageEmbedding).first()
    if embedding:
        print("\n--- EMBEDDING ---")
        print(f"Model: {embedding.model}")
        print(f"Vector Length: {len(embedding.embedding)}")
        
    usages = db.query(AIUsage).all()
    print(f"\n--- AI USAGE ({len(usages)} records) ---")
    for u in usages:
        print(f"- {u.operation} via {u.model}: {u.tokens} tokens (Cost: ${u.cost})")
        
    db.close()

if __name__ == "__main__":
    if "GEMINI_API_KEY" not in os.environ:
        print("ERROR: Please set your GEMINI_API_KEY environment variable before running the test.")
        print("Example (Windows PowerShell): $env:GEMINI_API_KEY='your_key_here'; python test_phase2.py")
    else:
        run_test()
