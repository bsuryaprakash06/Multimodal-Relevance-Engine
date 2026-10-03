import os
import base64
from app.schemas.image import ImageMetadataSchema

class UnifiedVisionProvider:
    def __init__(self):
        self.use_gemini = "GEMINI_API_KEY" in os.environ
        if self.use_gemini:
            from google import genai
            from google.genai import types
            self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
            self.model = "gemini-2.5-flash"
            self.types = types
        else:
            from groq import Groq
            self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            self.model = "qwen/qwen3.8-27b"
            
    def process_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> tuple[ImageMetadataSchema, dict]:
        if self.use_gemini:
            return self._process_gemini(image_bytes, mime_type)
        else:
            return self._process_groq(image_bytes, mime_type)
            
    def _process_gemini(self, image_bytes: bytes, mime_type: str) -> tuple[ImageMetadataSchema, dict]:
        image_part = self.types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                "Analyze this image and return a JSON object.",
                image_part
            ],
            config=self.types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ImageMetadataSchema,
                temperature=0.1
            )
        )
        metadata = ImageMetadataSchema.model_validate_json(response.text)
        usage = {
            "operation": "vision",
            "model": self.model,
            "tokens": response.usage_metadata.total_token_count if response.usage_metadata else 0,
            "cost": 0.0
        }
        return metadata, usage

    def _process_groq(self, image_bytes: bytes, mime_type: str) -> tuple[ImageMetadataSchema, dict]:
        encoded = base64.b64encode(image_bytes).decode('utf-8')
        image_url = f"data:{mime_type};base64,{encoded}"
        prompt = (
            "Analyze this image and return a JSON object with the following schema exactly:\n"
            "{\n"
            '  "subject": "string",\n'
            '  "category": "string",\n'
            '  "attributes": ["string"],\n'
            '  "caption": "string",\n'
            '  "confidence": float\n'
            "}\n"
            "Return only valid JSON."
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            response_format={"type": "json_object"}
        )
        raw_json = response.choices[0].message.content
        metadata = ImageMetadataSchema.model_validate_json(raw_json)
        usage = {
            "operation": "vision",
            "model": self.model,
            "tokens": response.usage.total_tokens,
            "cost": 0.0
        }
        return metadata, usage
