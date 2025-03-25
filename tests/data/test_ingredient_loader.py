import pytest
from unittest.mock import Mock, patch
import json
from sqlalchemy.orm import Session
from app.models.models import Ingredient
from scripts.data.load_ingredients import IngredientLoader

@pytest.fixture
def mock_session():
    return Mock(spec=Session)

@pytest.fixture
def mock_response():
    mock = Mock()
    mock.json.return_value = {
        "products": [
            {
                "ingredients": [
                    {
                        "text": "Test Ingredient",
                        "allergens": "milk, eggs"
                    }
                ]
            }
        ]
    }
    return mock

@pytest.fixture
def ingredient_loader(mock_session):
    with patch('scripts.data.load_ingredients.create_engine') as mock_engine, \
         patch('scripts.data.load_ingredients.sessionmaker') as mock_sessionmaker:
        mock_sessionmaker.return_value.return_value = mock_session
        loader = IngredientLoader()
        return loader

def test_extract_allergens():
    loader = IngredientLoader()
    
    # Test Open Food Facts format
    data1 = {"allergens": "milk, eggs, nuts"}
    assert set(loader._extract_allergens(data1)) == {"milk", "eggs", "nuts"}
    
    # Test Edamam format
    data2 = {"allergens": ["milk", "eggs"]}
    assert set(loader._extract_allergens(data2)) == {"milk", "eggs"}
    
    # Test USDA format
    data3 = {"allergenName": "milk"}
    assert set(loader._extract_allergens(data3)) == {"milk"}
    
    # Test empty data
    data4 = {}
    assert loader._extract_allergens(data4) == []

def test_get_openfoodfacts_ingredients(ingredient_loader, mock_response):
    with patch('requests.get', return_value=mock_response):
        ingredients = ingredient_loader.get_openfoodfacts_ingredients()
        
        assert len(ingredients) == 1
        assert ingredients[0]["name"] == "Test Ingredient"
        assert "milk" in ingredients[0]["common_allergens"]
        assert "eggs" in ingredients[0]["common_allergens"]
        assert ingredients[0]["source"] == "openfoodfacts"

def test_get_edamam_ingredients(ingredient_loader):
    mock_response = Mock()
    mock_response.json.return_value = {
        "hints": [
            {
                "food": {
                    "label": "Test Ingredient",
                    "allergens": ["milk", "eggs"]
                }
            }
        ]
    }
    
    with patch('requests.get', return_value=mock_response):
        ingredients = ingredient_loader.get_edamam_ingredients("test")
        
        assert len(ingredients) == 1
        assert ingredients[0]["name"] == "Test Ingredient"
        assert "milk" in ingredients[0]["common_allergens"]
        assert "eggs" in ingredients[0]["common_allergens"]
        assert ingredients[0]["source"] == "edamam"

def test_get_usda_ingredients(ingredient_loader):
    mock_response = Mock()
    mock_response.json.return_value = {
        "foods": [
            {
                "description": "Test Ingredient",
                "allergenName": "milk"
            }
        ]
    }
    
    with patch('requests.get', return_value=mock_response):
        ingredients = ingredient_loader.get_usda_ingredients("test")
        
        assert len(ingredients) == 1
        assert ingredients[0]["name"] == "Test Ingredient"
        assert "milk" in ingredients[0]["common_allergens"]
        assert ingredients[0]["source"] == "usda"

def test_save_ingredients(ingredient_loader, mock_session):
    ingredients = [
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
    
    # Mock database query to simulate no existing ingredients
    mock_session.query.return_value.filter.return_value.first.return_value = None
    
    ingredient_loader.save_ingredients(ingredients)
    
    # Verify that add was called twice
    assert mock_session.add.call_count == 2
    
    # Verify that commit was called
    mock_session.commit.assert_called_once()

def test_save_ingredients_duplicates(ingredient_loader, mock_session):
    ingredients = [
        {
            "name": "Test Ingredient",
            "common_allergens": ["milk"],
            "source": "test"
        },
        {
            "name": "Test Ingredient",  # Duplicate
            "common_allergens": ["eggs"],
            "source": "test"
        }
    ]
    
    # Mock database query to simulate existing ingredient
    mock_session.query.return_value.filter.return_value.first.return_value = Ingredient(
        name="Test Ingredient",
        common_allergens=json.dumps(["milk"])
    )
    
    ingredient_loader.save_ingredients(ingredients)
    
    # Verify that add was not called (duplicate)
    mock_session.add.assert_not_called()

def test_error_handling(ingredient_loader):
    with patch('requests.get', side_effect=Exception("API Error")):
        # Test Open Food Facts error handling
        ingredients = ingredient_loader.get_openfoodfacts_ingredients()
        assert ingredients == []
        
        # Test Edamam error handling
        ingredients = ingredient_loader.get_edamam_ingredients("test")
        assert ingredients == []
        
        # Test USDA error handling
        ingredients = ingredient_loader.get_usda_ingredients("test")
        assert ingredients == []

def test_rate_limiting(ingredient_loader):
    with patch('time.sleep') as mock_sleep, \
         patch('requests.get', return_value=Mock(json=lambda: {"products": []})):
        
        # Test rate limiting in Open Food Facts
        ingredient_loader.get_openfoodfacts_ingredients()
        mock_sleep.assert_called_with(1)
        
        # Test rate limiting in category loading
        ingredient_loader.load_all_ingredients()
        assert mock_sleep.call_count > 1  # Should be called multiple times for different categories 