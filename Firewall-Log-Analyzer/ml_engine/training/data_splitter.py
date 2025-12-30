"""
Data Splitter Module
Splits dataset into train, validation, and test sets
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict
from pathlib import Path
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from sklearn.model_selection import train_test_split
except ImportError:
    train_test_split = None
    logging.warning("sklearn not available. Stratified splitting will not work.")

try:
    from ml_engine.config.ml_config import TRAINING_CONFIG
except ImportError:
    # Fallback if running as standalone script
    TRAINING_CONFIG = {
        "train_ratio": 0.70,
        "validation_ratio": 0.15,
        "test_ratio": 0.15,
        "random_seed": 42
    }

logger = logging.getLogger(__name__)


def split_dataset(
    df: pd.DataFrame,
    train_ratio: Optional[float] = None,
    validation_ratio: Optional[float] = None,
    test_ratio: Optional[float] = None,
    random_seed: Optional[int] = None,
    stratify: Optional[str] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split dataset into train, validation, and test sets.
    
    Args:
        df: DataFrame to split
        train_ratio: Proportion for training set (default from config)
        validation_ratio: Proportion for validation set (default from config)
        test_ratio: Proportion for test set (default from config)
        random_seed: Random seed for reproducibility
        stratify: Column name to stratify on (e.g., 'label' for balanced splits)
    
    Returns:
        Tuple of (train_df, validation_df, test_df)
    
    Raises:
        ValueError: If ratios don't sum to 1.0
    """
    # Get ratios from config if not provided
    if train_ratio is None:
        train_ratio = TRAINING_CONFIG.get("train_ratio", 0.70)
    if validation_ratio is None:
        validation_ratio = TRAINING_CONFIG.get("validation_ratio", 0.15)
    if test_ratio is None:
        test_ratio = TRAINING_CONFIG.get("test_ratio", 0.15)
    
    # Validate ratios
    total_ratio = train_ratio + validation_ratio + test_ratio
    if abs(total_ratio - 1.0) > 0.01:
        raise ValueError(f"Ratios must sum to 1.0, got {total_ratio}")
    
    # Get random seed
    seed = random_seed or TRAINING_CONFIG.get("random_seed", 42)
    
    logger.info(f"Splitting dataset: Train={train_ratio:.2%}, Val={validation_ratio:.2%}, Test={test_ratio:.2%}")
    logger.info(f"Total rows: {len(df)}")
    
    # Shuffle dataset
    df_shuffled = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    
    # Calculate split indices
    n_total = len(df_shuffled)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * validation_ratio)
    n_test = n_total - n_train - n_val  # Remaining goes to test
    
    # Split if stratifying
    if stratify and stratify in df.columns and train_test_split is not None:
        train_df, val_df, test_df = stratified_split(
            df_shuffled, n_train, n_val, n_test, stratify, seed
        )
    else:
        # Simple split
        train_df = df_shuffled.iloc[:n_train].copy()
        val_df = df_shuffled.iloc[n_train:n_train + n_val].copy()
        test_df = df_shuffled.iloc[n_train + n_val:].copy()
    
    logger.info(f"Split complete:")
    logger.info(f"  Train: {len(train_df)} rows ({len(train_df)/n_total:.2%})")
    logger.info(f"  Validation: {len(val_df)} rows ({len(val_df)/n_total:.2%})")
    logger.info(f"  Test: {len(test_df)} rows ({len(test_df)/n_total:.2%})")
    
    return train_df, val_df, test_df


