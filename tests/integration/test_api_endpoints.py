import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.models import User, Recipe, Ingredient
from app.core.security import create_access_token
import json

@pytest.fixture
def client():
    return TestClient(app)

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
def test_recipe(db_session: Session):
    recipe = Recipe(
        name="Test Recipe",
        description="Test Description",
        ingredients=json.dumps(["ingredient1", "ingredient2"]),
        instructions=json.dumps(["step1", "step2"]),
        calories=500,
        protein=20,
        carbs=60,
        fat=15,
        food_flags=json.dumps(["high_sodium"])
    )
    db_session.add(recipe)
    db_session.commit()
    return recipe

@pytest.fixture
def test_ingredient(db_session: Session):
    ingredient = Ingredient(
        name="Test Ingredient",
        common_allergens=json.dumps(["nuts"]),
        source="test"
    )
    db_session.add(ingredient)
    db_session.commit()
    return ingredient

@pytest.fixture
def auth_headers(test_user):
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.mark.integration
def test_user_registration(client):
    """Test user registration endpoint"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "testpassword",
            "full_name": "New User"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert "id" in data

@pytest.mark.integration
def test_user_login(client, test_user):
    """Test user login endpoint"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.integration
def test_get_user_profile(client, test_user, auth_headers):
    """Test get user profile endpoint"""
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name
    assert data["dietary_restrictions"] == test_user.dietary_restrictions

@pytest.mark.integration
def test_update_user_preferences(client, test_user, auth_headers):
    """Test update user preferences endpoint"""
    response = client.put(
        "/api/v1/users/me/preferences",
        headers=auth_headers,
        json={
            "dietary_restrictions": ["vegan"],
            "favorite_cuisines": ["indian"],
            "allergies": ["shellfish"],
            "food_flags": ["high_sugar"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dietary_restrictions"] == ["vegan"]
    assert data["favorite_cuisines"] == ["indian"]
    assert data["allergies"] == ["shellfish"]
    assert data["food_flags"] == ["high_sugar"]

@pytest.mark.integration
def test_get_recipes(client, test_recipe, auth_headers):
    """Test get recipes endpoint"""
    response = client.get("/api/v1/recipes", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == test_recipe.name
    assert data[0]["calories"] == test_recipe.calories

@pytest.mark.integration
def test_get_recipe_by_id(client, test_recipe, auth_headers):
    """Test get recipe by ID endpoint"""
    response = client.get(f"/api/v1/recipes/{test_recipe.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_recipe.name
    assert data["description"] == test_recipe.description
    assert json.loads(data["ingredients"]) == json.loads(test_recipe.ingredients)

@pytest.mark.integration
def test_get_recommendations(client, test_user, test_recipe, auth_headers):
    """Test get recommendations endpoint"""
    response = client.get("/api/v1/recipes/recommendations", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(isinstance(recipe["id"], int) for recipe in data)

@pytest.mark.integration
def test_rate_recipe(client, test_recipe, auth_headers):
    """Test rate recipe endpoint"""
    response = client.post(
        f"/api/v1/recipes/{test_recipe.id}/rate",
        headers=auth_headers,
        json={"rating": 5}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 5

@pytest.mark.integration
def test_search_ingredients(client, test_ingredient, auth_headers):
    """Test search ingredients endpoint"""
    response = client.get(
        "/api/v1/ingredients/search",
        headers=auth_headers,
        params={"query": "Test"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == test_ingredient.name
    assert json.loads(data[0]["common_allergens"]) == json.loads(test_ingredient.common_allergens)

@pytest.mark.integration
def test_unauthorized_access(client):
    """Test unauthorized access to protected endpoints"""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401

@pytest.mark.integration
def test_invalid_token(client):
    """Test access with invalid token"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401

@pytest.mark.integration
def test_rate_recipe_validation(client, test_recipe, auth_headers):
    """Test recipe rating validation"""
    response = client.post(
        f"/api/v1/recipes/{test_recipe.id}/rate",
        headers=auth_headers,
        json={"rating": 6}  # Invalid rating > 5
    )
    assert response.status_code == 422  # Validation error 