from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Recipe, UserRecipeInteraction, Rating
from app.core.config import settings
import json
from typing import List, Dict
from pathlib import Path

def load_data_from_db() -> tuple[List[Dict], List[Dict]]:
    """Load recipes and interactions from database"""
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Load recipes
        recipes = db.query(Recipe).all()
        recipe_data = []
        for recipe in recipes:
            recipe_dict = {
                'id': recipe.id,
                'calories': recipe.calories,
                'protein': recipe.protein,
                'carbs': recipe.carbs,
                'fat': recipe.fat,
                'fiber': recipe.fiber,
                'prep_time': recipe.prep_time,
                'cook_time': recipe.cook_time,
                'servings': recipe.servings,
                'food_flags': json.loads(recipe.food_flags or "[]"),
                'ingredients': [
                    {
                        'id': ing.id,
                        'name': ing.name,
                        'common_allergens': json.loads(ing.common_allergens or "[]")
                    }
                    for ing in recipe.ingredients
                ]
            }
            recipe_data.append(recipe_dict)
        
        # Load interactions and ratings
        interactions = []
        ratings = db.query(Rating).all()
        for rating in ratings:
            interaction = {
                'user_id': rating.user_id,
                'recipe_id': rating.recipe_id,
                'rating': rating.rating
            }
            interactions.append(interaction)
        
        # Add view interactions
        view_interactions = db.query(UserRecipeInteraction).filter(
            UserRecipeInteraction.interaction_type == "view"
        ).all()
        for interaction in view_interactions:
            interactions.append({
                'user_id': interaction.user_id,
                'recipe_id': interaction.recipe_id,
                'rating': 0.5  # Lower weight for views
            })
        
        return recipe_data, interactions
    
    finally:
        db.close()

def save_data(data: tuple[List[Dict], List[Dict]], output_dir: str):
    """Save loaded data to disk"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    recipes, interactions = data
    
    # Save recipes
    with open(output_path / 'recipes.json', 'w') as f:
        json.dump(recipes, f)
    
    # Save interactions
    with open(output_path / 'interactions.json', 'w') as f:
        json.dump(interactions, f)

def main():
    # Load data from database
    recipes, interactions = load_data_from_db()
    
    # Save data
    save_data((recipes, interactions), 'data/raw')
    
    print(f"Loaded {len(recipes)} recipes and {len(interactions)} interactions")
    print("Data saved to data/raw/")

if __name__ == "__main__":
    main() 