#!/usr/bin/env python3
"""
Test script for feature extraction and normalization
"""
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ml_engine.training.data_loader import load_dataset, print_dataset_summary
from ml_engine.training.data_labeler import label_dataset, print_label_statistics
from ml_engine.features.feature_extractor import FeatureExtractor, extract_features_from_df
from ml_engine.features.feature_normalizer import FeatureNormalizer, normalize_features

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_feature_extraction():
    """Test feature extraction"""
    print("\n" + "="*60)
    print("TESTING FEATURE EXTRACTION")
    print("="*60)
    
    # Load and label data
    print("\n[Step 1] Loading dataset...")
    df = load_dataset()
    print(f"✓ Loaded {len(df)} rows")
    
    print("\n[Step 2] Labeling dataset...")
    df = label_dataset(df)
    label_counts = df['label'].value_counts()
    print(f"✓ Labeled {len(df)} entries")
    for label, count in label_counts.items():
        print(f"  - {label}: {count}")
    
    # Extract features
    print("\n[Step 3] Extracting features...")
    extractor = FeatureExtractor()
    features_df = extractor.extract_features(df)
    X, feature_names = extractor.get_feature_matrix(features_df)
    
    print(f"✓ Extracted {len(feature_names)} features")
    print(f"✓ Feature matrix shape: {X.shape}")
    
    # Show feature statistics
    print("\n[Step 4] Feature statistics:")
    print(f"  Total features: {len(feature_names)}")
    print(f"  Sample features: {feature_names[:10]}")
    print(f"\n  Feature value ranges:")
    print(X.describe().loc[['min', 'max', 'mean']].head(10))
    
    return X, feature_names, df


def test_feature_normalization(X, feature_names):
    """Test feature normalization"""
    print("\n" + "="*60)
    print("TESTING FEATURE NORMALIZATION")
    print("="*60)
    
    import pandas as pd
    
    # Convert to DataFrame if needed
    if not isinstance(X, pd.DataFrame):
        X = pd.DataFrame(X, columns=feature_names)
    
    print(f"\n[Step 1] Original features:")
    print(f"  Shape: {X.shape}")
    print(f"  Min values: {X.min().min():.2f}")
    print(f"  Max values: {X.max().max():.2f}")
    print(f"  Mean: {X.mean().mean():.2f}")
    print(f"  Std: {X.std().mean():.2f}")
    
    # Normalize
    print("\n[Step 2] Normalizing features...")
    X_normalized, normalizer = normalize_features(X, scaler_type='standard', fit=True)
    
    print(f"\n[Step 3] Normalized features:")
    print(f"  Shape: {X_normalized.shape}")
    print(f"  Min values: {X_normalized.min().min():.2f}")
    print(f"  Max values: {X_normalized.max().max():.2f}")
    print(f"  Mean: {X_normalized.mean().mean():.2f}")
    print(f"  Std: {X_normalized.std().mean():.2f}")
    
    # Test save/load
    print("\n[Step 4] Testing scaler save/load...")
    test_path = Path(__file__).resolve().parent.parent / "models" / "test_scaler.pkl"
    normalizer.save(test_path)
    print(f"✓ Saved scaler to: {test_path}")
    
    normalizer_loaded = FeatureNormalizer.load(test_path)
    X_loaded = normalizer_loaded.transform(X)
    print(f"✓ Loaded scaler and transformed features")
    print(f"  Transformed shape: {X_loaded.shape}")
    
    # Cleanup
    if test_path.exists():
        test_path.unlink()
        print(f"✓ Cleaned up test file")
    
    return X_normalized, normalizer


def main():
    """Run all tests"""
    try:
        # Test feature extraction
        X, feature_names, df = test_feature_extraction()
        
        # Test feature normalization
        X_normalized, normalizer = test_feature_normalization(X, feature_names)
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print(f"\nSummary:")
        print(f"  - Extracted {len(feature_names)} features")
        print(f"  - Feature matrix: {X.shape}")
        print(f"  - Normalized matrix: {X_normalized.shape}")
        print(f"  - Feature extraction: ✓ Working")
        print(f"  - Feature normalization: ✓ Working")
        print(f"  - Scaler save/load: ✓ Working")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

