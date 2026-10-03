from sentence_transformers import SentenceTransformer

class LocalEmbeddingProvider:
    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"
        # Download and load happens here automatically (cached locally)
        self.model = SentenceTransformer(self.model_name)
        
    def embed_text(self, text: str) -> tuple[list[float], dict]:
        # Encode returns a numpy array, convert to standard python float list
        embedding_values = self.model.encode(text).tolist()
        
        usage_info = {
            "operation": "embedding",
            "model": self.model_name,
            "tokens": 0, # N/A for local 
            "cost": 0.0
        }
        
        return embedding_values, usage_info
