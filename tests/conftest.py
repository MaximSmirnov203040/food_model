import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Base
from app.core.config import settings

def pytest_configure(config):
    """Configure test environment"""
    # Set test database URL
    test_db_url = settings.DATABASE_URL.replace("food_db", "food_test_db")
    os.environ["TEST_DATABASE_URL"] = test_db_url

@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine"""
    test_db_url = os.getenv("TEST_DATABASE_URL")
    engine = create_engine(test_db_url)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Clean up after tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a fresh database session for each test"""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    # Store original environment variables
    original_env = {}
    for key in ["DATABASE_URL", "EDAMAM_APP_ID", "EDAMAM_APP_KEY", "USDA_API_KEY"]:
        if key in os.environ:
            original_env[key] = os.environ[key]
    
    # Set test environment variables
    os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL")
    
    yield
    
    # Restore original environment variables
    for key, value in original_env.items():
        os.environ[key] = value
    for key in ["DATABASE_URL", "EDAMAM_APP_ID", "EDAMAM_APP_KEY", "USDA_API_KEY"]:
        if key not in original_env and key in os.environ:
            del os.environ[key] 