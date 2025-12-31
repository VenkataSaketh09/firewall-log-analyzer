#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

print("Testing imports...")
print(f"Project root: {project_root}")
print(f"Python path includes: {project_root}")

try:
    print("\n1. Testing config import...")
    from ml_engine.config.ml_config import DATASET_CSV, TRAINING_CONFIG
    print("   ✓ Config import successful")
    print(f"   Dataset path: {DATASET_CSV}")
    
    print("\n2. Testing data_loader import...")
    from ml_engine.training.data_loader import load_dataset
    print("   ✓ data_loader import successful")
    
    print("\n3. Testing data_labeler import...")
    from ml_engine.training.data_labeler import label_dataset
    print("   ✓ data_labeler import successful")
    
    print("\n4. Testing data_splitter import...")
    from ml_engine.training.data_splitter import split_dataset
    print("   ✓ data_splitter import successful")
    
    print("\n5. Testing required packages...")
    try:
        import pandas as pd
        print(f"   ✓ pandas {pd.__version__}")
    except ImportError:
        print("   ✗ pandas not installed")
        print("   Run: pip install pandas")
    
    try:
        import numpy as np
        print(f"   ✓ numpy {np.__version__}")
    except ImportError:
        print("   ✗ numpy not installed")
        print("   Run: pip install numpy")
    
    try:
        import sklearn
        print(f"   ✓ scikit-learn {sklearn.__version__}")
    except ImportError:
        print("   ✗ scikit-learn not installed")
        print("   Run: pip install scikit-learn")
    
    print("\n" + "="*60)
    print("All imports successful! ✓")
    print("="*60)
    
except ImportError as e:
    print(f"\n✗ Import error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure you're in the project root directory")
    print("2. Install dependencies: pip install -r backend/requirements.txt")
    print("3. Or activate virtual environment if using one")
    sys.exit(1)

except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

