# Multimodal Relevance Engine

An AI-driven backend engine that automatically indexes and analyzes image libraries, extracts structured visual metadata, and semantically matches relevant imagery to blog posts. The engine features a multi-signal Mismatch Guard designed to actively detect and reject false-positive pairings (such as preventing wolf imagery from pairing with red fox articles), outputting structured, human-readable explanations for all match and rejection decisions.

## Architecture

The system decouples visual extraction, semantic embedding generation, vector similarity search, and safety guardrails into modular stages.

```text
                                  INGESTION PIPELINE
                                  ------------------
Image Library ───> Unified Vision Model ───> Pydantic Validation ───> Text Embeddings ───> Database
               (Gemini Flash / Qwen 27B)    (ImageMetadataSchema)   (all-MiniLM-L6-v2)     (SQLite)
                                                                             │
                                                                             ▼
                                                                        image_vectors


                                  MATCHING & GUARD PIPELINE
                                  -------------------------
Blog Post ───> Post Understanding ───> Post Embedding ───> Cosine Similarity Ranking (image_vectors)
               (Subject / Category)   (post_vectors)                        │
                                                                            ▼
                                                                 Top-Ranked Candidate
                                                                            │
                                                                            ▼
                                                                  +-------------------+
                                                                  |  MISMATCH GUARD   |
                                                                  +-------------------+
                                                                  | 1. Sim >= 0.50    |
                                                                  | 2. Conf >= 0.80   |
                                                                  | 3. Subject Align  |
                                                                  +-------------------+
                                                                     /             \
                                                                    /               \
                                                                  PASS             FAIL
                                                                  /                   \
                                                                 ▼                     ▼
                                                          ACCEPTED PAIRING      REJECTED PAIRING
                                                          (Pending Review)     (With Explanation)
```

### Core Components

1. **Unified Vision Provider (`app/providers/vision/`)**: Dynamically routes image analysis through Google Gemini 2.5 Flash or Groq Qwen 27B multimodal models, extracting structured labels, attributes, captions, and model confidence scores.
2. **Post Understanding Service (`app/providers/vision/post_understanding.py`)**: Analyzes blog post content using LLM extraction to identify expected subjects and categories prior to matching.
3. **Local Embedding Service (`app/providers/embedding/`)**: Computes dense vector representations using SentenceTransformers (`all-MiniLM-L6-v2`) cached locally to maintain fast, reproducible embedding calculations without API quotas.
4. **Mismatch Guard (`app/services/matching_service.py`)**: Multi-signal safety layer enforcing:
   - **Vector Similarity Cutoff**: Rejects matches falling below the cosine similarity threshold.
   - **Vision Confidence Check**: Rejects candidates where the visual model confidence score falls below 0.80.
   - **Semantic Subject Alignment**: Enforces subject consistency to stop semantically close but distinct species or concepts from being falsely paired (e.g., rejecting a wolf image for a fox article).
5. **Human-in-the-Loop Review System (`/api/reviews`)**: Dedicated workflow endpoints for inspecting model decisions, reviewing rejection reasons, and logging manual approvals.

## Tech Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Web Framework | FastAPI | 0.110+ | Asynchronous RESTful API framework |
| Runtime | Python | 3.11+ | Core application runtime |
| Multimodal Vision | Google GenAI / Groq | Gemini 2.5 / Qwen 27B | Visual inspection and structured captioning |
| Embedding Engine | SentenceTransformers | all-MiniLM-L6-v2 | 384-dimensional dense text embeddings |
| Data Validation | Pydantic v2 | 2.6+ | Structured schema enforcement and serialization |
| Relational Storage | SQLite / SQLAlchemy | 2.0+ | Relational metadata, match logs, and cost audit trail |
| Containerization | Docker & Docker Compose | Compose V2 | Containerized deployment and health monitoring |
| Testing Suite | Pytest | 8.0+ | Automated unit and integration test runner |

## Project Structure

```text
Multimodal-Relevance-Engine/
|-- app/
|   |-- jobs/
|   |   |-- __init__.py
|   |   `-- image_processor.py         # Batch image ingestion with exponential backoff
|   |-- models/
|   |   |-- __init__.py
|   |   |-- image.py                   # SQLAlchemy models (Image, ImageMetadata, AIUsage)
|   |   `-- post.py                    # SQLAlchemy models (Post, Match)
|   |-- providers/
|   |   |-- __init__.py
|   |   |-- embedding/
|   |   |   |-- __init__.py
|   |   |   |-- gemini.py              # Gemini embedding provider
|   |   |   `-- local_provider.py      # Local SentenceTransformers embedding provider
|   |   `-- vision/
|   |       |-- __init__.py
|   |       |-- gemini.py              # Direct Gemini vision provider
|   |       |-- post_understanding.py  # Blog post subject & category extractor
|   |       `-- unified_provider.py    # Auto-switching Gemini / Groq vision provider
|   |-- schemas/
|   |   |-- __init__.py
|   |   `-- image.py                   # Pydantic schemas (ImageMetadataSchema)
|   |-- services/
|   |   |-- __init__.py
|   |   |-- embedding_service.py       # Embedding abstraction layer
|   |   |-- matching_service.py        # Cosine similarity and Mismatch Guard
|   |   `-- vision_service.py          # Image decoding and MIME dispatch
|   |-- database.py                    # SQLAlchemy sessionmaker and engine config
|   `-- main.py                        # FastAPI application endpoints and routes
|-- tests/
|   |-- __init__.py
|   |-- conftest.py                    # Database fixtures and mock providers
|   |-- test_api.py                    # Route integration tests
|   |-- test_mismatch_guard.py         # Mismatch Guard unit test matrix
|   |-- test_schemas.py                # Pydantic validation tests
|   `-- test_similarity.py             # Vector cosine similarity math tests
|-- .env.example                       # Environment variable configuration template
|-- .gitignore                         # Git tracking ignore rules
|-- BUILDLOG.md                        # Architectural decisions and build log
|-- capstone.yaml                      # Project entry point configuration
|-- DESIGN.md                          # Technical design specification
|-- docker-compose.yml                 # Multi-service container orchestration
|-- Dockerfile                         # Container image build file
|-- download_dataset.py                # Dataset acquisition script
|-- evaluate.py                        # Precision evaluation runner
|-- EVIDENCE.md                        # Evaluation evidence and verification checklist
|-- LICENSE                            # MIT License
|-- pytest.ini                         # Pytest configuration
|-- README.md                          # Project documentation
|-- requirements.txt                   # Project package dependencies
`-- test_phase2.py                     # End-to-end background job execution test
```

