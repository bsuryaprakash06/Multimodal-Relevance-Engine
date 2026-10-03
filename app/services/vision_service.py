from app.providers.vision.unified_provider import UnifiedVisionProvider
from app.schemas.image import ImageMetadataSchema

class VisionService:
    def __init__(self):
        self.provider = UnifiedVisionProvider()
        
    def process_image(self, filepath: str) -> tuple[ImageMetadataSchema, dict]:
        """
        Reads an image from disk and processes it using the vision provider.
        """
        # Determine mime type from extension
        ext = filepath.lower().split('.')[-1]
        mime_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp"
        }
        mime_type = mime_map.get(ext, "image/jpeg")
        
        with open(filepath, "rb") as f:
            image_bytes = f.read()
            
        return self.provider.process_image(image_bytes, mime_type)
