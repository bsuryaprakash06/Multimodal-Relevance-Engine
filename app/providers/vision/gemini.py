from google import genai
from google.genai import types
from app.schemas.image import ImageMetadataSchema

class GeminiVisionProvider:
    def __init__(self):
        self.client = genai.Client()
        self.model = "gemini-3.8-flash"
    
    def process_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> tuple[ImageMetadataSchema, dict]:
        """
        Sends an image to Gemini and returns the parsed ImageMetadataSchema 
        and token usage.
        (Currently mocked due to Google API 503 high usage errors on free tier)
        """
        # MOCK OUTPUT
        metadata = ImageMetadataSchema(
            subject="red fox",
            category="animal",
            attributes=["wild", "orange", "forest"],
            caption="A wild red fox in its natural habitat",
            confidence=0.92
        )
        usage = {
            "operation": "vision",
            "model": self.model,
            "tokens": 125,
            "cost": 0.0
        }
        return metadata, usage
