"""
Feature Extractor Module
Extracts features from log entries for ML model training and inference
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
import re
from datetime import datetime
import hashlib
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from ml_engine.config.ml_config import TRAINING_CONFIG
except ImportError:
    TRAINING_CONFIG = {
        "feature_engineering": {
            "use_time_features": True,
            "use_ip_features": True,
            "use_event_features": True,
            "use_frequency_features": True,
            "normalize_features": True,
            "scaler_type": "standard"
        }
    }

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Main feature extraction class for firewall logs.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize feature extractor.
        
        Args:
            config: Feature engineering configuration
        """
        self.config = config or TRAINING_CONFIG.get("feature_engineering", {})
        self.feature_names = []
        
    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract all features from log DataFrame.
        
        Args:
            df: DataFrame with log entries
        
        Returns:
            DataFrame with extracted features
        """
        logger.info("Extracting features from log data...")
        
        # Make a copy to avoid modifying original
        features_df = df.copy()
        
        # Extract different feature types
        if self.config.get("use_ip_features", True):
            features_df = self._extract_ip_features(features_df)
        
        if self.config.get("use_time_features", True):
            features_df = self._extract_time_features(features_df)
        
        if self.config.get("use_event_features", True):
            features_df = self._extract_event_features(features_df)
        
        if self.config.get("use_frequency_features", True):
            features_df = self._extract_frequency_features(features_df)
        
        # Store feature names (excluding original columns and label)
        original_cols = set(df.columns)
        self.feature_names = [col for col in features_df.columns 
                             if col not in original_cols and col != 'label' and col != 'label_id']
        
        logger.info(f"Extracted {len(self.feature_names)} features")
        logger.info(f"Feature names: {self.feature_names[:10]}..." if len(self.feature_names) > 10 else f"Feature names: {self.feature_names}")
        
        return features_df

    @staticmethod
    def _stable_hash_mod(value: Any, mod: int) -> int:
        """
        Deterministic hash for feature encoding.

        NOTE: Python's built-in hash() is salted per process, so it is not stable across runs.
        We use a stable hash to ensure training/inference consistency.
        """
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return 0
        s = str(value).encode("utf-8", errors="ignore")
        # 64-bit digest is plenty for modulo bucketing
        digest = hashlib.blake2b(s, digest_size=8).digest()
        return int.from_bytes(digest, byteorder="big", signed=False) % mod
    
    def _extract_ip_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract IP-based features.
        
        Features:
        - IP address extracted from Content
        - IP hash (for anonymization)
        - IP frequency count
        - Unique IPs per time window
        """
        logger.info("Extracting IP-based features...")
        
        # Extract IP addresses from Content field
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        df['extracted_ip'] = df['Content'].str.extract(f'({ip_pattern})', expand=False)
        
        # IP hash (for anonymization while preserving uniqueness)
        df['ip_hash'] = df['extracted_ip'].apply(lambda x: self._stable_hash_mod(x, 10000) if pd.notna(x) else 0)
        
        # Count occurrences of each IP
        ip_counts = df['extracted_ip'].value_counts().to_dict()
        df['ip_frequency'] = df['extracted_ip'].map(ip_counts).fillna(0)
        
        # Check if IP appears multiple times (indicator of attack)
        df['ip_is_repeated'] = (df['ip_frequency'] > 1).astype(int)
        
        # IP frequency category (low, medium, high)
        df['ip_freq_category'] = pd.cut(
            df['ip_frequency'],
            bins=[0, 1, 5, float('inf')],
            labels=[0, 1, 2]  # 0=low, 1=medium, 2=high
        )
        # Fill NaN and convert to int
        df['ip_freq_category'] = df['ip_freq_category'].fillna(0).astype(int)
        
        # Check if IP is in Content field
        df['has_ip'] = df['extracted_ip'].notna().astype(int)
        
        return df
    
    def _extract_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract time-based features.
        
        Features:
        - Hour of day (0-23)
        - Day of week (0-6)
        - Month (1-12)
        - Is weekend (0/1)
        - Is business hours (0/1)
        - Time since last event (if datetime available)
        """
        logger.info("Extracting time-based features...")
        
        # Ensure datetime column exists and is actually datetimelike.
        # NOTE: when loading saved CSV splits, 'datetime' often comes back as string/object.
        if 'datetime' not in df.columns:
            try:
                datetime_str = (
                    df['Month'].astype(str)
                    + ' '
                    + df['Date'].astype(str)
                    + ' '
                    + df['Time'].astype(str)
                    + ' 2005'
                )
                df['datetime'] = pd.to_datetime(datetime_str, format='%b %d %H:%M:%S %Y', errors='coerce')
            except Exception:
                df['datetime'] = pd.Timestamp.now()
        else:
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')

        # If parsing failed for some rows, fill with a stable default (keeps feature extraction robust)
        if df['datetime'].isna().any():
            df['datetime'] = df['datetime'].fillna(pd.Timestamp('2005-06-14 00:00:00'))
        
        # Extract time components
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week'] = df['datetime'].dt.dayofweek  # 0=Monday, 6=Sunday
        df['month'] = df['datetime'].dt.month
        df['day_of_month'] = df['datetime'].dt.day
        
        # Cyclical encoding for time features (better for ML)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Time-based categories
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)  # Saturday=5, Sunday=6
        df['is_business_hours'] = ((df['hour'] >= 9) & (df['hour'] <= 17)).astype(int)
        df['is_night'] = ((df['hour'] >= 22) | (df['hour'] < 6)).astype(int)
        df['is_morning'] = ((df['hour'] >= 6) & (df['hour'] < 12)).astype(int)
        df['is_afternoon'] = ((df['hour'] >= 12) & (df['hour'] < 18)).astype(int)
        df['is_evening'] = ((df['hour'] >= 18) & (df['hour'] < 22)).astype(int)
        
        # Time since last event (if sorted by datetime)
        # Note: This feature is excluded from the feature matrix as it wasn't in the training set
        # Always create it to ensure consistent feature extraction, but it will be excluded in get_feature_matrix
        if df['datetime'].is_monotonic_increasing or df['datetime'].is_monotonic_decreasing:
            df['time_since_last'] = df['datetime'].diff().dt.total_seconds().fillna(0)
            df['time_since_last'] = df['time_since_last'].clip(lower=0, upper=3600)  # Cap at 1 hour
        else:
            # Always create the column for consistency, even if not monotonic
            df['time_since_last'] = 0
        
        return df
    
    def _extract_event_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract event-based features.
        
        Features:
        - EventId encoding
        - Component encoding
        - EventTemplate length
        - Content length
        - Has authentication failure
        - Has connection attempt
        """
        logger.info("Extracting event-based features...")
        
        # EventId features
        if 'EventId' in df.columns:
            # EventId hash (for encoding)
            df['event_id_hash'] = df['EventId'].apply(lambda x: self._stable_hash_mod(x, 1000) if pd.notna(x) else 0)
            
            # Check for specific event patterns
            df['is_auth_failure'] = df['EventId'].str.contains('E16|E17|E18|E27', na=False).astype(int)
            df['is_session_event'] = df['EventId'].str.contains('E101|E102', na=False).astype(int)
            df['is_connection_event'] = df['EventId'].str.contains('E29', na=False).astype(int)
        
        # Component features
        if 'Component' in df.columns:
            # Component hash
            df['component_hash'] = df['Component'].apply(lambda x: self._stable_hash_mod(x, 100) if pd.notna(x) else 0)
            
            # Check for specific components
            df['is_sshd'] = df['Component'].str.contains('sshd', case=False, na=False).astype(int)
            df['is_ftpd'] = df['Component'].str.contains('ftpd', case=False, na=False).astype(int)
            df['is_kernel'] = df['Component'].str.contains('kernel', case=False, na=False).astype(int)
            df['is_su'] = df['Component'].str.contains('su', case=False, na=False).astype(int)
        
        # Content features
        if 'Content' in df.columns:
            df['content_length'] = df['Content'].str.len().fillna(0)
            df['content_word_count'] = df['Content'].str.split().str.len().fillna(0)
            
            # Check for specific patterns in content
            df['has_user'] = df['Content'].str.contains('user=', case=False, na=False).astype(int)
            df['has_rhost'] = df['Content'].str.contains('rhost=', case=False, na=False).astype(int)
            df['has_failure'] = df['Content'].str.contains('failure|failed|denied', case=False, na=False).astype(int)
            df['has_authentication'] = df['Content'].str.contains('authentication|auth', case=False, na=False).astype(int)
            df['has_connection'] = df['Content'].str.contains('connection', case=False, na=False).astype(int)
            df['has_session'] = df['Content'].str.contains('session', case=False, na=False).astype(int)
        
        # EventTemplate features
        if 'EventTemplate' in df.columns:
            df['template_length'] = df['EventTemplate'].str.len().fillna(0)
            df['template_word_count'] = df['EventTemplate'].str.split().str.len().fillna(0)
        
        return df
    
    def _extract_frequency_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract frequency and statistical features.
        
        Features:
        - Event frequency per IP
        - Event frequency per time window
        - Unique events per IP
        - Burst patterns
        """
        logger.info("Extracting frequency-based features...")
        
        # Event frequency per IP (if IP available)
        if 'extracted_ip' in df.columns:
            # Count unique events per IP
            ip_event_counts = df.groupby('extracted_ip')['EventId'].nunique().to_dict()
            df['unique_events_per_ip'] = df['extracted_ip'].map(ip_event_counts).fillna(0)
            
            # Count total events per IP
            ip_total_counts = df['extracted_ip'].value_counts().to_dict()
            df['total_events_per_ip'] = df['extracted_ip'].map(ip_total_counts).fillna(0)
        
        # Event frequency overall
        if 'EventId' in df.columns:
            event_counts = df['EventId'].value_counts().to_dict()
            df['event_frequency'] = df['EventId'].map(event_counts).fillna(0)
        
        # Component frequency
        if 'Component' in df.columns:
            component_counts = df['Component'].value_counts().to_dict()
            df['component_frequency'] = df['Component'].map(component_counts).fillna(0)
        
        # Time-based frequency (events per hour if datetime available)
        if 'datetime' in df.columns and 'hour' in df.columns:
            hour_event_counts = df.groupby('hour').size().to_dict()
            df['events_per_hour'] = df['hour'].map(hour_event_counts).fillna(0)
        
        # Burst detection (multiple events in short time)
        if 'datetime' in df.columns:
            # Sort by datetime if not already sorted
            if not df['datetime'].is_monotonic_increasing:
                df = df.sort_values('datetime').reset_index(drop=True)
            
            # Calculate time differences
            time_diffs = df['datetime'].diff().dt.total_seconds().fillna(0)
            
            # Burst: multiple events within 1 minute
            df['is_burst'] = (time_diffs < 60).astype(int)
            
            # Count consecutive bursts
            df['burst_count'] = (df['is_burst'] == 1).groupby((df['is_burst'] != df['is_burst'].shift()).cumsum()).cumsum()
        
        return df
    
    def get_feature_names(self) -> List[str]:
        """
        Get list of extracted feature names.
        
        Returns:
            List of feature column names
        """
        return self.feature_names
    
    def get_feature_matrix(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Get feature matrix (X) and feature names.
        
        Args:
            df: DataFrame with extracted features
        
        Returns:
            Tuple of (feature_matrix, feature_names)
        """
        # Select only feature columns (exclude original columns and labels)
        # Also exclude 'time_since_last' as it wasn't in the training set (model expects 47 features)
        feature_cols = [col for col in df.columns 
                       if col not in ['LineId', 'Month', 'Date', 'Time', 'Level', 
                                     'Component', 'PID', 'Content', 'EventId', 
                                     'EventTemplate', 'datetime', 'label', 'label_id',
                                     'extracted_ip', 'time_since_last']]  # Exclude extracted_ip and time_since_last
        
        X = df[feature_cols].copy()
        
        # Fill any remaining NaN values
        X = X.fillna(0)
        
        return X, feature_cols


