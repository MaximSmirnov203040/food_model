import requests
import json
from typing import List, Dict, Optional
from pathlib import Path
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Ingredient
from app.core.config import settings
import time
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ingredient_loading.log'),
        logging.StreamHandler()
    ]
)

class IngredientLoader:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # API endpoints
        self.openfoodfacts_url = "https://world.openfoodfacts.org/api/v2"
        self.edamam_url = "https://api.edamam.com/api/food-database/v2"
        self.usda_url = "https://api.nal.usda.gov/fdc/v1"
        
        # API keys (should be in environment variables)
        self.edamam_app_id = settings.EDAMAM_APP_ID
        self.edamam_app_key = settings.EDAMAM_APP_KEY
        self.usda_api_key = settings.USDA_API_KEY
    
    def get_openfoodfacts_ingredients(self, page: int = 1, page_size: int = 100) -> List[Dict]:
        """Fetch ingredients from Open Food Facts API"""
        try:
            response = requests.get(
                f"{self.openfoodfacts_url}/search",
                params={
                    "page": page,
                    "page_size": page_size,
                    "json": 1
                }
            )
            response.raise_for_status()
            data = response.json()
            
            ingredients = []
            for product in data.get("products", []):
                if "ingredients" in product:
                    for ingredient in product["ingredients"]:
                        if "text" in ingredient:
                            ingredients.append({
                                "name": ingredient["text"],
                                "common_allergens": self._extract_allergens(ingredient),
                                "source": "openfoodfacts"
                            })
            
            return ingredients
        except Exception as e:
            logging.error(f"Error fetching from Open Food Facts: {str(e)}")
            return []
    
    def get_edamam_ingredients(self, query: str) -> List[Dict]:
        """Fetch ingredients from Edamam API"""
        try:
            response = requests.get(
                f"{self.edamam_url}/parser",
                params={
                    "app_id": self.edamam_app_id,
                    "app_key": self.edamam_app_key,
                    "ingr": query
                }
            )
            response.raise_for_status()
            data = response.json()
            
            ingredients = []
            for hint in data.get("hints", []):
                food = hint.get("food", {})
                if "label" in food:
                    ingredients.append({
                        "name": food["label"],
                        "common_allergens": self._extract_allergens(food),
                        "source": "edamam"
                    })
            
            return ingredients
        except Exception as e:
            logging.error(f"Error fetching from Edamam: {str(e)}")
            return []
    
    def get_usda_ingredients(self, query: str) -> List[Dict]:
        """Fetch ingredients from USDA API"""
        try:
            response = requests.get(
                f"{self.usda_url}/foods/search",
                params={
                    "api_key": self.usda_api_key,
                    "query": query,
                    "pageSize": 25
                }
            )
            response.raise_for_status()
            data = response.json()
            
            ingredients = []
            for food in data.get("foods", []):
                if "description" in food:
                    ingredients.append({
                        "name": food["description"],
                        "common_allergens": self._extract_allergens(food),
                        "source": "usda"
                    })
            
            return ingredients
        except Exception as e:
            logging.error(f"Error fetching from USDA: {str(e)}")
            return []
    
    def _extract_allergens(self, data: Dict) -> List[str]:
        """Extract allergen information from various API responses"""
        allergens = []
        
        # Open Food Facts allergens
        if "allergens" in data:
            allergens.extend(data["allergens"].split(","))
        
        # Edamam allergens
        if "allergens" in data:
            allergens.extend(data["allergens"])
        
        # USDA allergens
        if "allergenName" in data:
            allergens.append(data["allergenName"])
        
        # Clean and standardize allergen names
        allergens = [a.strip().lower() for a in allergens if a.strip()]
        return list(set(allergens))  # Remove duplicates
    
    def save_ingredients(self, ingredients: List[Dict]):
        """Save ingredients to database"""
        db = self.SessionLocal()
        try:
            for ingredient_data in ingredients:
                # Check if ingredient already exists
                existing = db.query(Ingredient).filter(
                    Ingredient.name == ingredient_data["name"]
                ).first()
                
                if not existing:
                    ingredient = Ingredient(
                        name=ingredient_data["name"],
                        common_allergens=json.dumps(ingredient_data["common_allergens"]),
                        source=ingredient_data["source"]
                    )
                    db.add(ingredient)
            
            db.commit()
            logging.info(f"Saved {len(ingredients)} ingredients to database")
        except Exception as e:
            db.rollback()
            logging.error(f"Error saving ingredients: {str(e)}")
        finally:
            db.close()
    
    def load_all_ingredients(self):
        """Load ingredients from all sources"""
        # Common ingredient categories
        categories = [
            "vegetables", "fruits", "meat", "fish", "dairy",
            "grains", "spices", "herbs", "nuts", "seeds"
        ]
        
        all_ingredients = []
        
        # Load from Open Food Facts
        for page in tqdm(range(1, 11), desc="Loading from Open Food Facts"):
            ingredients = self.get_openfoodfacts_ingredients(page=page)
            all_ingredients.extend(ingredients)
            time.sleep(1)  # Rate limiting
        
        # Load from Edamam and USDA for each category
        for category in tqdm(categories, desc="Loading from other sources"):
            # Edamam
            ingredients = self.get_edamam_ingredients(category)
            all_ingredients.extend(ingredients)
            time.sleep(1)  # Rate limiting
            
            # USDA
            ingredients = self.get_usda_ingredients(category)
            all_ingredients.extend(ingredients)
            time.sleep(1)  # Rate limiting
        
        # Save all ingredients
        self.save_ingredients(all_ingredients)
        
        logging.info(f"Total ingredients loaded: {len(all_ingredients)}")

def main():
    loader = IngredientLoader()
    loader.load_all_ingredients()

if __name__ == "__main__":
    main() 