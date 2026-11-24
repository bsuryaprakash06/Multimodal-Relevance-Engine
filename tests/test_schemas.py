import pytest
from pydantic import ValidationError
from app.schemas.image import ImageMetadataSchema
from app.main import PostCreate, ReviewDecision, MatchResponse


def test_image_metadata_schema_valid():
    data = {
        "subject": "red fox",
        "category": "animal",
        "attributes": ["wild", "orange fur", "forest"],
        "caption": "A red fox in the snow",
        "confidence": 0.94
    }
    schema = ImageMetadataSchema(**data)
    assert schema.subject == "red fox"
    assert schema.confidence == 0.94


def test_image_metadata_schema_invalid_confidence():
    # Confidence must be between 0.0 and 1.0
    with pytest.raises(ValidationError):
        ImageMetadataSchema(
            subject="fox",
            category="animal",
            attributes=[],
            caption="test",
            confidence=1.5
        )


def test_post_create_schema():
    post = PostCreate(title="Test Title", content="Test Content")
    assert post.title == "Test Title"
    assert post.content == "Test Content"


def test_review_decision_schema():
    decision = ReviewDecision(approve=True)
    assert decision.approve is True

    decision_reject = ReviewDecision(approve=False)
    assert decision_reject.approve is False


def test_match_response_schema():
    resp = MatchResponse(
        id=1,
        post_id=10,
        image_id=5,
        status="accepted",
        reason="Good match",
        human_reviewed=False
    )
    assert resp.id == 1
    assert resp.image_id == 5
