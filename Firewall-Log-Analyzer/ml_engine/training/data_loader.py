"""
Data Loader Module
Loads and validates the dataset from CSV files
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from ml_engine.config.ml_config import DATASET_CSV, TRAINING_CONFIG
except ImportError:
    # Fallback if running as standalone script
    DATASET_CSV = Path(__file__).resolve().parent.parent / "dataset" / "Linux_2k.log_structured.csv"
    TRAINING_CONFIG = {"random_seed": 42}

logger = logging.getLogger(__name__)


def load_dataset(
    csv_path: Optional[Path] = None,
    sample_size: Optional[int] = None,
    random_seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Load the structured log dataset from CSV file.
    
    Args:
        csv_path: Path to CSV file. If None, uses default from config.
        sample_size: Optional number of rows to sample. If None, loads all.
        random_seed: Random seed for sampling reproducibility.
    
    Returns:
        DataFrame with loaded and validated data
    
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If data validation fails
    """
    if csv_path is None:
        csv_path = DATASET_CSV
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {csv_path}")
    
    logger.info(f"Loading dataset from: {csv_path}")
    
    # Load CSV
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        # Try with different encoding
        df = pd.read_csv(csv_path, encoding='latin-1')
    
    logger.info(f"Loaded {len(df)} rows from dataset")
    
    # Sample if requested
    if sample_size and sample_size < len(df):
        seed = random_seed or TRAINING_CONFIG.get("random_seed", 42)
        df = df.sample(n=sample_size, random_state=seed).reset_index(drop=True)
        logger.info(f"Sampled {sample_size} rows from dataset")
    
    # Validate and clean data
    df = validate_and_clean_data(df)
    
    return df


def validate_and_clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean the dataset.
    
    Args:
        df: Raw DataFrame from CSV
    
    Returns:
        Cleaned DataFrame
    
    Raises:
        ValueError: If required columns are missing
    """
    logger.info("Validating and cleaning dataset...")
    
    # Required columns
    required_columns = ['LineId', 'Month', 'Date', 'Time', 'Component', 'Content', 'EventId', 'EventTemplate']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Remove completely empty rows
    initial_count = len(df)
    df = df.dropna(how='all')
    if len(df) < initial_count:
        logger.warning(f"Removed {initial_count - len(df)} completely empty rows")
    
    # Handle missing values in key columns
    # Fill missing Component with 'unknown'
    if df['Component'].isna().any():
        df['Component'] = df['Component'].fillna('unknown')
        logger.info("Filled missing Component values with 'unknown'")
    
    # Fill missing Content with empty string
    if df['Content'].isna().any():
        df['Content'] = df['Content'].fillna('')
        logger.info("Filled missing Content values with empty string")
    
    # Fill missing EventId with 'UNKNOWN'
    if df['EventId'].isna().any():
        df['EventId'] = df['EventId'].fillna('UNKNOWN')
        logger.info("Filled missing EventId values with 'UNKNOWN'")
    
    # Fill missing EventTemplate with empty string
    if df['EventTemplate'].isna().any():
        df['EventTemplate'] = df['EventTemplate'].fillna('')
        logger.info("Filled missing EventTemplate values with empty string")
    
    # Fill missing PID with 0
    if 'PID' in df.columns and df['PID'].isna().any():
        df['PID'] = df['PID'].fillna(0)
        logger.info("Filled missing PID values with 0")
    
    # Fill missing Level with 'unknown'
    if 'Level' in df.columns and df['Level'].isna().any():
        df['Level'] = df['Level'].fillna('unknown')
        logger.info("Filled missing Level values with 'unknown'")
    
    # Validate data types
    if 'LineId' in df.columns:
        df['LineId'] = pd.to_numeric(df['LineId'], errors='coerce').fillna(0).astype(int)
    
    if 'PID' in df.columns:
        df['PID'] = pd.to_numeric(df['PID'], errors='coerce').fillna(0).astype(int)
    
    # Create datetime column if possible
    df = create_datetime_column(df)
    
    logger.info(f"Dataset validation complete. Final row count: {len(df)}")
    
    return df


def create_datetime_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a datetime column from Month, Date, and Time columns.
    
    Args:
        df: DataFrame with Month, Date, Time columns
    
    Returns:
        DataFrame with added 'datetime' column
    """
    if 'datetime' in df.columns:
        return df
    
    try:
        # Combine Month, Date, Time into datetime
        # Format: "Jun 14 15:16:01"
        datetime_str = df['Month'].astype(str) + ' ' + df['Date'].astype(str) + ' ' + df['Time'].astype(str)
        
        # Try to parse (assuming year 2005 based on dataset context)
        # In production, you'd extract year from logs or use current year
        datetime_str = datetime_str + ' 2005'  # Default year
        
        df['datetime'] = pd.to_datetime(datetime_str, format='%b %d %H:%M:%S %Y', errors='coerce')
        
        # Fill NaT with a default datetime
        if df['datetime'].isna().any():
            default_datetime = pd.Timestamp('2005-06-14 00:00:00')
            df['datetime'] = df['datetime'].fillna(default_datetime)
            logger.info("Filled missing datetime values with default")
        
        logger.info("Created datetime column from Month, Date, Time")
    except Exception as e:
        logger.warning(f"Could not create datetime column: {e}")
        # Create a dummy datetime column
        df['datetime'] = pd.Timestamp.now()
    
    return df


