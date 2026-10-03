# Build Log

The following files and components were written and designed directly using AI assistance:
- `DESIGN.md` (Architecture, scope, mismatched guard outline)
- Database models (`app/models/image.py`, `app/models/post.py`)
- Pydantic schemas (`app/schemas/image.py`)
- Background jobs (`app/jobs/image_processor.py`)
- Service logic for Gemini integration (`app/providers/vision/gemini.py`, `app/providers/vision/post_understanding.py`, `app/providers/embedding/gemini.py`)
- Match Service (`app/services/matching_service.py`)
- FastAPI endpoints (`app/main.py`)
- Evaluation Script (`evaluate.py`)
- Documentation (`README.md`, `EVIDENCE.md`, `capstone.yaml`)

## AI Decisions vs Human Modifications
- AI initially suggested combining image metadata and embeddings into a single table. It was modified to separate `images`, `image_metadata`, `image_embeddings`, and `ai_usage` into their own tables for a cleaner architecture and easier cost tracking.
- The concept of "Post Understanding" was injected into the matching logic manually to ensure a reliable "Expected Subject" comparison for the Mismatch Guard.
- Threshold values were abstracted as placeholders until the evaluation phase dictates their ideal configurations.

No custom model training was performed. All AI components leverage the free tier Gemini API (`gemini-3.7-flash` and `gemini-embedding-2`).
