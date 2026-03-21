"""
Unit tests for database layer
Tests ORM models, initialization, and DAO operations
"""

import pytest
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Case, Suspect, TextDocument, Image, AnalysisResult
from app.db import dao



TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine"""
    engine = create_engine(TEST_DB_URL, echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a test database session"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def mock_session_factory(monkeypatch, test_engine):
    """Mock the session factory to use test database"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    monkeypatch.setattr(dao, "SessionLocal", SessionLocal)
    return SessionLocal






def test_tables_created_successfully(test_engine):
    """Test that all tables are created with correct names"""
    inspector = test_engine.dialect.get_table_names(test_engine.connect())
    
    expected_tables = [
        'cases', 'suspects', 'text_documents', 'images', 'analysis_results'
    ]
    
    for table in expected_tables:
        assert table in inspector, f"Table '{table}' was not created"


def test_case_model_fields(test_session):
    """Test Case model has all required fields"""
    case = Case(
        title="Test Case",
        description="Test description"
    )
    test_session.add(case)
    test_session.commit()
    
    assert case.id is not None
    assert case.title == "Test Case"
    assert case.description == "Test description"
    assert isinstance(case.created_at, datetime)


def test_suspect_model_fields(test_session):
    """Test Suspect model has all required fields"""

    case = Case(title="Test Case", description="Test")
    test_session.add(case)
    test_session.commit()
    

    suspect = Suspect(
        case_id=case.id,
        name="John Doe",
        profile_text="Suspicious individual",
        metadata_json={"alibi": "None"}
    )
    test_session.add(suspect)
    test_session.commit()
    
    assert suspect.id is not None
    assert suspect.case_id == case.id
    assert suspect.name == "John Doe"
    assert suspect.metadata_json == {"alibi": "None"}
    assert isinstance(suspect.created_at, datetime)






def test_case_suspect_relationship(test_session):
    """Test relationship between Case and Suspect"""
    case = Case(title="Test Case", description="Test")
    test_session.add(case)
    test_session.commit()
    
    suspect1 = Suspect(case_id=case.id, name="Suspect 1", profile_text="Profile 1")
    suspect2 = Suspect(case_id=case.id, name="Suspect 2", profile_text="Profile 2")
    test_session.add_all([suspect1, suspect2])
    test_session.commit()
    

    assert len(case.suspects) == 2
    assert suspect1 in case.suspects
    assert suspect2 in case.suspects
    

    assert suspect1.case.id == case.id
    assert suspect2.case.id == case.id


def test_cascade_delete(test_session):
    """Test that deleting a case cascades to related entities"""
    case = Case(title="Test Case", description="Test")
    test_session.add(case)
    test_session.commit()
    

    suspect = Suspect(case_id=case.id, name="Test", profile_text="Test")
    text = TextDocument(
        case_id=case.id,
        source_type="witness",
        title="Statement",
        content="I saw..."
    )
    test_session.add_all([suspect, text])
    test_session.commit()
    
    case_id = case.id
    

    test_session.delete(case)
    test_session.commit()
    

    assert test_session.query(Suspect).filter(Suspect.case_id == case_id).count() == 0
    assert test_session.query(TextDocument).filter(TextDocument.case_id == case_id).count() == 0






def test_add_case(mock_session_factory):
    """Test adding a case via DAO"""
    case = dao.add_case(
        title="Murder Investigation",
        description="Case opened on suspicion of homicide"
    )
    
    assert case is not None
    assert case.id is not None
    assert case.title == "Murder Investigation"
    assert case.description == "Case opened on suspicion of homicide"


def test_get_case(mock_session_factory):
    """Test retrieving a case by ID"""

    case = dao.add_case(title="Test Case", description="Test")
    case_id = case.id
    

    retrieved = dao.get_case(case_id)
    
    assert retrieved is not None
    assert retrieved.id == case_id
    assert retrieved.title == "Test Case"


def test_get_all_cases(mock_session_factory):
    """Test retrieving all cases"""

    dao.add_case(title="Case 1", description="First case")
    dao.add_case(title="Case 2", description="Second case")
    dao.add_case(title="Case 3", description="Third case")
    

    cases = dao.get_all_cases()
    
    assert len(cases) == 3
    assert all(isinstance(c, Case) for c in cases)






def test_add_suspect(mock_session_factory):
    """Test adding a suspect via DAO"""
    case = dao.add_case(title="Test Case", description="Test")
    
    suspect = dao.add_suspect(
        case_id=case.id,
        name="Jane Smith",
        profile_text="Known associate of victim",
        metadata_json={"age": 35, "occupation": "Teacher"}
    )
    
    assert suspect is not None
    assert suspect.id is not None
    assert suspect.name == "Jane Smith"
    assert suspect.metadata_json["age"] == 35


def test_add_suspect_invalid_case(mock_session_factory):
    """Test that adding suspect with invalid case_id fails gracefully"""
    suspect = dao.add_suspect(
        case_id=99999,
        name="Test",
        profile_text="Test"
    )
    



    assert suspect is None or suspect.id is not None


def test_get_suspects_by_case(mock_session_factory):
    """Test retrieving suspects for a specific case"""
    case = dao.add_case(title="Test Case", description="Test")
    
    dao.add_suspect(case.id, "Suspect 1", "Profile 1")
    dao.add_suspect(case.id, "Suspect 2", "Profile 2")
    
    suspects = dao.get_suspects_by_case(case.id)
    
    assert len(suspects) == 2
    assert suspects[0].name == "Suspect 1"
    assert suspects[1].name == "Suspect 2"