def get_dataset_info(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get information about the dataset.
    
    Args:
        df: DataFrame to analyze
    
    Returns:
        Dictionary with dataset statistics
    """
    info = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'columns': list(df.columns),
        'missing_values': df.isnull().sum().to_dict(),
        'data_types': df.dtypes.to_dict(),
    }
    
    # Event statistics
    if 'EventId' in df.columns:
        info['unique_events'] = df['EventId'].nunique()
        info['event_counts'] = df['EventId'].value_counts().head(10).to_dict()
    
    # Component statistics
    if 'Component' in df.columns:
        info['unique_components'] = df['Component'].nunique()
        info['component_counts'] = df['Component'].value_counts().head(10).to_dict()
    
    # Date range
    if 'datetime' in df.columns:
        info['date_range'] = {
            'start': str(df['datetime'].min()),
            'end': str(df['datetime'].max())
        }
    
    return info


def print_dataset_summary(df: pd.DataFrame):
    """
    Print a summary of the dataset.
    
    Args:
        df: DataFrame to summarize
    """
    info = get_dataset_info(df)
    
    print("\n" + "="*60)
    print("DATASET SUMMARY")
    print("="*60)
    print(f"Total Rows: {info['total_rows']}")
    print(f"Total Columns: {info['total_columns']}")
    print(f"\nColumns: {', '.join(info['columns'])}")
    
    if 'unique_events' in info:
        print(f"\nUnique Event IDs: {info['unique_events']}")
        print("\nTop 10 Events:")
        for event, count in list(info['event_counts'].items())[:10]:
            print(f"  {event}: {count}")
    
    if 'unique_components' in info:
        print(f"\nUnique Components: {info['unique_components']}")
        print("\nTop 10 Components:")
        for component, count in list(info['component_counts'].items())[:10]:
            print(f"  {component}: {count}")
    
    if 'date_range' in info:
        print(f"\nDate Range:")
        print(f"  Start: {info['date_range']['start']}")
        print(f"  End: {info['date_range']['end']}")
    
    print("\nMissing Values:")
    for col, count in info['missing_values'].items():
        if count > 0:
            print(f"  {col}: {count}")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    # Test data loading
    logging.basicConfig(level=logging.INFO)
    
    try:
        df = load_dataset()
        print_dataset_summary(df)
        print(f"\nFirst 5 rows:")
        print(df.head())
    except Exception as e:
        print(f"Error loading dataset: {e}")
        import traceback
        traceback.print_exc()

