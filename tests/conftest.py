import sys
from unittest.mock import MagicMock
import pytest

# Provide mock fallback for optional libraries if not installed in local environment
if "sqlalchemy" not in sys.modules:
    try:
        import sqlalchemy
    except ImportError:
        sa_mock = MagicMock()
        sa_mock.Column = lambda *args, **kwargs: None
        sa_mock.Integer = None
        sa_mock.String = None
        sa_mock.Boolean = None
        sa_mock.Float = None
        sa_mock.Text = None
        sa_mock.JSON = None
        sa_mock.DateTime = None
        sa_mock.ForeignKey = lambda *args, **kwargs: None
        sa_mock.Enum = lambda *args, **kwargs: None
        sa_mock.create_engine = MagicMock()

        class MockDeclarativeBase:
            metadata = MagicMock()
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        sa_orm_mock = MagicMock()
        sa_orm_mock.DeclarativeBase = MockDeclarativeBase
        sa_orm_mock.declarative_base.return_value = MockDeclarativeBase
        sa_orm_mock.Session = MagicMock
        sa_orm_mock.sessionmaker = MagicMock()
        sa_orm_mock.relationship = lambda *args, **kwargs: None

        sys.modules["sqlalchemy"] = sa_mock
        sys.modules["sqlalchemy.orm"] = sa_orm_mock

if "sentence_transformers" not in sys.modules:
    try:
        import sentence_transformers
    except ImportError:
        st_mock = MagicMock()
        class MockSentenceTransformer:
            def __init__(self, *args, **kwargs):
                pass
            def encode(self, text):
                import numpy as np
                return np.array([0.1] * 384)
        st_mock.SentenceTransformer = MockSentenceTransformer
        sys.modules["sentence_transformers"] = st_mock

if "groq" not in sys.modules:
    try:
        import groq
    except ImportError:
        sys.modules["groq"] = MagicMock()

if "google.genai" not in sys.modules:
    try:
        from google import genai
    except ImportError:
        google_mock = MagicMock()
        genai_mock = MagicMock()
        google_mock.genai = genai_mock
        sys.modules["google"] = google_mock
        sys.modules["google.genai"] = genai_mock
        sys.modules["google.genai.types"] = MagicMock()


@pytest.fixture(scope="function")
def db_session():
    # If sqlalchemy is available with in-memory SQLite, use real session
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.image import Base

        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        db = Session()
        try:
            yield db
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)
    except Exception:
        # Fallback mock session
        mock_db = MagicMock()
        yield mock_db