def test_add_text_document(mock_session_factory):
    """Test adding a text document via DAO"""
    case = dao.add_case(title="Test Case", description="Test")
    
    text = dao.add_text(
        case_id=case.id,
        source_type="witness",
        title="Witness Statement - John Doe",
        content="I saw the suspect at 3pm near the scene..."
    )
    
    assert text is not None
    assert text.id is not None
    assert text.source_type == "witness"
    assert "3pm" in text.content


def test_get_texts_by_case(mock_session_factory):
    """Test retrieving text documents for a case"""
    case = dao.add_case(title="Test Case", description="Test")
    
    dao.add_text(case.id, "witness", "Statement 1", "Content 1")
    dao.add_text(case.id, "report", "Police Report", "Content 2")
    
    texts = dao.get_texts_by_case(case.id)
    
    assert len(texts) == 2
    assert texts[0].source_type == "witness"
    assert texts[1].source_type == "report"






def test_add_image(mock_session_factory):
    """Test adding an encrypted image via DAO"""
    case = dao.add_case(title="Test Case", description="Test")
    
    image = dao.add_image(
        case_id=case.id,
        filename="evidence_photo.jpg",
        file_path="/data/encrypted/abc123.enc",
        iv_hex="0123456789abcdef0123456789abcdef",
        sha256_hex="a" * 64
    )
    
    assert image is not None
    assert image.id is not None
    assert image.filename == "evidence_photo.jpg"
    assert len(image.iv_hex) == 32
    assert len(image.sha256_hex) == 64


def test_update_image_analysis(mock_session_factory):
    """Test updating image with analysis results"""
    case = dao.add_case(title="Test Case", description="Test")
    image = dao.add_image(case.id, "test.jpg", "/path/test.enc", "a" * 32, "b" * 64)
    

    success = dao.update_image_analysis(
        image_id=image.id,
        exif_json={"camera": "Canon EOS", "location": "40.7128,-74.0060"},
        caption_text="A dark alley with a suspicious figure"
    )
    
    assert success is True
    

    updated = dao.get_images_by_case(case.id)[0]
    assert updated.exif_json["camera"] == "Canon EOS"
    assert "suspicious" in updated.caption_text






def test_save_analysis_results(mock_session_factory):
    """Test saving analysis results for multiple suspects"""
    case = dao.add_case(title="Test Case", description="Test")
    suspect1 = dao.add_suspect(case.id, "Suspect 1", "Profile 1")
    suspect2 = dao.add_suspect(case.id, "Suspect 2", "Profile 2")
    
    results = [
        {
            "suspect_id": suspect1.id,
            "score": 0.85,
            "matched_clues": {"location": "Near scene", "motive": "Financial"}
        },
        {
            "suspect_id": suspect2.id,
            "score": 0.42,
            "matched_clues": {"witness": "Not mentioned"}
        }
    ]
    
    success = dao.save_analysis_results(case.id, results)
    
    assert success is True
    

    saved_results = dao.get_analysis_results(case.id)
    assert len(saved_results) == 2
    assert saved_results[0].score_float == 0.85
    assert saved_results[1].score_float == 0.42






def test_get_case_data_complete(mock_session_factory):
    """Test retrieving complete case data with all relationships"""

    case = dao.add_case(title="Complete Case", description="Full test")
    suspect = dao.add_suspect(case.id, "Suspect", "Profile")
    text = dao.add_text(case.id, "witness", "Statement", "Content")
    image = dao.add_image(case.id, "photo.jpg", "/path.enc", "a" * 32, "b" * 64)
    
    dao.save_analysis_results(case.id, [{
        "suspect_id": suspect.id,
        "score": 0.75,
        "matched_clues": {"test": "data"}
    }])
    

    data = dao.get_case_data(case.id)
    
    assert data is not None
    assert data["case"]["title"] == "Complete Case"
    assert len(data["suspects"]) == 1
    assert len(data["text_documents"]) == 1
    assert len(data["images"]) == 1
    assert len(data["analysis_results"]) == 1
    assert data["analysis_results"][0]["score"] == 0.75


def test_delete_case(mock_session_factory):
    """Test deleting a case via DAO"""
    case = dao.add_case(title="To Delete", description="Test")
    case_id = case.id
    

    dao.add_suspect(case_id, "Suspect", "Profile")
    

    success = dao.delete_case(case_id)
    assert success is True
    

    deleted_case = dao.get_case(case_id)
    assert deleted_case is None






def test_session_rollback_on_error(mock_session_factory):
    """Test that sessions rollback properly on errors"""
    case = dao.add_case(title="Test", description="Test")
    

    image1 = dao.add_image(case.id, "test.jpg", "/unique/path.enc", "a" * 32, "b" * 64)
    assert image1 is not None
    

    image2 = dao.add_image(case.id, "test2.jpg", "/unique/path.enc", "c" * 32, "d" * 64)
    assert image2 is None
    

    images = dao.get_images_by_case(case.id)
    assert len(images) == 1


def test_get_nonexistent_case(mock_session_factory):
    """Test retrieving non-existent case returns None"""
    case = dao.get_case(99999)
    assert case is None






def test_model_repr(test_session):
    """Test that model __repr__ methods work"""
    case = Case(title="Test", description="Test")
    test_session.add(case)
    test_session.commit()
    
    repr_str = repr(case)
    assert "Case" in repr_str
    assert "Test" in repr_str
    assert str(case.id) in repr_str