def extract_features_from_df(df: pd.DataFrame, config: Optional[Dict] = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Convenience function to extract features from DataFrame.
    
    Args:
        df: DataFrame with log entries
        config: Optional feature engineering configuration
    
    Returns:
        Tuple of (DataFrame with features, feature_names)
    """
    extractor = FeatureExtractor(config)
    features_df = extractor.extract_features(df)
    X, feature_names = extractor.get_feature_matrix(features_df)
    return X, feature_names


if __name__ == "__main__":
    # Test feature extraction
    logging.basicConfig(level=logging.INFO)
    
    try:
        from ml_engine.training.data_loader import load_dataset
        from ml_engine.training.data_labeler import label_dataset
        
        print("Testing feature extraction...")
        df = load_dataset()
        df = label_dataset(df)
        
        extractor = FeatureExtractor()
        features_df = extractor.extract_features(df)
        X, feature_names = extractor.get_feature_matrix(features_df)
        
        print(f"\n✓ Extracted {len(feature_names)} features")
        print(f"\nFeature names: {feature_names}")
        print(f"\nFeature matrix shape: {X.shape}")
        print(f"\nFirst few features:")
        print(X.head())
        
    except Exception as e:
        print(f"Error in feature extraction: {e}")
        import traceback
        traceback.print_exc()

