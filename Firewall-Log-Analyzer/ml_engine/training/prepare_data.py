"""
Data Preparation Pipeline
Complete pipeline to load, label, and split the dataset
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from ml_engine.training.data_loader import load_dataset, print_dataset_summary
    from ml_engine.training.data_labeler import label_dataset, print_label_statistics
    from ml_engine.training.data_splitter import (
        split_dataset,
        save_splits,
        print_split_statistics
    )
    from ml_engine.config.ml_config import DATASET_DIR, TRAINING_CONFIG
except ImportError:
    # Fallback for standalone execution
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from data_loader import load_dataset, print_dataset_summary
    from data_labeler import label_dataset, print_label_statistics
    from data_splitter import (
        split_dataset,
        save_splits,
        print_split_statistics
    )
    DATASET_DIR = Path(__file__).resolve().parent.parent / "dataset"
    TRAINING_CONFIG = {"random_seed": 42}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def prepare_complete_dataset(
    csv_path: Path = None,
    save_splits_to_disk: bool = True,
    stratify: bool = True
) -> tuple:
    """
    Complete data preparation pipeline.
    
    Steps:
    1. Load dataset from CSV
    2. Validate and clean data
    3. Label the data
    4. Split into train/validation/test
    
    Args:
        csv_path: Path to CSV file (uses default if None)
        save_splits_to_disk: Whether to save splits to CSV files
        stratify: Whether to use stratified splitting
    
    Returns:
        Tuple of (train_df, val_df, test_df, labeled_df)
    """
    logger.info("="*60)
    logger.info("STARTING DATA PREPARATION PIPELINE")
    logger.info("="*60)
    
    # Step 1: Load dataset
    logger.info("\n[Step 1/4] Loading dataset...")
    df = load_dataset(csv_path)
    print_dataset_summary(df)
    
    # Step 2: Label dataset
    logger.info("\n[Step 2/4] Labeling dataset...")
    labeled_df = label_dataset(df)
    print_label_statistics(labeled_df)
    
    # Step 3: Split dataset
    logger.info("\n[Step 3/4] Splitting dataset...")
    stratify_column = 'label' if stratify else None
    train_df, val_df, test_df = split_dataset(
        labeled_df,
        stratify=stratify_column
    )
    print_split_statistics(train_df, val_df, test_df)
    
    # Step 4: Save splits (optional)
    if save_splits_to_disk:
        logger.info("\n[Step 4/4] Saving splits to disk...")
        file_paths = save_splits(
            train_df, val_df, test_df,
            DATASET_DIR,
            prefix="labeled_dataset"
        )
        logger.info(f"Saved splits to: {list(file_paths.values())}")
    
    logger.info("\n" + "="*60)
    logger.info("DATA PREPARATION COMPLETE")
    logger.info("="*60)
    
    return train_df, val_df, test_df, labeled_df


if __name__ == "__main__":
    try:
        train_df, val_df, test_df, labeled_df = prepare_complete_dataset()
        
        print("\n✅ Data preparation successful!")
        print(f"\nSummary:")
        print(f"  Total labeled entries: {len(labeled_df)}")
        print(f"  Training set: {len(train_df)} rows")
        print(f"  Validation set: {len(val_df)} rows")
        print(f"  Test set: {len(test_df)} rows")
        
    except Exception as e:
        logger.error(f"Error in data preparation: {e}", exc_info=True)
        raise

