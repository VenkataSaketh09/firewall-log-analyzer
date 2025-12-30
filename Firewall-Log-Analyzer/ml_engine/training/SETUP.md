# Setup Guide for Data Preparation

## Quick Fix for Import Errors

All import errors have been fixed! The scripts now work both as modules and standalone.

## Installing Dependencies

You need to install the ML dependencies. Choose one method:

### Option 1: Using Virtual Environment (Recommended)

```bash
# Activate virtual environment
cd /home/nulumohan/firewall-log-analyzer/Firewall-Log-Analyzer
source venv/bin/activate  # or: . venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### Option 2: Install Globally

```bash
# Install ML dependencies
pip3 install pandas numpy scikit-learn joblib imbalanced-learn
```

### Option 3: Install from Backend Requirements

```bash
pip3 install -r backend/requirements.txt
```

## Testing the Setup

After installing dependencies, test the imports:

```bash
cd /home/nulumohan/firewall-log-analyzer/Firewall-Log-Analyzer
python3 ml_engine/training/test_imports.py
```

You should see:
```
✓ Config import successful
✓ data_loader import successful
✓ data_labeler import successful
✓ data_splitter import successful
✓ pandas X.X.X
✓ numpy X.X.X
✓ scikit-learn X.X.X
All imports successful! ✓
```

## Running Data Preparation

Once dependencies are installed, you can run:

```bash
# From project root
python3 -m ml_engine.training.prepare_data

# Or directly
cd ml_engine/training
python3 prepare_data.py
```

## What Was Fixed

1. **Import Path Issues**: All files now add the project root to `sys.path` automatically
2. **Fallback Imports**: Files work even if run as standalone scripts
3. **Error Handling**: Better error messages for missing dependencies

## Common Errors and Solutions

### Error: "No module named 'pandas'"
**Solution**: Install dependencies (see above)

### Error: "No module named 'ml_engine'"
**Solution**: Run from project root directory, or use the fixed imports (already done)

### Error: "Dataset file not found"
**Solution**: Make sure `ml_engine/dataset/Linux_2k.log_structured.csv` exists

## Verification

Run the test script to verify everything works:

```bash
python3 ml_engine/training/test_imports.py
```

If all checks pass, you're ready to proceed with data preparation!

