import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Tuple
import json
from pathlib import Path
import torch
from torch.utils.data import Dataset, DataLoader

class RecipeDataset(Dataset):
    def __init__(self, features: np.ndarray, targets: np.ndarray):
        self.features = torch.FloatTensor(features)
        self.targets = torch.FloatTensor(targets)
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        return self.features[idx], self.targets[idx]

class DataPreprocessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_columns = [
            'calories', 'protein', 'carbs', 'fat', 'fiber',
            'prep_time', 'cook_time', 'servings'
        ]
    
    def prepare_recipe_features(self, recipes: List[Dict]) -> np.ndarray:
        """Convert recipe data to feature matrix"""
        features = []
        for recipe in recipes:
            feature_vector = [
                recipe.get('calories', 0),
                recipe.get('protein', 0),
                recipe.get('carbs', 0),
                recipe.get('fat', 0),
                recipe.get('fiber', 0),
                recipe.get('prep_time', 0),
                recipe.get('cook_time', 0),
                recipe.get('servings', 1)
            ]
            features.append(feature_vector)
        
        return np.array(features)
    
    def prepare_interaction_matrix(self, interactions: List[Dict]) -> np.ndarray:
        """Create user-recipe interaction matrix"""
        # Get unique users and recipes
        users = sorted(list(set(i['user_id'] for i in interactions)))
        recipes = sorted(list(set(i['recipe_id'] for i in interactions)))
        
        # Create mapping dictionaries
        user_to_idx = {user: idx for idx, user in enumerate(users)}
        recipe_to_idx = {recipe: idx for idx, recipe in enumerate(recipes)}
        
        # Create interaction matrix
        matrix = np.zeros((len(users), len(recipes)))
        for interaction in interactions:
            user_idx = user_to_idx[interaction['user_id']]
            recipe_idx = recipe_to_idx[interaction['recipe_id']]
            matrix[user_idx, recipe_idx] = interaction.get('rating', 1)
        
        return matrix
    
    def prepare_training_data(
        self,
        recipes: List[Dict],
        interactions: List[Dict],
        batch_size: int = 32
    ) -> Tuple[DataLoader, DataLoader]:
        """Prepare training and validation data"""
        # Prepare features
        features = self.prepare_recipe_features(recipes)
        features_scaled = self.scaler.fit_transform(features)
        
        # Prepare interaction matrix
        interaction_matrix = self.prepare_interaction_matrix(interactions)
        
        # Split data into training and validation sets
        train_size = int(0.8 * len(interactions))
        train_indices = np.random.choice(len(interactions), train_size, replace=False)
        val_indices = np.setdiff1d(np.arange(len(interactions)), train_indices)
        
        # Create datasets
        train_dataset = RecipeDataset(
            features_scaled[train_indices],
            interaction_matrix[train_indices]
        )
        val_dataset = RecipeDataset(
            features_scaled[val_indices],
            interaction_matrix[val_indices]
        )
        
        # Create data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=4
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=4
        )
        
        return train_loader, val_loader
    
    def save_preprocessed_data(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        output_dir: str
    ):
        """Save preprocessed data to disk"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save scaler
        torch.save(self.scaler, output_path / 'scaler.pt')
        
        # Save data loaders
        torch.save(train_loader, output_path / 'train_loader.pt')
        torch.save(val_loader, output_path / 'val_loader.pt')

def main():
    # Example usage
    preprocessor = DataPreprocessor()
    
    # Load your data here
    # recipes = load_recipes()
    # interactions = load_interactions()
    
    # Prepare data
    # train_loader, val_loader = preprocessor.prepare_training_data(recipes, interactions)
    
    # Save preprocessed data
    # preprocessor.save_preprocessed_data(train_loader, val_loader, 'data/preprocessed')

if __name__ == "__main__":
    main() 