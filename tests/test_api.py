import pytest
from fastapi import HTTPException
from app.main import (
    read_root,
    health_check,
    create_post,
    list_reviews,
    get_review,
    submit_review,
    PostCreate,
    ReviewDecision
)
from app.models.post import Post, Match, MatchStatus


class FakeQuery:
    def __init__(self, items):
        self._items = items

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._items[0] if self._items else None

    def all(self):
        return list(self._items)


class FakeAPIDB:
    def __init__(self, items=None):
        self.items = items or []
        self.added = []

    def query(self, entity):
        return FakeQuery(self.items)

    def add(self, item):
        self.added.append(item)

    def commit(self):
        pass

    def refresh(self, item):
        if not hasattr(item, "id") or item.id is None:
            item.id = 1


def test_api_root():
    res = read_root()
    assert res["status"] == "online"
    assert "Multimodal Relevance Engine" in res["message"]


def test_api_health():
    res = health_check()
    assert res["status"] == "ok"


def test_api_create_post():
    db = FakeAPIDB()
    post_in = PostCreate(title="Testing FastAPI", content="Content of post")
    res = create_post(post=post_in, db=db)
    assert res["id"] == 1
    assert res["title"] == "Testing FastAPI"


def test_api_list_reviews():
    match = Match(id=1, post_id=1, image_id=10, status=MatchStatus.pending, reason="Good match", human_reviewed=False)
    db = FakeAPIDB([match])
    res = list_reviews(db=db)
    assert len(res) == 1
    assert res[0].human_reviewed is False


def test_api_get_review_success():
    match = Match(id=1, post_id=1, image_id=10, status=MatchStatus.pending, reason="Good match", human_reviewed=False)
    db = FakeAPIDB([match])
    res = get_review(match_id=1, db=db)
    assert res.id == 1


def test_api_get_review_not_found():
    db = FakeAPIDB([])
    with pytest.raises(HTTPException) as exc_info:
        get_review(match_id=999, db=db)
    assert exc_info.value.status_code == 404


def test_api_submit_review_approve():
    match = Match(id=1, post_id=1, image_id=10, status=MatchStatus.pending, reason="Good match", human_reviewed=False)
    db = FakeAPIDB([match])
    decision = ReviewDecision(approve=True)
    res = submit_review(match_id=1, decision=decision, db=db)
    assert res.status == MatchStatus.accepted
    assert res.human_reviewed is True


def test_api_submit_review_reject():
    match = Match(id=1, post_id=1, image_id=10, status=MatchStatus.pending, reason="Good match", human_reviewed=False)
    db = FakeAPIDB([match])
    decision = ReviewDecision(approve=False)
    res = submit_review(match_id=1, decision=decision, db=db)
    assert res.status == MatchStatus.rejected
    assert res.human_reviewed is True
