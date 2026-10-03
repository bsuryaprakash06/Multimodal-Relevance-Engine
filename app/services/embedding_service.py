from app.providers.embedding.local_provider import LocalEmbeddingProvider

class EmbeddingService:
    def __init__(self):
        self.provider = LocalEmbeddingProvider()
        
    def generate_image_embedding(self, caption: str) -> tuple[list[float], dict]:
        """
        Generates an embedding based on the image's generated caption.
        """
        return self.provider.embed_text(caption)
        
    def generate_post_embedding(self, post_text: str) -> tuple[list[float], dict]:
        """
        Generates an embedding for a blog post.
        """
        return self.provider.embed_text(post_text)
