# Feature Engineering Module

This module handles feature extraction and normalization for ML model training and inference.

## Files

### 1. `feature_extractor.py`
Main feature extraction module that extracts various types of features from log entries.

**Key Classes:**
- `FeatureExtractor` - Main feature extraction class

**Feature Types:**
- **IP Features**: IP extraction, frequency, repetition patterns
- **Time Features**: Hour, day, month, cyclical encoding, time categories
- **Event Features**: EventId, Component, Content patterns
- **Frequency Features**: Event frequency, burst detection, statistical features

**Usage:**
```python
from ml_engine.features.feature_extractor import FeatureExtractor, extract_features_from_df

# Method 1: Using class
extractor = FeatureExtractor()
features_df = extractor.extract_features(df)
X, feature_names = extractor.get_feature_matrix(features_df)

# Method 2: Using convenience function
X, feature_names = extract_features_from_df(df)
```

### 2. `feature_normalizer.py`
Feature normalization and scaling module.

**Key Classes:**
- `FeatureNormalizer` - Feature normalization class

**Scaler Types:**
- `standard` - StandardScaler (mean=0, std=1)
- `minmax` - MinMaxScaler (range 0-1)
- `robust` - RobustScaler (median-based, handles outliers)

**Usage:**
```python
from ml_engine.features.feature_normalizer import FeatureNormalizer, normalize_features

# Method 1: Using class
normalizer = FeatureNormalizer(scaler_type='standard')
normalizer.fit(X_train)
X_train_scaled = normalizer.transform(X_train)
normalizer.save('models/scaler.pkl')

# Method 2: Using convenience function
X_normalized, normalizer = normalize_features(X, scaler_type='standard', fit=True)
```

## Feature List

### IP-Based Features (7 features)
- `ip_frequency` - Frequency of IP in dataset
- `ip_is_repeated` - Whether IP appears multiple times
- `ip_freq_category` - IP frequency category (low/medium/high)
- `has_ip` - Whether IP is present in log
- `unique_events_per_ip` - Unique events per IP
- `total_events_per_ip` - Total events per IP

### Time-Based Features (15 features)
- `hour` - Hour of day (0-23)
- `day_of_week` - Day of week (0-6)
- `month` - Month (1-12)
- `day_of_month` - Day of month (1-31)
- `hour_sin`, `hour_cos` - Cyclical encoding of hour
- `day_sin`, `day_cos` - Cyclical encoding of day
- `month_sin`, `month_cos` - Cyclical encoding of month
- `is_weekend` - Weekend indicator
- `is_business_hours` - Business hours indicator
- `is_night`, `is_morning`, `is_afternoon`, `is_evening` - Time of day categories
- `time_since_last` - Time since last event (if available)

### Event-Based Features (15 features)
- `event_id_hash` - Hashed EventId
- `is_auth_failure` - Authentication failure indicator
- `is_session_event` - Session event indicator
- `is_connection_event` - Connection event indicator
- `component_hash` - Hashed Component
- `is_sshd`, `is_ftpd`, `is_kernel`, `is_su` - Component type indicators
- `content_length` - Content length
- `content_word_count` - Word count in content
- `has_user`, `has_rhost`, `has_failure`, `has_authentication`, `has_connection`, `has_session` - Content pattern indicators
- `template_length`, `template_word_count` - Template features

### Frequency Features (8 features)
- `event_frequency` - Overall event frequency
- `component_frequency` - Component frequency
- `events_per_hour` - Events per hour
- `is_burst` - Burst indicator (events within 1 minute)
- `burst_count` - Consecutive burst count

**Total: ~45 features** (may vary based on data)

## Testing

Run the test script:

```bash
cd ml_engine
source venv/bin/activate
python3 features/test_features.py
```

## Integration with Training Pipeline

Features are extracted before model training:

```python
# Complete pipeline
from ml_engine.training.data_loader import load_dataset
from ml_engine.training.data_labeler import label_dataset
from ml_engine.features.feature_extractor import extract_features_from_df
from ml_engine.features.feature_normalizer import normalize_features

# Load and label
df = load_dataset()
df = label_dataset(df)

# Extract features
X, feature_names = extract_features_from_df(df)
y = df['label_id']  # Labels

# Normalize features
X_normalized, normalizer = normalize_features(X, fit=True)

# Ready for model training
# X_normalized = features, y = labels
```

## Configuration

Feature extraction is configured in `ml_engine/config/ml_config.py`:

```python
"feature_engineering": {
    "use_time_features": True,
    "use_ip_features": True,
    "use_event_features": True,
    "use_frequency_features": True,
    "normalize_features": True,
    "scaler_type": "standard"  # "standard", "minmax", or "robust"
}
```

## Notes

- Features are extracted from the labeled dataset
- IP addresses are hashed for privacy while preserving uniqueness
- Time features use cyclical encoding for better ML performance
- All features are normalized before training
- Scaler is saved for use during inference

