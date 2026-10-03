# AI Image Matching Engine - Design Document

## 1. Problem Statement
Build an AI system that matches images to blog posts based on semantic understanding of the image content rather than basic keywords or filenames. The system must include a safety layer (mismatch guard) that reliably rejects incorrect recommendations (e.g., rejecting a wolf image for a red fox article) and outputs human-readable explanations for its decisions.

## 2. Goals
- Ensure valid, structured output from the vision model.
- Rely on semantic similarity instead of keyword matching.
- Identify and confidently reject mismatching concepts (e.g., dog vs. fox).
- Maintain high precision over simply returning a result (safe rejection is a production feature).

## 3. Non-Goals
- **No Frontend UI/App:** The review interface will solely rely on REST API endpoints.
- **No multi-model evaluation:** We will stick to one vision model (Gemini Flash) and one embedding model.
- **Not a large-scale image database:** Processing is optimized for a small capstone dataset (~50 images), so complex vector DB infrastructure is unnecessary.

## 4. Architecture

```text
                    ┌─────────────────┐
                    │    BLOG POST    │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
       ┌────────────────┐       ┌─────────────────┐
       │ Post           │       │ Post Embedding  │
       │ Understanding  │       └────────┬────────┘
       │                │                │
       │ subject        │                │
       │ category       │                │
       └───────┬────────┘                │
               │                         │
               └────────────┬────────────┘
                            │
                            ▼
                  ┌────────────────────┐
                  │ Candidate Ranking  │
                  │                    │
                  │ Cosine Similarity  │
                  └─────────┬──────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │       MISMATCH GUARD      │
              │                           │
              │  Similarity Threshold     │
              │  Subject Alignment        │
              │  Category Alignment       │
              │  Vision Confidence        │
              └─────────────┬─────────────┘
                            │
                   ┌────────┴────────┐
                   ▼                 ▼
              ┌──────────┐     ┌─────────────┐
              │ ACCEPT   │     │   REJECT    │
              │          │     │             │
              │ Suggest  │     │ Explanation │
              │ image    │     │             │
              └────┬─────┘     └─────────────┘
                   │
                   ▼
             ┌─────────────┐
             │ Human Review│
             └─────────────┘


IMAGE PIPELINE
────────────────────────────────────────────────────

Image
  │
  ▼
Background Job
  │
  ▼
Gemini Vision
  │
  ▼
Pydantic Validation
  │
  ├── Invalid → Retry → Failed
  │
  ├── Low confidence → Flagged
  │
  ▼
Structured Metadata
  │
  ▼
Embedding
  │
  ▼
SQLite
```

## 5. Technology Stack
- **Language / Framework**: Python with FastAPI.
- **Vision Model**: Gemini Flash (Free Tier).
- **Embeddings**: Gemini Text Embeddings (Free Tier).
- **Database**: SQLite. Embeddings will be serialized and stored in SQLite. At the current ~50-image scale, cosine similarity will be calculated in the application layer rather than introducing a dedicated vector DB.
- **Validation**: Pydantic.

## 6. Image Metadata Schema
The vision model will produce structured output conforming to the following JSON schema:
```json
{
  "subject": "red fox",
  "category": "animal",
  "attributes": ["orange fur", "wild", "forest"],
  "caption": "A red fox standing in a forest",
  "confidence": 0.94
}
```

## 7. Database Schema
Using SQLite for the capstone scale.

**Tables:**
1. `images`
    * `id` (PK)
    * `filepath` (string)
    * `created_at` (datetime)

2. `image_metadata`
    * `id` (PK)
    * `image_id` (FK -> images.id)
    * `subject` (string)
    * `category` (string)
    * `attributes` (json)
    * `caption` (string)
    * `confidence` (float)
    * `status` (enum: pending, processed, flagged, failed)

3. `image_embeddings`
    * `id` (PK)
    * `image_id` (FK -> images.id)
    * `embedding` (json array)
    * `model` (string)

