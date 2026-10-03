from google import genai

class GeminiEmbeddingProvider:
    def __init__(self):
        self.client = genai.Client()
        self.model = "gemini-embedding-001"
        
    def embed_text(self, text: str) -> tuple[list[float], dict]:
        """
        Generates an embedding for the given text.
        (Currently mocked due to Google API 503 high usage errors on free tier)
        """
        # Return a mock 768-dimensional vector
        embedding_values = [0.015] * 768
        
        usage_info = {
            "operation": "embedding",
            "model": self.model,
            "tokens": 10, 
            "cost": 0.0
        }
        
        return embedding_values, usage_info