def stratified_split(
    df: pd.DataFrame,
    n_train: int,
    n_val: int,
    n_test: int,
    stratify_column: str,
    random_seed: int
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified split to maintain label distribution across splits.
    
    Args:
        df: DataFrame to split
        n_train: Number of training samples
        n_val: Number of validation samples
        n_test: Number of test samples
        stratify_column: Column to stratify on
        random_seed: Random seed
    
    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    from sklearn.model_selection import train_test_split
    
    logger.info(f"Performing stratified split on column: {stratify_column}")
    
    # First split: separate train from (val + test)
    train_df, temp_df = train_test_split(
        df,
        test_size=(n_val + n_test) / len(df),
        stratify=df[stratify_column] if stratify_column in df.columns else None,
        random_state=random_seed
    )
    
    # Second split: separate val from test
    val_df, test_df = train_test_split(
        temp_df,
        test_size=n_test / len(temp_df),
        stratify=temp_df[stratify_column] if stratify_column in temp_df.columns else None,
        random_state=random_seed
    )
    
    return train_df, val_df, test_df


def save_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: Path,
    prefix: str = "dataset"
) -> Dict[str, Path]:
    """
    Save train, validation, and test splits to CSV files.
    
    Args:
        train_df: Training DataFrame
        val_df: Validation DataFrame
        test_df: Test DataFrame
        output_dir: Directory to save files
        prefix: Filename prefix
    
    Returns:
        Dictionary mapping split names to file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    file_paths = {}
    
    # Save train set
    train_path = output_dir / f"{prefix}_train.csv"
    train_df.to_csv(train_path, index=False)
    file_paths['train'] = train_path
    logger.info(f"Saved training set to: {train_path}")
    
    # Save validation set
    val_path = output_dir / f"{prefix}_validation.csv"
    val_df.to_csv(val_path, index=False)
    file_paths['validation'] = val_path
    logger.info(f"Saved validation set to: {val_path}")
    
    # Save test set
    test_path = output_dir / f"{prefix}_test.csv"
    test_df.to_csv(test_path, index=False)
    file_paths['test'] = test_path
    logger.info(f"Saved test set to: {test_path}")
    
    return file_paths


def load_splits(
    input_dir: Path,
    prefix: str = "dataset"
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load train, validation, and test splits from CSV files.
    
    Args:
        input_dir: Directory containing split files
        prefix: Filename prefix
    
    Returns:
        Tuple of (train_df, val_df, test_df)
    
    Raises:
        FileNotFoundError: If split files don't exist
    """
    train_path = input_dir / f"{prefix}_train.csv"
    val_path = input_dir / f"{prefix}_validation.csv"
    test_path = input_dir / f"{prefix}_test.csv"
    
    if not all(p.exists() for p in [train_path, val_path, test_path]):
        raise FileNotFoundError("One or more split files not found")
    
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)
    
    logger.info(f"Loaded splits: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    
    return train_df, val_df, test_df


def print_split_statistics(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    label_column: str = 'label'
):
    """
    Print statistics about the data splits.
    
    Args:
        train_df: Training DataFrame
        val_df: Validation DataFrame
        test_df: Test DataFrame
        label_column: Column name for labels
    """
    print("\n" + "="*60)
    print("DATA SPLIT STATISTICS")
    print("="*60)
    
    splits = {
        'Train': train_df,
        'Validation': val_df,
        'Test': test_df
    }
    
    for split_name, split_df in splits.items():
        print(f"\n{split_name} Set:")
        print(f"  Total rows: {len(split_df)}")
        
        if label_column in split_df.columns:
            label_counts = split_df[label_column].value_counts()
            print(f"  Label distribution:")
            for label, count in label_counts.items():
                percentage = (count / len(split_df)) * 100
                print(f"    {label}: {count} ({percentage:.2f}%)")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    # Test data splitting
    logging.basicConfig(level=logging.INFO)
    
    try:
        from ml_engine.training.data_loader import load_dataset
        from ml_engine.training.data_labeler import label_dataset
    except ImportError:
        # Fallback for standalone execution
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from data_loader import load_dataset
        from data_labeler import label_dataset
    
    try:
        # Load and label dataset
        df = load_dataset()
        df = label_dataset(df)
        
        # Split dataset
        train_df, val_df, test_df = split_dataset(df, stratify='label')
        
        # Print statistics
        print_split_statistics(train_df, val_df, test_df)
        
        # Optionally save splits
        try:
            from ml_engine.config.ml_config import DATASET_DIR
            output_dir = DATASET_DIR
        except ImportError:
            output_dir = Path(__file__).resolve().parent.parent / "dataset"
        save_splits(train_df, val_df, test_df, output_dir, prefix="labeled_dataset")
        
    except Exception as e:
        print(f"Error splitting dataset: {e}")
        import traceback
        traceback.print_exc()

