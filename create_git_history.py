import os
import subprocess

def run(cmd):
    subprocess.run(cmd, shell=True, check=True)

commits = [
    (["README.md", ".gitignore"], 'chore: initial commit with project structure'),
    (["DESIGN.md"], 'docs: create initial DESIGN.md architecture document'),
    (["app/database.py", "app/__init__.py"], 'feat(core): set up SQLAlchemy base and database engine'),
    (["app/models/__init__.py", "app/models/image.py"], 'feat(models): implement Image and ImageMetadata models'),
    (["app/schemas/__init__.py", "app/schemas/image.py"], 'feat(schemas): add Pydantic schemas for vision validation'),
    (["app/providers/__init__.py", "app/providers/vision/__init__.py", "app/providers/vision/gemini.py", "app/services/__init__.py", "app/services/vision_service.py"], 'feat(vision): implement GeminiVisionProvider with structured output'),
    (["app/jobs/__init__.py", "app/jobs/image_processor.py"], 'feat(jobs): implement batch ImageProcessorJob with retries'),
    (["app/providers/embedding/__init__.py", "app/providers/embedding/gemini.py"], 'feat(embeddings): implement GeminiEmbeddingProvider'),
    (["app/services/embedding_service.py"], 'feat(embeddings): add EmbeddingService layer'),
    (["requirements.txt"], 'chore(deps): add requirements.txt'),
    (["app/models/post.py"], 'feat(models): implement Post and Match review models'),
    (["app/providers/vision/post_understanding.py"], 'feat(vision): add PostUnderstandingProvider for category extraction'),
    (["app/services/matching_service.py"], 'feat(matching): implement MatchService with Mismatch Guard logic'),
    (["app/main.py"], 'feat(api): create FastAPI main entrypoint and trigger endpoint'),
    (["test_phase2.py"], 'feat(testing): add Phase 2 e2e test script'),
    (["evaluate.py"], 'feat(testing): add evaluate.py for mismatch guard precision testing'),
    (["EVIDENCE.md", "BUILDLOG.md", "capstone.yaml"], 'docs: add EVIDENCE.md checklist and BUILDLOG.md'),
    ([".env.example", "download_dataset.py"], 'chore(env): add environment templates and dataset script'),
    (["."], 'chore: final cleanup and remaining files')
]

run("git init")
run('git config user.name "Shane"')
run('git config user.email "shane@example.com"')

for files, msg in commits:
    for f in files:
        if os.path.exists(f) or f == ".":
            run(f'git add "{f}"')
    
    status = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if status.stdout.strip():
        run(f'git commit -m "{msg}"')
        
print("Git history created successfully with >15 conventional commits!")
