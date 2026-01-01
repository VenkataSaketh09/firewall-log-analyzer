# Training Module - Data Preparation

This module handles all data preparation tasks for ML model training.

## Files

### 1. `data_loader.py`
Loads and validates the dataset from CSV files.

**Key Functions:**
- `load_dataset()` - Load CSV dataset with validation
- `validate_and_clean_data()` - Clean and validate data
- `create_datetime_column()` - Create datetime from Month/Date/Time
- `get_dataset_info()` - Get dataset statistics
- `print_dataset_summary()` - Print dataset summary

**Usage:**
```python
from ml_engine.training.data_loader import load_dataset, print_dataset_summary

df = load_dataset()
print_dataset_summary(df)
```

### 2. `data_labeler.py`
Labels log entries based on patterns and event types.

**Labels:**
- `NORMAL` - Normal system events
- `BRUTE_FORCE` - Authentication failures, brute force attacks
- `SUSPICIOUS` - Suspicious patterns

**Key Functions:**
- `label_dataset()` - Main labeling function
- `label_brute_force()` - Label brute force attacks
- `label_suspicious()` - Label suspicious activities
- `get_label_statistics()` - Get label distribution stats
- `print_label_statistics()` - Print label statistics

**Usage:**
```python
from ml_engine.training.data_labeler import label_dataset, print_label_statistics

labeled_df = label_dataset(df)
print_label_statistics(labeled_df)
```

### 3. `data_splitter.py`
Splits dataset into train, validation, and test sets.

**Key Functions:**
- `split_dataset()` - Split dataset with configurable ratios
- `stratified_split()` - Stratified split to maintain label distribution
- `save_splits()` - Save splits to CSV files
- `load_splits()` - Load splits from CSV files
- `print_split_statistics()` - Print split statistics

**Usage:**
```python
from ml_engine.training.data_splitter import split_dataset, save_splits

train_df, val_df, test_df = split_dataset(df, stratify='label')
save_splits(train_df, val_df, test_df, output_dir)
```

### 4. `prepare_data.py`
Complete data preparation pipeline.

**Key Functions:**
- `prepare_complete_dataset()` - Complete pipeline: load → label → split

**Usage:**
```python
from ml_engine.training.prepare_data import prepare_complete_dataset

train_df, val_df, test_df, labeled_df = prepare_complete_dataset()
```

## Quick Start

Run the complete data preparation pipeline:

```bash
cd ml_engine/training
python prepare_data.py
```

This will:
1. Load the dataset from CSV
2. Validate and clean the data
3. Label all entries
4. Split into train/validation/test sets
5. Save splits to disk (optional)

## Data Flow

```
CSV File (Linux_2k.log_structured.csv)
    ↓
data_loader.load_dataset()
    ↓
[Validated & Cleaned DataFrame]
    ↓
data_labeler.label_dataset()
    ↓
[Labeled DataFrame with 'label' and 'label_id' columns]
    ↓
data_splitter.split_dataset()
    ↓
[Train DataFrame] [Validation DataFrame] [Test DataFrame]
```

## Configuration

Data preparation uses settings from `ml_engine/config/ml_config.py`:

- **Data Split Ratios**: `TRAINING_CONFIG["train_ratio"]`, `validation_ratio`, `test_ratio`
- **Random Seed**: `TRAINING_CONFIG["random_seed"]`
- **Dataset Path**: `DATASET_CSV`

## Output Files

When `save_splits_to_disk=True`, the following files are created:

- `labeled_dataset_train.csv` - Training set
- `labeled_dataset_validation.csv` - Validation set
- `labeled_dataset_test.csv` - Test set

All files are saved in the `ml_engine/dataset/` directory.

## Label Distribution

Expected label distribution (approximate):
- **NORMAL**: ~60-70% (normal system events)
- **BRUTE_FORCE**: ~25-35% (authentication failures)
- **SUSPICIOUS**: ~5-10% (suspicious patterns)

## Notes

- Stratified splitting ensures label distribution is maintained across splits
- Missing values are handled automatically
- Datetime column is created from Month/Date/Time columns
- IP addresses are extracted from Content field for pattern detection

