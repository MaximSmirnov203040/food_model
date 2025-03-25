import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from pathlib import Path
import numpy as np
from tqdm import tqdm
import logging
from datetime import datetime
from app.services.recommendation import RecipeEmbedding

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)

class ModelTrainer:
    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        learning_rate: float = 0.001,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.device = device
        self.criterion = nn.MSELoss()
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        
        # Create checkpoint directory
        self.checkpoint_dir = Path('checkpoints')
        self.checkpoint_dir.mkdir(exist_ok=True)
        
        # Training metrics
        self.train_losses = []
        self.val_losses = []
        self.best_val_loss = float('inf')
    
    def train_epoch(self) -> float:
        """Train for one epoch"""
        self.model.train()
        total_loss = 0
        
        for batch_idx, (features, targets) in enumerate(tqdm(self.train_loader, desc='Training')):
            features = features.to(self.device)
            targets = targets.to(self.device)
            
            self.optimizer.zero_grad()
            outputs = self.model(features)
            loss = self.criterion(outputs, targets)
            
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
        
        return total_loss / len(self.train_loader)
    
    def validate(self) -> float:
        """Validate the model"""
        self.model.eval()
        total_loss = 0
        
        with torch.no_grad():
            for features, targets in tqdm(self.val_loader, desc='Validating'):
                features = features.to(self.device)
                targets = targets.to(self.device)
                
                outputs = self.model(features)
                loss = self.criterion(outputs, targets)
                total_loss += loss.item()
        
        return total_loss / len(self.val_loader)
    
    def save_checkpoint(self, epoch: int, val_loss: float):
        """Save model checkpoint"""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'val_loss': val_loss,
            'train_losses': self.train_losses,
            'val_losses': self.val_losses
        }
        
        # Save best model
        if val_loss < self.best_val_loss:
            self.best_val_loss = val_loss
            torch.save(checkpoint, self.checkpoint_dir / 'best_model.pt')
        
        # Save latest checkpoint
        torch.save(checkpoint, self.checkpoint_dir / f'checkpoint_epoch_{epoch}.pt')
    
    def train(
        self,
        num_epochs: int,
        save_interval: int = 5,
        early_stopping_patience: int = 10
    ):
        """Train the model with early stopping"""
        patience_counter = 0
        
        for epoch in range(num_epochs):
            logging.info(f'Epoch {epoch+1}/{num_epochs}')
            
            # Train and validate
            train_loss = self.train_epoch()
            val_loss = self.validate()
            
            # Log metrics
            logging.info(f'Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}')
            
            # Save metrics
            self.train_losses.append(train_loss)
            self.val_losses.append(val_loss)
            
            # Save checkpoint
            if (epoch + 1) % save_interval == 0:
                self.save_checkpoint(epoch, val_loss)
            
            # Early stopping
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                patience_counter = 0
                self.save_checkpoint(epoch, val_loss)
            else:
                patience_counter += 1
                if patience_counter >= early_stopping_patience:
                    logging.info(f'Early stopping triggered after {epoch+1} epochs')
                    break

def main():
    # Load preprocessed data
    data_dir = Path('data/preprocessed')
    train_loader = torch.load(data_dir / 'train_loader.pt')
    val_loader = torch.load(data_dir / 'val_loader.pt')
    
    # Initialize model
    model = RecipeEmbedding(input_dim=8)  # Adjust based on your feature dimension
    
    # Initialize trainer
    trainer = ModelTrainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        learning_rate=0.001
    )
    
    # Train model
    trainer.train(
        num_epochs=100,
        save_interval=5,
        early_stopping_patience=10
    )

if __name__ == "__main__":
    main() 