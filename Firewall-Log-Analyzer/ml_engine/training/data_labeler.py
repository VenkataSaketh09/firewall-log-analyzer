"""
Data Labeler Module
Labels log entries based on patterns and event types
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
import re
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from ml_engine.config.ml_config import LABEL_TO_ID, THREAT_LABELS
except ImportError:
    # Fallback if running as standalone script
    THREAT_LABELS = {
        0: "NORMAL",
        1: "BRUTE_FORCE",
        2: "SUSPICIOUS",
        3: "DDOS",
        4: "PORT_SCAN"
    }
    LABEL_TO_ID = {v: k for k, v in THREAT_LABELS.items()}

logger = logging.getLogger(__name__)


def label_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Label the dataset based on log patterns and event types.
    
    Labels:
    - NORMAL: Normal system events (sessions, system startup, etc.)
    - BRUTE_FORCE: Authentication failures, multiple failed attempts
    - SUSPICIOUS: Suspicious patterns that don't fit other categories
    
    Args:
        df: DataFrame with log data
    
    Returns:
        DataFrame with added 'label' and 'label_id' columns
    """
    logger.info("Labeling dataset...")
    
    # Initialize label column
    df = df.copy()
    df['label'] = 'NORMAL'
    df['label_id'] = LABEL_TO_ID.get('NORMAL', 0)
    
    # Label brute force attacks
    df = label_brute_force(df)
    
    # Label suspicious activities
    df = label_suspicious(df)
    
    # Count labels
    label_counts = df['label'].value_counts()
    logger.info(f"Label distribution:\n{label_counts}")
    
    return df


def label_brute_force(df: pd.DataFrame) -> pd.DataFrame:
    """
    Label brute force attacks based on authentication failures.
    
    Brute force indicators:
    - Authentication failures (EventId: E16, E17, E18)
    - Multiple failed attempts from same IP
    - "check pass; user unknown" events
    
    Args:
        df: DataFrame to label
    
    Returns:
        DataFrame with brute force labels
    """
    logger.info("Labeling brute force attacks...")
    
    # Authentication failure event IDs
    auth_failure_events = ['E16', 'E17', 'E18', 'E27']  # E27 = "check pass; user unknown"
    
    # Label based on EventId
    brute_force_mask = df['EventId'].isin(auth_failure_events)
    
    # Also check Content field for authentication failure patterns
    auth_patterns = [
        'authentication failure',
        'check pass; user unknown',
        'Permission denied',
        'Failed password'
    ]
    
    content_mask = df['Content'].str.contains('|'.join(auth_patterns), case=False, na=False)
    
    # Combine masks
    brute_force_mask = brute_force_mask | content_mask
    
    # Apply labels
    df.loc[brute_force_mask, 'label'] = 'BRUTE_FORCE'
    df.loc[brute_force_mask, 'label_id'] = LABEL_TO_ID.get('BRUTE_FORCE', 1)
    
    brute_force_count = brute_force_mask.sum()
    logger.info(f"Labeled {brute_force_count} entries as BRUTE_FORCE")
    
    return df


def label_suspicious(df: pd.DataFrame) -> pd.DataFrame:
    """
    Label suspicious activities that don't fit other categories.
    
    Suspicious indicators:
    - Multiple connections from same IP in short time
    - Unusual event patterns
    - ALERT messages
    - Failed operations
    
    Args:
        df: DataFrame to label
    
    Returns:
        DataFrame with suspicious labels
    """
    logger.info("Labeling suspicious activities...")
    
    # Only label entries that are not already labeled as BRUTE_FORCE
    unlabeled_mask = df['label'] == 'NORMAL'
    
    # Suspicious patterns
    suspicious_patterns = [
        'ALERT',
        'exited abnormally',
        'connection from.*connection from',  # Multiple rapid connections
        'Failed',
        'Error',
        'WARNING'
    ]
    
    # Check Content field for suspicious patterns
    suspicious_mask = pd.Series([False] * len(df))
    
    for pattern in suspicious_patterns:
        pattern_mask = df['Content'].str.contains(pattern, case=False, na=False, regex=True)
        suspicious_mask = suspicious_mask | pattern_mask
    
    # Check for multiple rapid connections from same IP
    if 'datetime' in df.columns and 'Content' in df.columns:
        suspicious_mask = suspicious_mask | detect_rapid_connections(df)
    
    # Apply labels only to unlabeled entries
    final_mask = unlabeled_mask & suspicious_mask
    df.loc[final_mask, 'label'] = 'SUSPICIOUS'
    df.loc[final_mask, 'label_id'] = LABEL_TO_ID.get('SUSPICIOUS', 2)
    
    suspicious_count = final_mask.sum()
    logger.info(f"Labeled {suspicious_count} entries as SUSPICIOUS")
    
    return df


