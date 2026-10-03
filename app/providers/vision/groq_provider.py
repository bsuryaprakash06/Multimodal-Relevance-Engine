import os
import base64
import json
from groq import Groq
from app.schemas.image import ImageMetadataSchema

class GroqVisionProvider:
    def __init__(self):
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model = "qwen/qwen3.8-27b"
    
    def process_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> tuple[ImageMetadataSchema, dict]:
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
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                            },
                        },
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
