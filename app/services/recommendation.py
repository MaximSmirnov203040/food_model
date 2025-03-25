import torch
import torch.nn as nn
import numpy as np
from typing import List, Dict, Optional
from sklearn.preprocessing import StandardScaler
from app.core.config import settings
import json

class RecipeEmbedding(nn.Module):
    def __init__(self, input_dim: int, embedding_dim: int = 128):
        super().__init__()
        self.embedding = nn.Sequential(
            nn.Linear(input_dim, embedding_dim),
            nn.ReLU(),
            nn.Linear(embedding_dim, embedding_dim),
            nn.ReLU(),
            nn.Linear(embedding_dim, embedding_dim)
        )
    
    def forward(self, x):
        return self.embedding(x)

class RecommendationService:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.scaler = StandardScaler()
        
        # Define common food flags and their thresholds
        self.food_flags = {
            "high_sodium": {"threshold": 500, "unit": "mg"},
            "high_sugar": {"threshold": 25, "unit": "g"},
            "high_fat": {"threshold": 20, "unit": "g"},
            "high_calories": {"threshold": 500, "unit": "kcal"},
            "high_carbs": {"threshold": 50, "unit": "g"},
            "low_protein": {"threshold": 10, "unit": "g"}
        }
        
    def load_model(self):
        """Load the trained model from disk"""
        if self.model is None:
            self.model = RecipeEmbedding(input_dim=100)  # Adjust input_dim based on your features
            self.model.load_state_dict(torch.load(settings.MODEL_PATH, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()
    
    def get_recipe_features(self, recipe: Dict) -> torch.Tensor:
        """Convert recipe data to feature tensor"""
        features = [
            recipe.get('calories', 0),
            recipe.get('protein', 0),
            recipe.get('carbs', 0),
            recipe.get('fat', 0),
            recipe.get('fiber', 0),
            recipe.get('prep_time', 0),
            recipe.get('cook_time', 0),
            recipe.get('servings', 1)
        ]
        # Add more features as needed
        
        features = self.scaler.fit_transform(np.array(features).reshape(1, -1))
        return torch.FloatTensor(features).to(self.device)
    
    def get_user_preferences(self, user_id: int, db) -> Dict:
        """Get user preferences from database"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                "dietary_restrictions": [],
                "favorite_cuisines": [],
                "allergies": [],
                "food_flags": []
            }
        
        return {
            "dietary_restrictions": json.loads(user.dietary_restrictions or "[]"),
            "favorite_cuisines": json.loads(user.favorite_cuisines or "[]"),
            "allergies": json.loads(user.allergies or "[]"),
            "food_flags": json.loads(user.food_flags or "[]")
        }
    
    def check_recipe_allergens(self, recipe: Dict, user_allergies: List[str]) -> bool:
        """Check if recipe contains any user's allergens"""
        recipe_ingredients = recipe.get('ingredients', [])
        for ingredient in recipe_ingredients:
            common_allergens = json.loads(ingredient.common_allergens or "[]")
            if any(allergen in common_allergens for allergen in user_allergies):
                return True
        return False
    
    def check_food_flags(self, recipe: Dict) -> List[str]:
        """Check recipe against food flags"""
        flags = []
        
        # Check sodium content
        if recipe.get('sodium', 0) > self.food_flags['high_sodium']['threshold']:
            flags.append('high_sodium')
        
        # Check sugar content
        if recipe.get('sugar', 0) > self.food_flags['high_sugar']['threshold']:
            flags.append('high_sugar')
        
        # Check fat content
        if recipe.get('fat', 0) > self.food_flags['high_fat']['threshold']:
            flags.append('high_fat')
        
        # Check calories
        if recipe.get('calories', 0) > self.food_flags['high_calories']['threshold']:
            flags.append('high_calories')
        
        # Check carbs
        if recipe.get('carbs', 0) > self.food_flags['high_carbs']['threshold']:
            flags.append('high_carbs')
        
        # Check protein
        if recipe.get('protein', 0) < self.food_flags['low_protein']['threshold']:
            flags.append('low_protein')
        
        return flags
    
    def filter_by_preferences(self, recipes: List[Dict], preferences: Dict) -> List[Dict]:
        """Filter recipes based on user preferences"""
        filtered_recipes = []
        for recipe in recipes:
            # Check dietary restrictions
            if any(restriction in recipe.get('tags', []) for restriction in preferences['dietary_restrictions']):
                continue
            
            # Check allergies
            if self.check_recipe_allergens(recipe, preferences['allergies']):
                continue
            
            # Check food flags
            recipe_flags = self.check_food_flags(recipe)
            if any(flag in recipe_flags for flag in preferences['food_flags']):
                continue
                
            # Check favorite cuisines
            if recipe.get('cuisine') in preferences['favorite_cuisines']:
                recipe['match_score'] = recipe.get('match_score', 0) + 0.2  # Boost score for favorite cuisine
            
            # Add food flags to recipe info
            recipe['food_flags'] = recipe_flags
            
            filtered_recipes.append(recipe)
        
        return filtered_recipes
    
    def collaborative_filtering(self, user_id: int, db) -> List[int]:
        """Get recommendations based on user interactions"""
        # Get user's interaction history
        user_interactions = db.query(UserRecipeInteraction).filter(
            UserRecipeInteraction.user_id == user_id
        ).all()
        
        # Get similar users based on interaction patterns
        similar_users = self._find_similar_users(user_id, db)
        
        # Get recipes liked by similar users
        recommended_recipes = self._get_recipes_from_similar_users(similar_users, db)
        
        return recommended_recipes
    
    def content_based_filtering(self, recipe_id: int, db) -> List[int]:
        """Get recommendations based on recipe content"""
        # Get the target recipe
        target_recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not target_recipe:
            return []
        
        # Get recipe features
        target_features = self.get_recipe_features(target_recipe.__dict__)
        
        # Get all recipes
        all_recipes = db.query(Recipe).all()
        
        # Calculate similarity scores
        similar_recipes = []
        for recipe in all_recipes:
            if recipe.id == recipe_id:
                continue
                
            recipe_features = self.get_recipe_features(recipe.__dict__)
            similarity = torch.cosine_similarity(target_features, recipe_features)
            
            similar_recipes.append({
                'id': recipe.id,
                'match_score': similarity.item()
            })
        
        # Sort by similarity score
        similar_recipes.sort(key=lambda x: x['match_score'], reverse=True)
        return [recipe['id'] for recipe in similar_recipes]
    
    def get_recommendations(
        self,
        user_id: int,
        db,
        n_recommendations: int = 10
    ) -> List[Dict]:
        """
        Get personalized recipe recommendations using hybrid approach
        """
        # Load model if not already loaded
        self.load_model()
        
        # Get user preferences
        user_prefs = self.get_user_preferences(user_id, db)
        
        # Get collaborative filtering recommendations
        cf_recommendations = self.collaborative_filtering(user_id, db)
        
        # Get content-based recommendations
        cb_recommendations = self.content_based_filtering(user_id, db)
        
        # Combine and rank recommendations
        combined_recommendations = list(set(cf_recommendations + cb_recommendations))
        
        # Get recipe details for recommendations
        recommended_recipes = []
        for recipe_id in combined_recommendations[:n_recommendations]:
            recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
            if recipe:
                recipe_dict = recipe.__dict__
                recipe_dict['match_score'] = 0.5  # Default score
                recommended_recipes.append(recipe_dict)
        
        # Filter and adjust scores based on preferences
        recommended_recipes = self.filter_by_preferences(recommended_recipes, user_prefs)
        
        # Sort by match score
        recommended_recipes.sort(key=lambda x: x['match_score'], reverse=True)
        
        return recommended_recipes[:n_recommendations]
    
    def _find_similar_users(self, user_id: int, db) -> List[int]:
        """Find users with similar interaction patterns"""
        # Implement user similarity calculation
        # This is a simplified version
        return []
    
    def _get_recipes_from_similar_users(self, similar_users: List[int], db) -> List[int]:
        """Get recipes liked by similar users"""
        # Implement recipe collection from similar users
        # This is a simplified version
        return []
    
    def train_model(self, training_data: List[Dict]):
        """
        Train the recommendation model
        """
        # Implement model training logic
        pass 