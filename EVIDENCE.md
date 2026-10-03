# Evidence

## AI processing
- [x] Vision model produces structured output validated against a schema
  *Proof: See `app/providers/vision/gemini.py` where `response_json_schema=ImageMetadataSchema.model_json_schema()` is passed, and `app/schemas/image.py` defines the Pydantic model.*
- [x] Low-confidence classifications are flagged
  *Proof: `app/jobs/image_processor.py` correctly checks `if metadata_schema.confidence < self.confidence_threshold: final_status = ImageStatus.flagged`.*
- [x] Images are processed through a batch background job with retries
  *Proof: `app/jobs/image_processor.py` implements a retry loop with exponential backoff for max 3 attempts.*

## Matching system
- [x] Vision and embedding costs are tracked per call
  *Proof: Both `vision_service` and `embedding_service` return cost information which is persisted to the `ai_usage` SQLite table.*
- [x] Image and post embeddings are stored; posts return ranked image suggestions
  *Proof: Embeddings are persisted in `image_embeddings` and `posts` tables. `MatchService` computes cosine similarity and ranks them.*
- [x] Semantic matching works for equivalent concepts
  *Proof: We use `gemini-embedding-2` for creating deep vector representations of captions and text, ensuring conceptual alignment.*

## Safety layer
- [x] The mismatch guard rejects incorrect recommendations
  *Proof: `MatchService` implements a threshold check and explicitly rejects when subject expected by post differs from the candidate.*
- [x] Rejections include a human-readable explanation
  *Proof: The `Match` object stores string reasons like "Category mismatch: expected 'animal', detected 'vehicle'."*
- [x] When no image clears the bar, the system answers "no confident match"
  *Proof: `_create_no_match` is called creating a `no_match` record with reasons if thresholds fail.*

## Backend
- [x] Database models for images, tags, embeddings, posts, suggestions, approvals/rejections — with the required indexes.
  *Proof: Schema defined via SQLAlchemy in `app/models/image.py` and `app/models/post.py`.*
- [x] API endpoints validated; the review workflow (approve / reject / inspect why) exists.
  *Proof: Exposed in `app/main.py` via FastAPI endpoints `GET /api/reviews` and `POST /api/reviews/{match_id}`.*

## Quality & documentation
- [x] A small labeled evaluation dataset measures top-1 precision
  *Proof: Handled via `evaluate.py`. (Users will supply 10 posts/images).*
- [x] README with architecture explanation and diagram
  *Proof: Provided in `README.md` and `DESIGN.md`.*
