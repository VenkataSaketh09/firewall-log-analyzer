"""
Feature Normalizer Module
Normalizes and scales features for ML models
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
import logging
import sys
from pathlib import Path
import joblib

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
    from ml_engine.config.ml_config import FEATURE_SCALER, TRAINING_CONFIG
except ImportError:
    StandardScaler = None
    MinMaxScaler = None
    RobustScaler = None
    FEATURE_SCALER = None
    TRAINING_CONFIG = {"feature_engineering": {"scaler_type": "standard"}}

logger = logging.getLogger(__name__)


class FeatureNormalizer:
    """
    Normalizes and scales features for ML models.
    """
    
    def __init__(self, scaler_type: str = "standard"):
        """
        Initialize feature normalizer.
        
        Args:
            scaler_type: Type of scaler ("standard", "minmax", "robust")
        """
        if StandardScaler is None:
            raise ImportError("scikit-learn is required for feature normalization")
        
        self.scaler_type = scaler_type
        self.scaler = None
        self.feature_names = []
        
        # Create appropriate scaler
        if scaler_type == "standard":
            self.scaler = StandardScaler()
        elif scaler_type == "minmax":
            self.scaler = MinMaxScaler()
        elif scaler_type == "robust":
            self.scaler = RobustScaler()
        else:
            raise ValueError(f"Unknown scaler type: {scaler_type}")
        
        logger.info(f"Initialized {scaler_type} scaler")
    
    def fit(self, X: pd.DataFrame):
        """
        Fit the scaler on training data.
        
        Args:
            X: Feature matrix (DataFrame)
        """
        logger.info(f"Fitting {self.scaler_type} scaler on {X.shape[0]} samples, {X.shape[1]} features")
        
        # Store feature names
        self.feature_names = list(X.columns)
        
        # Fit scaler
        self.scaler.fit(X.values)
        
        logger.info("Scaler fitted successfully")
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform features using fitted scaler.
        
        Args:
            X: Feature matrix (DataFrame)
        
        Returns:
            Scaled feature matrix (DataFrame)
        """
        if self.scaler is None:
            raise ValueError("Scaler not fitted. Call fit() first.")
        
        # Ensure same columns as training
        if list(X.columns) != self.feature_names:
            logger.warning(f"Feature columns don't match. Expected {len(self.feature_names)}, got {len(X.columns)}")
            # Reorder columns to match
            missing_cols = set(self.feature_names) - set(X.columns)
            if missing_cols:
                logger.warning(f"Missing columns: {missing_cols}")
                for col in missing_cols:
                    X[col] = 0
            
            # Select only expected columns in correct order
            X = X[self.feature_names]
        
        # Transform
        X_scaled = self.scaler.transform(X.values)
        
        # Convert back to DataFrame
        X_scaled_df = pd.DataFrame(X_scaled, columns=self.feature_names, index=X.index)
        
        return X_scaled_df
    
    def fit_transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Fit scaler and transform features.
        
        Args:
            X: Feature matrix (DataFrame)
        
        Returns:
            Scaled feature matrix (DataFrame)
        """
        self.fit(X)
        return self.transform(X)
    
    def save(self, filepath: Optional[Path] = None):
        """
        Save fitted scaler to disk.
        
        Args:
            filepath: Path to save scaler (uses config default if None)
        """
        if self.scaler is None:
            raise ValueError("Scaler not fitted. Call fit() first.")
        
        if filepath is None:
            filepath = FEATURE_SCALER if FEATURE_SCALER else Path(__file__).resolve().parent.parent / "models" / "feature_scaler.pkl"
        
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Save scaler and metadata
        save_data = {
            'scaler': self.scaler,
            'scaler_type': self.scaler_type,
            'feature_names': self.feature_names
        }
        
        joblib.dump(save_data, filepath)
        logger.info(f"Saved scaler to: {filepath}")
    
    @classmethod
    def load(cls, filepath: Optional[Path] = None) -> 'FeatureNormalizer':
        """
        Load fitted scaler from disk.
        
        Args:
            filepath: Path to load scaler from (uses config default if None)
        
        Returns:
            FeatureNormalizer instance with loaded scaler
        """
        if filepath is None:
            filepath = FEATURE_SCALER if FEATURE_SCALER else Path(__file__).resolve().parent.parent / "models" / "feature_scaler.pkl"
        
        if not filepath.exists():
            raise FileNotFoundError(f"Scaler file not found: {filepath}")
        
        # Load scaler and metadata
        save_data = joblib.load(filepath)
        
        # Create instance
        normalizer = cls(scaler_type=save_data['scaler_type'])
        normalizer.scaler = save_data['scaler']
        normalizer.feature_names = save_data['feature_names']
        
        logger.info(f"Loaded scaler from: {filepath}")
        logger.info(f"Scaler type: {save_data['scaler_type']}, Features: {len(save_data['feature_names'])}")
        
        return normalizer


def normalize_features(
    X: pd.DataFrame,
    scaler_type: str = "standard",
    fit: bool = True,
    scaler_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, Optional[FeatureNormalizer]]:
    """
    Convenience function to normalize features.
    
    Args:
        X: Feature matrix (DataFrame)
        scaler_type: Type of scaler ("standard", "minmax", "robust")
        fit: Whether to fit scaler (True) or load existing (False)
        scaler_path: Path to save/load scaler
    
    Returns:
        Tuple of (normalized_features, normalizer)
    """
    normalizer = FeatureNormalizer(scaler_type=scaler_type)
    
    if fit:
        X_normalized = normalizer.fit_transform(X)
        if scaler_path:
            normalizer.save(scaler_path)
    else:
        if scaler_path:
            normalizer = FeatureNormalizer.load(scaler_path)
        X_normalized = normalizer.transform(X)
    
    return X_normalized, normalizer


if __name__ == "__main__":
    # Test feature normalization
    logging.basicConfig(level=logging.INFO)
    
    try:
        from ml_engine.features.feature_extractor import extract_features_from_df
        from ml_engine.training.data_loader import load_dataset
        from ml_engine.training.data_labeler import label_dataset
        
        print("Testing feature normalization...")
        
        # Load and prepare data
        df = load_dataset()
        df = label_dataset(df)
        
        # Extract features
        X, feature_names = extract_features_from_df(df)
        print(f"\nOriginal features shape: {X.shape}")
        print(f"Feature ranges before normalization:")
        print(X.describe().loc[['min', 'max']])
        
        # Normalize features
        X_normalized, normalizer = normalize_features(X, scaler_type="standard", fit=True)
        print(f"\nNormalized features shape: {X_normalized.shape}")
        print(f"Feature ranges after normalization:")
        print(X_normalized.describe().loc[['min', 'max', 'mean', 'std']])
        
        # Test save/load
        test_path = Path(__file__).resolve().parent.parent / "models" / "test_scaler.pkl"
        normalizer.save(test_path)
        normalizer_loaded = FeatureNormalizer.load(test_path)
        print(f"\n✓ Scaler save/load test successful")
        
    except Exception as e:
        print(f"Error in feature normalization: {e}")
        import traceback
        traceback.print_exc()

