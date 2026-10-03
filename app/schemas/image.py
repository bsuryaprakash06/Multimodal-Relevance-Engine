from pydantic import BaseModel, Field
from typing import List

class ImageMetadataSchema(BaseModel):
    subject: str = Field(description="The primary subject of the image, e.g., 'red fox'")
    category: str = Field(description="The category of the subject, e.g., 'animal'")
    attributes: List[str] = Field(description="A list of attributes about the image")
    caption: str = Field(description="A short descriptive caption of the image")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0", ge=0.0, le=1.0)
