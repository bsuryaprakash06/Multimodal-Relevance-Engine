import logging
import time
from sqlalchemy.orm import Session
from app.models.image import Image, ImageMetadata, ImageEmbedding, AIUsage, ImageStatus
from app.services.vision_service import VisionService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class ImageProcessorJob:
    def __init__(self, db: Session):
        self.db = db
        self.vision_service = VisionService()
        self.embedding_service = EmbeddingService()
        # Initial development threshold, will be tuned later based on evaluation
        self.confidence_threshold = 0.8  

    def process_pending_images(self, limit: int = 10):
        # Fetch pending images: either no metadata exists, or status is pending/failed
        pending_images = self.db.query(Image).outerjoin(
            ImageMetadata, Image.id == ImageMetadata.image_id
        ).filter(
            (ImageMetadata.id == None) | 
            (ImageMetadata.status == ImageStatus.pending) | 
            (ImageMetadata.status == ImageStatus.failed)
        ).limit(limit).all()

        results = {"processed": 0, "flagged": 0, "failed": 0, "total_cost": 0.0, "total_tokens": 0}

        for image in pending_images:
            self._process_single_image(image, results)
            
        return results

    def _process_single_image(self, image: Image, results: dict) -> bool:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 1. Vision Provider Call & Pydantic Validation
                metadata_schema, usage_info = self.vision_service.process_image(image.filepath)
                
                # 2. Confidence Handling
                if metadata_schema.confidence < self.confidence_threshold:
                    final_status = ImageStatus.flagged
                    results["flagged"] += 1
                else:
                    final_status = ImageStatus.processed
                    results["processed"] += 1

                # 3. Store Metadata
                metadata = self.db.query(ImageMetadata).filter(ImageMetadata.image_id == image.id).first()
                if not metadata:
                    metadata = ImageMetadata(image_id=image.id)
                    self.db.add(metadata)
                
                metadata.subject = metadata_schema.subject
                metadata.category = metadata_schema.category
                metadata.attributes = metadata_schema.attributes
                metadata.caption = metadata_schema.caption
                metadata.confidence = metadata_schema.confidence
                metadata.status = final_status

                # 4. Cost Tracking (Vision)
                usage = AIUsage(
                    image_id=image.id,
                    operation=usage_info["operation"],
                    model=usage_info["model"],
                    tokens=usage_info["tokens"],
                    cost=usage_info["cost"]
                )
                self.db.add(usage)
                results["total_tokens"] += usage_info["tokens"]
                results["total_cost"] += usage_info["cost"]
                
                # 5. Embedding Generation (only if processed/confident)
                if final_status == ImageStatus.processed:
                    embedding_vals, embed_usage = self.embedding_service.generate_image_embedding(metadata.caption)
                    
                    embedding_record = self.db.query(ImageEmbedding).filter(ImageEmbedding.image_id == image.id).first()
                    if not embedding_record:
                        embedding_record = ImageEmbedding(image_id=image.id)
                        self.db.add(embedding_record)
                        
                    embedding_record.embedding = embedding_vals
                    embedding_record.model = embed_usage["model"]
                    
                    embed_usage_record = AIUsage(
                        image_id=image.id,
                        operation=embed_usage["operation"],
                        model=embed_usage["model"],
                        tokens=embed_usage["tokens"],
                        cost=embed_usage["cost"]
                    )
                    self.db.add(embed_usage_record)
                    results["total_tokens"] += embed_usage["tokens"]
                    results["total_cost"] += embed_usage["cost"]
                
                self.db.commit()
                return True

            except Exception as e:
                logger.error(f"Error processing image {image.id} (Attempt {attempt + 1}/{max_retries}): {e}")
                self.db.rollback()
                time.sleep(2 ** attempt) # Exponential backoff for retries

        # If all retries failed, mark as failed
        metadata = self.db.query(ImageMetadata).filter(ImageMetadata.image_id == image.id).first()
        if not metadata:
            metadata = ImageMetadata(image_id=image.id)
            self.db.add(metadata)
        metadata.status = ImageStatus.failed
        self.db.commit()
        results["failed"] += 1
        
        return False
