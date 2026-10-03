import os
import json
from groq import Groq
from pydantic import BaseModel, Field

class PostMetadataSchema(BaseModel):
    subject: str = Field(description="The expected primary subject of an image matching this post, e.g., 'red fox'")
    category: str = Field(description="The category of the subject, e.g., 'animal'")

class PostUnderstandingProvider:
    def __init__(self):
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model = "qwen/qwen3.8-27b"
        
    def analyze_post(self, content: str) -> tuple[PostMetadataSchema, dict]:
        prompt = (
            "Analyze this blog post and return a JSON object with the following schema exactly:\n"
            "{\n"
            '  "subject": "string",\n'
            '  "category": "string"\n'
            "}\n"
            "Return only valid JSON.\n\n"
            f"Post content:\n{content}"
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        raw_json = response.choices[0].message.content
        metadata = PostMetadataSchema.model_validate_json(raw_json)
        
        usage = {
            "operation": "post_understanding",
            "model": self.model,
            "tokens": response.usage.total_tokens,
            "cost": 0.0
        }
        return metadata, usage
