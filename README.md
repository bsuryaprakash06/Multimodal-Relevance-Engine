# Multimodal Relevance Engine

An AI-driven backend system that automatically processes an image library, tracks metadata, and semantically matches the right image to the right blog post—complete with a Mismatch Guard to confidently reject incorrect pairings. Built as a backend architecture Capstone Project.

## Documentation
- See `DESIGN.md` for the technical breakdown, Database schema, and API endpoint lists.
- See `EVIDENCE.md` for the grading checklist matrix.

## Setup & Run

1. **Install dependencies:**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

2. **Environment Variables:**
   Set your Gemini API Key in your `.env` file (A `.env.example` is provided).

3. **Run the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

## Evaluation
Run `python test_phase2.py` to see the background image processor run and execute live Groq Qwen Vision analysis.
Then run `python evaluate.py` to see the Mismatch Guard actively accept and reject mock pairings based on semantic concepts and local HuggingFace similarity thresholds.
