import math
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models.image import Image, ImageEmbedding, ImageMetadata, AIUsage, ImageStatus
from app.models.post import Post, Match, MatchStatus
from app.services.embedding_service import EmbeddingService
from app.providers.vision.post_understanding import PostUnderstandingProvider

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(a * a for a in v2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)

class MatchService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.post_provider = PostUnderstandingProvider()
        # Development thresholds
        self.similarity_threshold = 0.50
        self.confidence_threshold = 0.8
        
    def process_post_and_match(self, post_id: int) -> Match:
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise ValueError("Post not found")
            
        # 1. Post Understanding (if not done)
        if not post.expected_subject:
            meta, usage = self.post_provider.analyze_post(post.content)
            post.expected_subject = meta.subject
            post.expected_category = meta.category
            
            self._log_usage(usage, post_id=post.id)
            self.db.commit()
            
        # 2. Post Embedding (if not done)
        if not post.embedding:
            emb, usage = self.embedding_service.generate_post_embedding(post.content)
            post.embedding = emb
            self._log_usage(usage, post_id=post.id)
            self.db.commit()
            
        # 3. Retrieve all valid image embeddings
        candidates = self.db.query(Image, ImageEmbedding, ImageMetadata).join(
            ImageEmbedding, Image.id == ImageEmbedding.image_id
        ).join(
            ImageMetadata, Image.id == ImageMetadata.image_id
        ).filter(
            ImageMetadata.status == ImageStatus.processed # Only consider processed ones
        ).all()
        
        if not candidates:
            return self._create_no_match(post.id, "No processed images available in library.")
            
        # 4. Rank Candidates
        ranked = []
        for img, emb_record, meta_record in candidates:
            sim = cosine_similarity(post.embedding, emb_record.embedding)
            ranked.append((sim, img, meta_record))
            
        ranked.sort(key=lambda x: x[0], reverse=True)
        top_sim, top_img, top_meta = ranked[0]
        
        # 5. Mismatch Guard
        # Check similarity
        if top_sim < self.similarity_threshold:
            return self._create_no_match(post.id, f"Best match similarity ({top_sim:.2f}) is below threshold ({self.similarity_threshold}).")
            
        # Check confidence
        if top_meta.confidence is None or top_meta.confidence < self.confidence_threshold:
            return self._create_no_match(post.id, f"Candidate image vision confidence ({top_meta.confidence}) is too low.")
            
        # Check subject/category mismatch
        expected_cat = (post.expected_category or "").lower()
        candidate_cat = (top_meta.category or "").lower()
        # if expected_cat and candidate_cat and expected_cat not in candidate_cat and candidate_cat not in expected_cat:
        #     return self._create_no_match(post.id, f"Category mismatch: expected '{expected_cat}', detected '{candidate_cat}'.")
            
        expected_sub = (post.expected_subject or "").lower()
        candidate_sub = (top_meta.subject or "").lower()
        # Ensure semantic concepts don't hard clash if words slightly differ
        # (A real prod app uses LLM here, but soft substring works for our capstone data)
        if expected_sub and candidate_sub and expected_sub not in candidate_sub and candidate_sub not in expected_sub:
            return self._create_no_match(post.id, f"Subject mismatch: expected '{expected_sub}', detected '{candidate_sub}'.")
            
        # All checks pass
        match = Match(
            post_id=post.id,
            image_id=top_img.id,
            status=MatchStatus.pending, # wait for human review
            reason=f"Accepted. Similarity: {top_sim:.2f}, Subject match: {candidate_sub}."
        )
        self.db.add(match)
        self.db.commit()
        
        return match
        
    def _create_no_match(self, post_id: int, reason: str) -> Match:
        match = Match(
            post_id=post_id,
            image_id=None,
            status=MatchStatus.no_match,
            reason=reason
        )
        self.db.add(match)
        self.db.commit()
        return match

    def _log_usage(self, usage: dict, post_id: int):
        u = AIUsage(
            image_id=None, 
            operation=usage["operation"],
            model=usage["model"],
            tokens=usage["tokens"],
            cost=usage["cost"]
        )
        self.db.add(u)
