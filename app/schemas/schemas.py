from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    dietary_restrictions: Optional[List[str]] = []
    favorite_cuisines: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    food_flags: Optional[List[str]] = []

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    dietary_restrictions: Optional[List[str]] = None
    favorite_cuisines: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    food_flags: Optional[List[str]] = None
    password: Optional[str] = None

class UserPreferences(BaseModel):
    dietary_restrictions: List[str]
    favorite_cuisines: List[str]
    allergies: List[str]
    food_flags: List[str]

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Recipe schemas
class IngredientBase(BaseModel):
    name: str
    category: str
    common_allergens: Optional[List[str]] = []

class IngredientCreate(IngredientBase):
    pass

class Ingredient(IngredientBase):
    id: int

    class Config:
        from_attributes = True

class RecipeBase(BaseModel):
    title: str
    description: str
    instructions: str
    prep_time: int
    cook_time: int
    servings: int
    calories: int
    image_url: Optional[str] = None
    protein: float
    carbs: float
    fat: float
    fiber: float
    food_flags: Optional[List[str]] = []

class RecipeCreate(RecipeBase):
    ingredients: List[int]  # List of ingredient IDs

class Recipe(RecipeBase):
    id: int
    created_at: datetime
    ingredients: List[Ingredient]

    class Config:
        from_attributes = True

# Rating schemas
class RatingBase(BaseModel):
    rating: int
    comment: Optional[str] = None

class RatingCreate(RatingBase):
    recipe_id: int

class Rating(RatingBase):
    id: int
    user_id: int
    recipe_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Recommendation schemas
class RecipeRecommendation(BaseModel):
    id: int
    title: str
    description: str
    image_url: Optional[str]
    match_score: float
    nutritional_info: dict

    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None 