def detect_rapid_connections(df: pd.DataFrame, time_window_minutes: int = 5) -> pd.Series:
    """
    Detect rapid connections from same IP within a time window.
    
    Args:
        df: DataFrame with datetime and Content columns
        time_window_minutes: Time window in minutes to check for rapid connections
    
    Returns:
        Boolean Series indicating rapid connections
    """
    if 'datetime' not in df.columns or 'Content' not in df.columns:
        return pd.Series([False] * len(df))
    
    # Extract IP addresses from Content
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    df['extracted_ip'] = df['Content'].str.extract(f'({ip_pattern})', expand=False)
    
    # Check for connection patterns
    connection_mask = df['Content'].str.contains('connection from', case=False, na=False)
    
    # Group by IP and check for multiple connections in time window
    rapid_connection_mask = pd.Series([False] * len(df))
    
    for ip in df[connection_mask]['extracted_ip'].dropna().unique():
        ip_mask = (df['extracted_ip'] == ip) & connection_mask
        ip_entries = df[ip_mask].sort_values('datetime')
        
        if len(ip_entries) > 1:
            # Check time differences
            time_diffs = ip_entries['datetime'].diff().dt.total_seconds() / 60
            # If multiple connections within time window
            if (time_diffs < time_window_minutes).any():
                rapid_connection_mask = rapid_connection_mask | ip_mask
    
    return rapid_connection_mask


def get_label_statistics(df: pd.DataFrame) -> Dict:
    """
    Get statistics about label distribution.
    
    Args:
        df: DataFrame with 'label' column
    
    Returns:
        Dictionary with label statistics
    """
    if 'label' not in df.columns:
        return {}
    
    stats = {
        'total': len(df),
        'label_counts': df['label'].value_counts().to_dict(),
        'label_percentages': (df['label'].value_counts(normalize=True) * 100).to_dict(),
        'class_imbalance_ratio': None
    }
    
    # Calculate class imbalance ratio
    label_counts = df['label'].value_counts()
    if len(label_counts) > 1:
        max_count = label_counts.max()
        min_count = label_counts.min()
        stats['class_imbalance_ratio'] = max_count / min_count if min_count > 0 else float('inf')
    
    return stats


def print_label_statistics(df: pd.DataFrame):
    """
    Print label distribution statistics.
    
    Args:
        df: DataFrame with 'label' column
    """
    stats = get_label_statistics(df)
    
    if not stats:
        print("No label statistics available")
        return
    
    print("\n" + "="*60)
    print("LABEL STATISTICS")
    print("="*60)
    print(f"Total Entries: {stats['total']}")
    print(f"\nLabel Counts:")
    for label, count in stats['label_counts'].items():
        percentage = stats['label_percentages'].get(label, 0)
        print(f"  {label}: {count} ({percentage:.2f}%)")
    
    if stats['class_imbalance_ratio']:
        print(f"\nClass Imbalance Ratio: {stats['class_imbalance_ratio']:.2f}")
        if stats['class_imbalance_ratio'] > 10:
            print("  WARNING: High class imbalance detected. Consider using class weights.")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    # Test labeling
    logging.basicConfig(level=logging.INFO)
    
    try:
        from ml_engine.training.data_loader import load_dataset
    except ImportError:
        # Fallback for standalone execution
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from data_loader import load_dataset
    
    try:
        df = load_dataset()
        df = label_dataset(df)
        print_label_statistics(df)
        
        # Show some examples
        print("\nSample BRUTE_FORCE entries:")
        print(df[df['label'] == 'BRUTE_FORCE'][['LineId', 'EventId', 'Content', 'label']].head(10))
        
        print("\nSample NORMAL entries:")
        print(df[df['label'] == 'NORMAL'][['LineId', 'EventId', 'Content', 'label']].head(10))
        
    except Exception as e:
        print(f"Error labeling dataset: {e}")
        import traceback
        traceback.print_exc()