4. `ai_usage`
    * `id` (PK)
    * `image_id` (FK -> images.id, nullable for post processing)
    * `operation` (string)
    * `model` (string)
    * `tokens` (int)
    * `cost` (float)
    * `created_at` (datetime)

5. `posts`
    * `id` (PK)
    * `title` (string)
    * `content` (text)
    * `subject` (string, expected)
    * `category` (string, expected)
    * `embedding` (json array)

6. `matches` (Suggestions / Review)
    * `id` (PK)
    * `post_id` (FK -> posts.id)
    * `image_id` (FK -> images.id, nullable)
    * `status` (enum: accepted, rejected, flagged, no_match)
    * `reason` (text)
    * `human_reviewed` (boolean)

## 8. API Endpoints
- `POST /api/jobs/process-images`: Triggers background batch job to run vision extraction.
- `GET /api/posts/{id}/images`: Retrieves the ranked and guard-checked image suggestion.
- `GET /api/reviews`: List pending reviews.
- `GET /api/reviews/{match_id}`: View details/reasons for a specific pairing.
- `POST /api/reviews/{match_id}`: Human approval/rejection of a suggested pairing.

## 9. Matching Algorithm
- **Post Understanding:** The blog post text is first passed to a Gemini model to extract structured metadata (expected `subject` and `category`).
- **Embedding Generation:** Embed both the image `caption` (generated by the vision model) and the blog post text using Gemini's text embedding model.
- **Similarity Search:** Perform a cosine similarity search between the post embedding and all image embeddings (calculated in-memory) to rank the candidates.

## 10. Mismatch Guard Rules
The safety layer follows this decision flow:
```text
Candidate
    │
    ├── Similarity below threshold?
    │       └── YES → REJECT
    │
    ├── Low vision confidence?
    │       └── YES → FLAG / REJECT
    │
    ├── Subject mismatch? (e.g. Expected "red fox", Candidate "gray wolf")
    │       └── YES → REJECT
    │
    └── All checks pass
            │
            ▼
          ACCEPT

If none of the candidates pass:
NO CONFIDENT MATCH (with human-readable reason)
```
*Note: Initial similarity (e.g. 0.75) and confidence (e.g. 0.8) thresholds will be used for development only. Final thresholds will be selected using the labeled evaluation dataset and documented in the README.*

## 11. Background-Job Flow
- Images are added to the DB.
- The background job fetches images lacking metadata.
- For each image, it calls Gemini Vision.
- If successful and valid via Pydantic, it updates `image_metadata`, stores the embedding in `image_embeddings`, and tracks tokens/cost in `ai_usage`.
- If low confidence, it's flagged.
- The job tracks total API costs for the batch.

## 12. Evaluation Strategy
- **Dataset:** We will manually collect an evaluation set of ~10 blog posts mapped to 1 correct image each (from our ~50 image library).
- **Metric:** Top-1 Precision (the percentage of posts where the top-ranked, accepted image is the correctly labeled one).
- **Verification:** An eval script will run the matching algorithm against the labeled dataset and output the precision score for `README.md`.

## 13. Cost-Tracking Strategy
- Each call to the Gemini Vision or Embedding API will calculate its token usage/cost.
- This cost will be stored in the `ai_usage` table.
- A hardcoded budget limit can be set in the background job to abort if a certain threshold is exceeded (preventing runaway loops).

## 14. Failure/Retry Behavior
- **API Failures:** If the Gemini API rate limits or times out, the background job will use exponential backoff and retry up to 3 times.
- **Validation Failures:** If Pydantic rejects the model's output schema, the job will retry the prompt requesting stricter adherence to the JSON format. After 2 failed retries, the image metadata status is marked as failed.

## 15. Security/Secrets Handling
- **No hardcoded secrets:** `GEMINI_API_KEY` and other sensitive configs will live in a local `.env` file.
- `.env` will be added to `.gitignore`.
- A `.env.example` will be checked into source control with placeholder values.
