import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Base, Ingredient
from scripts.data.load_ingredients import IngredientLoader
from app.core.config import settings
import json
import os
from typing import Generator

@pytest.fixture(scope="session")
def engine():
    """Create a test database engine"""
    # Use a test database URL
    test_db_url = settings.DATABASE_URL.replace("food_db", "food_test_db")
    engine = create_engine(test_db_url)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Clean up after tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(engine) -> Generator:
    """Create a fresh database session for each test"""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def ingredient_loader(db_session):
    """Create an IngredientLoader instance with test database session"""
    loader = IngredientLoader()
    loader.SessionLocal = lambda: db_session
    return loader

@pytest.mark.integration
def test_openfoodfacts_integration(ingredient_loader):
    """Test integration with Open Food Facts API"""
    # Skip if no API key is available
    if not os.getenv("OPENFOODFACTS_API_KEY"):
        pytest.skip("Open Food Facts API key not available")
    
    # Test with a known product
    ingredients = ingredient_loader.get_openfoodfacts_ingredients(page=1, page_size=10)
    
    assert len(ingredients) > 0
    assert all(isinstance(ing["name"], str) for ing in ingredients)
    assert all(isinstance(ing["common_allergens"], list) for ing in ingredients)
    assert all(isinstance(ing["source"], str) for ing in ingredients)

@pytest.mark.integration
def test_edamam_integration(ingredient_loader):
    """Test integration with Edamam API"""
    # Skip if no API key is available
    if not os.getenv("EDAMAM_APP_ID") or not os.getenv("EDAMAM_APP_KEY"):
        pytest.skip("Edamam API keys not available")
    
    # Test with common ingredients
    test_ingredients = ["apple", "chicken", "rice"]
    all_ingredients = []
    
    for ingredient in test_ingredients:
        ingredients = ingredient_loader.get_edamam_ingredients(ingredient)
        all_ingredients.extend(ingredients)
    
    assert len(all_ingredients) > 0
    assert all(isinstance(ing["name"], str) for ing in all_ingredients)
    assert all(isinstance(ing["common_allergens"], list) for ing in all_ingredients)
    assert all(ing["source"] == "edamam" for ing in all_ingredients)

@pytest.mark.integration
def test_usda_integration(ingredient_loader):
    """Test integration with USDA API"""
    # Skip if no API key is available
    if not os.getenv("USDA_API_KEY"):
        pytest.skip("USDA API key not available")
    
    # Test with common ingredients
    test_ingredients = ["apple", "chicken", "rice"]
    all_ingredients = []
    
    for ingredient in test_ingredients:
        ingredients = ingredient_loader.get_usda_ingredients(ingredient)
        all_ingredients.extend(ingredients)
    
    assert len(all_ingredients) > 0
    assert all(isinstance(ing["name"], str) for ing in all_ingredients)
    assert all(isinstance(ing["common_allergens"], list) for ing in all_ingredients)
    assert all(ing["source"] == "usda" for ing in all_ingredients)

@pytest.mark.integration
def test_database_integration(ingredient_loader, db_session):
    """Test database operations with real database"""
    # Prepare test data
    test_ingredients = [
        {
            "name": "Test Ingredient 1",
            "common_allergens": ["milk", "eggs"],
            "source": "test"
        },
        {
            "name": "Test Ingredient 2",
            "common_allergens": ["nuts"],
            "source": "test"
        }
    ]
    
    # Save ingredients
    ingredient_loader.save_ingredients(test_ingredients)
    
    # Verify saved data
    saved_ingredients = db_session.query(Ingredient).all()
    assert len(saved_ingredients) == 2
    
    # Check first ingredient
    ing1 = db_session.query(Ingredient).filter_by(name="Test Ingredient 1").first()
    assert ing1 is not None
    assert json.loads(ing1.common_allergens) == ["milk", "eggs"]
    assert ing1.source == "test"
    
    # Check second ingredient
    ing2 = db_session.query(Ingredient).filter_by(name="Test Ingredient 2").first()
    assert ing2 is not None
    assert json.loads(ing2.common_allergens) == ["nuts"]
    assert ing2.source == "test"

@pytest.mark.integration
def test_full_pipeline_integration(ingredient_loader, db_session):
    """Test the complete ingredient loading pipeline"""
    # Skip if any required API keys are missing
    required_keys = ["OPENFOODFACTS_API_KEY", "EDAMAM_APP_ID", "EDAMAM_APP_KEY", "USDA_API_KEY"]
    if not all(os.getenv(key) for key in required_keys):
        pytest.skip("Required API keys not available")
    
    # Run the full pipeline
    ingredient_loader.load_all_ingredients()
    
    # Verify results
    saved_ingredients = db_session.query(Ingredient).all()
    assert len(saved_ingredients) > 0
    
    # Check data quality
    for ingredient in saved_ingredients:
        assert isinstance(ingredient.name, str)
        assert len(ingredient.name) > 0
        assert isinstance(ingredient.common_allergens, str)
        allergens = json.loads(ingredient.common_allergens)
        assert isinstance(allergens, list)
        assert ingredient.source in ["openfoodfacts", "edamam", "usda"]

@pytest.mark.integration
def test_error_handling_integration(ingredient_loader):
    """Test error handling with real API calls"""
    # Test with invalid API keys
    original_edamam_id = ingredient_loader.edamam_app_id
    ingredient_loader.edamam_app_id = "invalid_key"
    
    try:
        ingredients = ingredient_loader.get_edamam_ingredients("test")
        assert len(ingredients) == 0  # Should handle error gracefully
    finally:
        ingredient_loader.edamam_app_id = original_edamam_id
    
    # Test with invalid USDA key
    original_usda_key = ingredient_loader.usda_api_key
    ingredient_loader.usda_api_key = "invalid_key"
    
    try:
        ingredients = ingredient_loader.get_usda_ingredients("test")
        assert len(ingredients) == 0  # Should handle error gracefully
    finally:
        ingredient_loader.usda_api_key = original_usda_key

@pytest.mark.integration
def test_rate_limiting_integration(ingredient_loader):
    """Test rate limiting with real API calls"""
    import time
    
    # Test Open Food Facts rate limiting
    start_time = time.time()
    for _ in range(3):
        ingredient_loader.get_openfoodfacts_ingredients(page=1, page_size=10)
    end_time = time.time()
    
    # Should take at least 2 seconds due to rate limiting
    assert end_time - start_time >= 2
    
    # Test category loading rate limiting
    start_time = time.time()
    ingredient_loader.load_all_ingredients()
    end_time = time.time()
    
    # Should take at least 1 second per category
    assert end_time - start_time >= 10  # 10 categories 