import pytest
from sqlalchemy.orm import Session
from app.models.models import User, Recipe, Ingredient
from app.services.recommendation import RecommendationService
import json
import numpy as np

@pytest.fixture
def recommendation_service(db_session: Session):
    return RecommendationService(db_session)

@pytest.fixture
def test_user(db_session: Session):
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        dietary_restrictions=["vegetarian"],
        favorite_cuisines=["italian", "japanese"],
        allergies=["nuts"],
        food_flags=["high_sodium"]
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_recipes(db_session: Session):
    recipes = [
        Recipe(
            name="Italian Pasta",
            description="Classic Italian pasta",
            ingredients=json.dumps(["pasta", "tomato", "cheese"]),
            instructions=json.dumps(["step1", "step2"]),
            calories=600,
            protein=20,
            carbs=80,
            fat=15,
            food_flags=json.dumps(["high_sodium"]),
            cuisine="italian"
        ),
        Recipe(
            name="Sushi Roll",
            description="Japanese sushi",
            ingredients=json.dumps(["rice", "fish", "seaweed"]),
            instructions=json.dumps(["step1", "step2"]),
            calories=400,
            protein=15,
            carbs=60,
            fat=10,
            food_flags=json.dumps([]),
            cuisine="japanese"
        ),
        Recipe(
            name="Nutty Salad",
            description="Salad with nuts",
            ingredients=json.dumps(["lettuce", "nuts", "dressing"]),
            instructions=json.dumps(["step1", "step2"]),
            calories=300,
            protein=10,
            carbs=20,
            fat=25,
            food_flags=json.dumps(["high_fat"]),
            cuisine="mediterranean"
        )
    ]
    for recipe in recipes:
        db_session.add(recipe)
    db_session.commit()
    return recipes

@pytest.fixture
def test_ingredients(db_session: Session):
    ingredients = [
        Ingredient(
            name="pasta",
            common_allergens=json.dumps(["gluten"]),
            source="test"
        ),
        Ingredient(
            name="cheese",
            common_allergens=json.dumps(["dairy"]),
            source="test"
        ),
        Ingredient(
            name="nuts",
            common_allergens=json.dumps(["nuts"]),
            source="test"
        )
    ]
    for ingredient in ingredients:
        db_session.add(ingredient)
    db_session.commit()
    return ingredients

@pytest.mark.integration
def test_get_recipe_features(recommendation_service, test_recipes):
    """Test recipe feature extraction"""
    features = recommendation_service.get_recipe_features(test_recipes[0])
    
    assert isinstance(features, np.ndarray)
    assert len(features) == 6  # calories, protein, carbs, fat, sodium, sugar
    assert features[0] == test_recipes[0].calories
    assert features[1] == test_recipes[0].protein
    assert features[2] == test_recipes[0].carbs
    assert features[3] == test_recipes[0].fat

@pytest.mark.integration
def test_get_user_preferences(recommendation_service, test_user):
    """Test user preference extraction"""
    preferences = recommendation_service.get_user_preferences(test_user)
    
    assert isinstance(preferences, dict)
    assert preferences["dietary_restrictions"] == test_user.dietary_restrictions
    assert preferences["favorite_cuisines"] == test_user.favorite_cuisines
    assert preferences["allergies"] == test_user.allergies
    assert preferences["food_flags"] == test_user.food_flags

@pytest.mark.integration
def test_check_recipe_allergens(recommendation_service, test_recipes, test_ingredients):
    """Test allergen checking"""
    # Test recipe with allergens
    has_allergens = recommendation_service.check_recipe_allergens(
        test_recipes[2],  # Nutty Salad
        {"allergies": ["nuts"]}
    )
    assert has_allergens is True
    
    # Test recipe without allergens
    has_allergens = recommendation_service.check_recipe_allergens(
        test_recipes[0],  # Italian Pasta
        {"allergies": ["nuts"]}
    )
    assert has_allergens is False

@pytest.mark.integration
def test_check_food_flags(recommendation_service, test_recipes):
    """Test food flag checking"""
    # Test recipe with flagged food
    has_flags = recommendation_service.check_food_flags(
        test_recipes[0],  # Italian Pasta with high_sodium
        {"food_flags": ["high_sodium"]}
    )
    assert has_flags is True
    
    # Test recipe without flagged food
    has_flags = recommendation_service.check_food_flags(
        test_recipes[1],  # Sushi Roll with no flags
        {"food_flags": ["high_sodium"]}
    )
    assert has_flags is False

@pytest.mark.integration
def test_filter_by_preferences(recommendation_service, test_recipes, test_user):
    """Test recipe filtering based on user preferences"""
    filtered_recipes = recommendation_service.filter_by_preferences(
        test_recipes,
        recommendation_service.get_user_preferences(test_user)
    )
    
    # Should exclude Nutty Salad due to nut allergy
    assert len(filtered_recipes) == 2
    assert all(recipe.name != "Nutty Salad" for recipe in filtered_recipes)
    
    # Should prefer Italian and Japanese recipes
    assert any(recipe.cuisine == "italian" for recipe in filtered_recipes)
    assert any(recipe.cuisine == "japanese" for recipe in filtered_recipes)

@pytest.mark.integration
def test_get_recommendations(recommendation_service, test_recipes, test_user):
    """Test recommendation generation"""
    recommendations = recommendation_service.get_recommendations(
        test_user,
        limit=2
    )
    
    assert len(recommendations) <= 2
    assert all(isinstance(recipe, Recipe) for recipe in recommendations)
    assert all(recipe.name != "Nutty Salad" for recipe in recommendations)  # Should exclude due to allergy

@pytest.mark.integration
def test_recommendation_ranking(recommendation_service, test_recipes, test_user):
    """Test recommendation ranking"""
    recommendations = recommendation_service.get_recommendations(
        test_user,
        limit=3
    )
    
    # Should prefer recipes matching user's favorite cuisines
    italian_recipes = [r for r in recommendations if r.cuisine == "italian"]
    japanese_recipes = [r for r in recommendations if r.cuisine == "japanese"]
    
    assert len(italian_recipes) > 0
    assert len(japanese_recipes) > 0

@pytest.mark.integration
def test_empty_recommendations(recommendation_service, test_user):
    """Test recommendation generation with no recipes"""
    recommendations = recommendation_service.get_recommendations(
        test_user,
        limit=5
    )
    assert len(recommendations) == 0

@pytest.mark.integration
def test_strict_filtering(recommendation_service, test_recipes, test_user):
    """Test strict filtering with multiple restrictions"""
    # Add more restrictions to user
    test_user.dietary_restrictions = ["vegan"]
    test_user.allergies = ["nuts", "dairy"]
    test_user.food_flags = ["high_sodium", "high_fat"]
    
    filtered_recipes = recommendation_service.filter_by_preferences(
        test_recipes,
        recommendation_service.get_user_preferences(test_user)
    )
    
    # Should exclude all recipes due to strict restrictions
    assert len(filtered_recipes) == 0 