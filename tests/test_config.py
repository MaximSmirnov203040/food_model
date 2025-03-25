"""Basic tests to verify test configuration."""
import os
import pytest
from app.core.config import Settings

def test_test_environment():
    """Verify that we're running in test environment with correct configuration."""
    assert os.getenv("DATABASE_URL") is not None, "DATABASE_URL must be set"
    assert os.getenv("SECRET_KEY") is not None, "SECRET_KEY must be set"
    assert os.getenv("ALGORITHM") == "HS256", "ALGORITHM must be set to HS256"
    
    settings = Settings()
    assert settings.database_url.endswith("food_test_db"), "Must use test database"
    assert settings.secret_key == "test_secret_key", "Must use test secret key"

@pytest.mark.unit
def test_basic_addition():
    """Basic test to verify pytest is working."""
    assert 1 + 1 == 2, "Basic arithmetic should work"

@pytest.mark.integration
def test_database_connection(db_session):
    """Verify database connection is working."""
    assert db_session is not None, "Database session should be available"
    
    # Try a simple query
    result = db_session.execute("SELECT 1")
    assert result.scalar() == 1, "Should be able to execute queries" 