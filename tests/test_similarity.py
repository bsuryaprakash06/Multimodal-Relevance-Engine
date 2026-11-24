import pytest
import math
from app.services.matching_service import cosine_similarity


def test_cosine_similarity_identical_vectors():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert pytest.approx(cosine_similarity(v1, v2), 1e-5) == 1.0


def test_cosine_similarity_orthogonal_vectors():
    v1 = [1.0, 0.0]
    v2 = [0.0, 1.0]
    assert pytest.approx(cosine_similarity(v1, v2), 1e-5) == 0.0


def test_cosine_similarity_opposite_vectors():
    v1 = [1.0, 2.0, 3.0]
    v2 = [-1.0, -2.0, -3.0]
    assert pytest.approx(cosine_similarity(v1, v2), 1e-5) == -1.0


def test_cosine_similarity_arbitrary_vectors():
    v1 = [1.0, 2.0, 3.0]
    v2 = [4.0, 5.0, 6.0]
    dot = 1*4 + 2*5 + 3*6  # 32
    mag1 = math.sqrt(1 + 4 + 9)  # sqrt(14)
    mag2 = math.sqrt(16 + 25 + 36)  # sqrt(77)
    expected = dot / (mag1 * mag2)
    assert pytest.approx(cosine_similarity(v1, v2), 1e-5) == expected


def test_cosine_similarity_zero_vector():
    v1 = [0.0, 0.0, 0.0]
    v2 = [1.0, 2.0, 3.0]
    assert cosine_similarity(v1, v2) == 0.0
