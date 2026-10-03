# Evidence Checklist

## 1. Vision model produces structured output validated against a schema
**Proof:** `ImageMetadataSchema.model_validate_json(raw_json)` in `groq_provider.py`. The batch job logs validate this (e.g. `Subject: red fox`).

## 2. Low-confidence classifications are flagged instead of accepted
**Proof:** `app/jobs/image_processor.py` explicitly handles `if metadata.confidence < 0.8: status = flagged`. The evaluate job handles rejections based on confidence.

## 3. Images are processed through a batch background job with retries
**Proof:** `ImageProcessorJob.process_pending_images()` processes in batches, and `google.genai` api client implements `tenacity` retries.

## 4. Vision and embedding costs are tracked per call
**Proof:** `AI USAGE` log output shows: `- vision via qwen/qwen3.8-27b: 2006 tokens (Cost: $0.0)`

## 5. Image and post embeddings are stored; posts return ranked image suggestions
**Proof:** `MatchService.rank_images_for_post` actively uses cosine similarity on the vectors stored in the DB.

## 6. Semantic matching works for equivalent concepts
**Proof:** The `evaluate.py` script successfully maps "gray wolves pack dynamics" to "A wild gray wolf in the snow".

## 7. The mismatch guard rejects incorrect recommendations — the wolf-on-a-fox-post scenario provably fails
**Proof:** In `evaluate.py`, the system actively rejects the wolf candidate for the red fox post based on category extraction logic.

## 8. Rejections include a human-readable explanation
**Proof:** The response outputs `Reason: Animal category mismatch: expected fox, detected wolf`.

## 9. When no image clears the bar, the system answers "no confident match" with reasons
**Proof:** In `evaluate.py` for the Space post, it outputs `Reason: Similarity threshold 0.25 not met`.

## 10. Database models for images, tags, embeddings, posts, suggestions, approvals/rejections
**Proof:** `app/models/image.py` and `app/models/post.py` use SQLAlchemy models with constraints and indexing.

## 11. API endpoints validated; the review workflow (approve / reject / inspect why) exists
**Proof:** `app/main.py` contains `POST /api/reviews/{match_id}` taking a `ReviewDecision(approve=True)` JSON body.

## 12. A small labeled evaluation dataset measures top-1 precision
**Proof:** `evaluate.py` implements a 3-pair evaluation dataset testing positive matches and intentional rejections. Top-1 Precision: 100.0%.

## 13. README with architecture explanation and diagram; the required files present
**Proof:** `README.md` contains the ASCII diagram. `capstone.yaml`, `EVIDENCE.md`, and `.env.example` are present.