## Environment Configuration

Copy `.env.example` to create your local `.env`:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | None | Google Gemini API key for vision and LLM extraction |
| `GROQ_API_KEY` | None | Groq API key for high-speed Qwen vision fallback |
| `DATABASE_URL` | `sqlite:///./capstone.db` | SQLAlchemy database connection URI |
| `SIMILARITY_THRESHOLD` | `0.50` | Minimum cosine similarity required to clear the guard |
| `CONFIDENCE_THRESHOLD` | `0.80` | Minimum vision model confidence required for acceptance |

## Setup & Execution

### Option 1: Docker Compose (Recommended)

Run the containerized application with automated healthchecks:

```bash
docker compose up --build
```

- API Root: `http://localhost:8000/`
- Health Probe: `http://localhost:8000/health`
- Interactive Swagger Documentation: `http://localhost:8000/docs`

### Option 2: Local Python Environment

1. Clone and navigate to the repository:
   ```bash
   git clone https://github.com/bsuryaprakash06/Multimodal-Relevance-Engine.git
   cd Multimodal-Relevance-Engine
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv

   # On Linux / macOS:
   source venv/bin/activate

   # On Windows:
   .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Launch development server:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

5. (Optional) Download evaluation dataset:
   ```bash
   python download_dataset.py
   ```

## Evaluation & Precision Benchmarks

The Mismatch Guard was benchmarked against an adversarial evaluation dataset containing subtle cross-category distractors (such as pairing a wolf image with an article on red foxes, and pairing space imagery with wildlife posts).

Run the evaluation script:

```bash
python evaluate.py
```

### Benchmark Results

- **Metric**: Top-1 Precision on adversarial evaluation set
- **Score**: **100.0%**
- **Adversarial Rejection**: 100% of conflicting subjects and below-threshold pairings were safely rejected with explanatory reasons.

## API Specification

### General Endpoints

| Method | Endpoint | Description | Status Codes |
|---|---|---|---|
| `GET` | `/` | Root endpoint returning service status | `200` |
| `GET` | `/health` | Container and monitoring health probe | `200` |

### Batch Processing Endpoints

| Method | Endpoint | Description | Status Codes |
|---|---|---|---|
| `POST` | `/api/jobs/process-images` | Trigger background image processing job | `200` |

### Post & Matching Endpoints

| Method | Endpoint | Request Body | Description | Status Codes |
|---|---|---|---|---|
| `POST` | `/api/posts` | `{"title": str, "content": str}` | Create a new blog post | `200` |
| `GET` | `/api/posts/{id}/images` | None | Retrieve guard-evaluated image recommendation | `200`, `404` |

### Review & Human-in-the-Loop Endpoints

| Method | Endpoint | Request Body | Description | Status Codes |
|---|---|---|---|---|
| `GET` | `/api/reviews` | None | List all pending unreviewed match decisions | `200` |
| `GET` | `/api/reviews/{id}` | None | Retrieve specific match decision details and reasoning | `200`, `404` |
| `POST` | `/api/reviews/{id}` | `{"approve": bool}` | Approve or reject a suggested image match | `200`, `404` |

## Automated Testing

The project maintains an automated test suite verifying vector math, schema enforcement, API routes, and Mismatch Guard decision branches.

Execute tests using pytest:

```bash
pytest
```

Run with verbose test reporting:

```bash
pytest -v
```

### Test Coverage Summary

- **Vector Mathematics (`tests/test_similarity.py`)**: Validates cosine similarity under identical, orthogonal, opposite, unnormalized, and zero-vector conditions.
- **Mismatch Guard Rules (`tests/test_mismatch_guard.py`)**: Tests all safety decision branches: valid match acceptance, low similarity rejection, low confidence rejection, adversarial subject mismatch rejection, and empty library handling.
- **Schema Validation (`tests/test_schemas.py`)**: Verifies Pydantic v2 validation boundaries, confidence range limits, and serialization.
- **REST Endpoints (`tests/test_api.py`)**: Tests welcome probe, health check, post creation, review listing, detail lookup, and approval/rejection updates.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
