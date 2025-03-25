import subprocess
import logging
from pathlib import Path
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training_pipeline.log'),
        logging.StreamHandler()
    ]
)

def run_script(script_path: str, description: str):
    """Run a Python script and handle errors"""
    logging.info(f"Starting {description}...")
    try:
        result = subprocess.run([sys.executable, script_path], check=True)
        logging.info(f"Completed {description} successfully")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during {description}: {str(e)}")
        return False

def main():
    # Create necessary directories
    Path('data/raw').mkdir(parents=True, exist_ok=True)
    Path('data/preprocessed').mkdir(parents=True, exist_ok=True)
    Path('checkpoints').mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load data from database
    if not run_script('scripts/training/load_data.py', 'data loading'):
        return
    
    # Step 2: Prepare data for training
    if not run_script('scripts/training/data_preparation.py', 'data preparation'):
        return
    
    # Step 3: Train the model
    if not run_script('scripts/training/train_model.py', 'model training'):
        return
    
    logging.info("Training pipeline completed successfully!")

if __name__ == "__main__":
    main() 