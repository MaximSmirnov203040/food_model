from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, Table, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

# Association table for recipe ingredients
recipe_ingredients = Table(
    'recipe_ingredients',
    Base.metadata,
    Column('recipe_id', Integer, ForeignKey('recipes.id')),
    Column('ingredient_id', Integer, ForeignKey('ingredients.id'))
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # User preferences
    dietary_restrictions = Column(String)  # JSON string of dietary restrictions
    favorite_cuisines = Column(String)     # JSON string of favorite cuisines
    
    # Allergies and food flags
    allergies = Column(String)  # JSON string of allergies
    food_flags = Column(String)  # JSON string of food flags (e.g., high_sodium, high_sugar)
    
    # Relationships
    interactions = relationship("UserRecipeInteraction", back_populates="user")
    ratings = relationship("Rating", back_populates="user")

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    instructions = Column(String)
    prep_time = Column(Integer)  # in minutes
    cook_time = Column(Integer)  # in minutes
    servings = Column(Integer)
    calories = Column(Integer)
    image_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Nutritional information
    protein = Column(Float)
    carbs = Column(Float)
    fat = Column(Float)
    fiber = Column(Float)
    
    # Food flags
    food_flags = Column(String)  # JSON string of food flags
    
    # Relationships
    ingredients = relationship("Ingredient", secondary=recipe_ingredients, back_populates="recipes")
    interactions = relationship("UserRecipeInteraction", back_populates="recipe")
    ratings = relationship("Rating", back_populates="recipe")

class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category = Column(String)  # e.g., "vegetable", "meat", "spice"
    common_allergens = Column(String)  # JSON string of common allergens in this ingredient
    
    # Relationships
    recipes = relationship("Recipe", secondary=recipe_ingredients, back_populates="ingredients")

class UserRecipeInteraction(Base):
    __tablename__ = "user_recipe_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    interaction_type = Column(String)  # "view", "save", "cook"
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="interactions")
    recipe = relationship("Recipe", back_populates="interactions")

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    rating = Column(Integer)  # 1-5 stars
    comment = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="ratings")
    recipe = relationship("Recipe", back_populates="ratings") 