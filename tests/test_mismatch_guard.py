import pytest
from app.models.image import Image, ImageMetadata, ImageEmbedding, ImageStatus
from app.models.post import Post, Match, MatchStatus
from app.services.matching_service import MatchService


class FakeQuery:
    def __init__(self, items):
        self._items = items

    def filter(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def first(self):
        return self._items[0] if self._items else None

    def all(self):
        return list(self._items)


class FakeDB:
    def __init__(self, post=None, candidates=None):
        self.post = post
        self.candidates = candidates or []
        self.added = []

    def query(self, *entities):
        if entities and entities[0] == Post:
            return FakeQuery([self.post] if self.post else [])
        return FakeQuery(self.candidates)

    def add(self, item):
        self.added.append(item)

    def commit(self):
        pass


def test_mismatch_guard_empty_image_library():
    post = Post(id=1, title="Test Post", content="Post content", expected_subject="tech", expected_category="news", embedding=[0.1]*10)
    db = FakeDB(post=post, candidates=[])
    service = MatchService(db)
    match = service.process_post_and_match(1)

    assert match.status == MatchStatus.no_match
    assert "No processed images available" in match.reason
    assert match.image_id is None


def test_mismatch_guard_accepted_match():
    vec = [1.0, 0.0, 0.0]
    post = Post(id=1, title="Fox", content="Fox content", expected_subject="red fox", expected_category="animal", embedding=vec)
    img = Image(id=10, filepath="data/images/fox.jpg")
    meta = ImageMetadata(subject="red fox", category="animal", confidence=0.95, status=ImageStatus.processed)
    emb = ImageEmbedding(embedding=vec)

    db = FakeDB(post=post, candidates=[(img, emb, meta)])
    service = MatchService(db)
    match = service.process_post_and_match(1)

    assert match.status == MatchStatus.pending
    assert match.image_id == 10
    assert "Accepted" in match.reason


def test_mismatch_guard_rejects_low_similarity():
    post = Post(id=1, title="Ocean", content="Ocean content", expected_subject="red fox", expected_category="animal", embedding=[0.0, 1.0, 0.0])
    img = Image(id=10, filepath="data/images/fox.jpg")
    meta = ImageMetadata(subject="red fox", category="animal", confidence=0.95, status=ImageStatus.processed)
    emb = ImageEmbedding(embedding=[1.0, 0.0, 0.0])  # Orthogonal -> sim = 0.0

    db = FakeDB(post=post, candidates=[(img, emb, meta)])
    service = MatchService(db)
    match = service.process_post_and_match(1)

    assert match.status == MatchStatus.no_match
    assert "below threshold" in match.reason
    assert match.image_id is None


def test_mismatch_guard_rejects_low_vision_confidence():
    vec = [1.0, 0.0, 0.0]
    post = Post(id=1, title="Fox", content="Fox content", expected_subject="red fox", expected_category="animal", embedding=vec)
    img = Image(id=10, filepath="data/images/blurry_fox.jpg")
    meta = ImageMetadata(subject="red fox", category="animal", confidence=0.60, status=ImageStatus.processed)  # 0.60 < 0.80
    emb = ImageEmbedding(embedding=vec)

    db = FakeDB(post=post, candidates=[(img, emb, meta)])
    service = MatchService(db)
    match = service.process_post_and_match(1)

    assert match.status == MatchStatus.no_match
    assert "confidence (0.6) is too low" in match.reason
    assert match.image_id is None


def test_mismatch_guard_rejects_subject_mismatch_adversarial():
    vec = [1.0, 0.0, 0.0]
    post = Post(id=1, title="Fox", content="Fox content", expected_subject="red fox", expected_category="animal", embedding=vec)
    img = Image(id=20, filepath="data/images/wolf.jpg")
    meta = ImageMetadata(subject="gray wolf", category="animal", confidence=0.95, status=ImageStatus.processed)
    emb = ImageEmbedding(embedding=vec)  # Same vector, but wrong subject!

    db = FakeDB(post=post, candidates=[(img, emb, meta)])
    service = MatchService(db)
    match = service.process_post_and_match(1)

    assert match.status == MatchStatus.no_match
    assert "Subject mismatch" in match.reason
    assert "expected 'red fox', detected 'gray wolf'" in match.reason
    assert match.image_id is None


def test_mismatch_guard_nonexistent_post_raises_error():
    db = FakeDB(post=None)
    service = MatchService(db)
    with pytest.raises(ValueError, match="Post not found"):
        service.process_post_and_match(9999)
