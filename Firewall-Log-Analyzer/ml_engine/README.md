# ML Engine - Firewall Log Analyzer

Machine Learning components for threat detection and anomaly analysis.

## Directory Structure

```
ml_engine/
├── __init__.py                 # Package initialization
├── requirements.txt            # ML-specific dependencies
├── README.md                   # This file
│
├── config/                     # Configuration files
│   ├── __init__.py
│   └── ml_config.py           # ML configuration settings
│
├── dataset/                    # Training datasets
│   ├── Linux_2k.log
│   ├── Linux_2k.log_structured.csv
│   ├── Linux_2k.log_templates.csv
│   └── Processed Version.xlsx
│
├── models/                     # Trained model files (generated)
│   ├── __init__.py
│   ├── anomaly_detector.pkl    # Isolation Forest model
│   ├── threat_classifier.pkl  # Random Forest classifier
│   ├── feature_scaler.pkl      # Feature normalization scaler
│   └── label_encoder.pkl       # Label encoder
│
├── training/                   # Training scripts
│   ├── __init__.py
│   ├── data_loader.py         # Dataset loading utilities
│   ├── data_labeler.py        # Data labeling functions
│   ├── train_anomaly_detector.py
│   ├── train_threat_classifier.py
│   └── evaluate_models.py
│
├── inference/                  # Real-time prediction scripts
│   ├── __init__.py
│   ├── model_loader.py        # Model loading utilities
│   └── predictor.py           # Prediction functions
│
├── features/                   # Feature engineering
│   ├── __init__.py
│   └── feature_extractor.py   # Feature extraction functions
│
└── utils/                      # Helper utilities
    └── __init__.py
```

## Configuration

All ML configuration is stored in `config/ml_config.py`:

- **Training Configuration**: Data splits, model parameters, feature engineering settings
- **Inference Configuration**: Confidence thresholds, performance settings
- **Model Paths**: Locations for saved models and scalers
- **Service Configuration**: ML service behavior and retraining settings

## Dependencies

ML Engine requires:
- scikit-learn (model training and inference)
- pandas (data manipulation)
- numpy (numerical operations)
- joblib (model serialization)
- imbalanced-learn (handling class imbalance)

These are included in `backend/requirements.txt` for integration.

## Usage

### Training Models

```python
from ml_engine.training.train_anomaly_detector import train_anomaly_model
from ml_engine.training.train_threat_classifier import train_classifier_model

# Train anomaly detection model
train_anomaly_model()

# Train threat classifier
train_classifier_model()
```

### Using Models for Inference

```python
from ml_engine.inference.predictor import predict_anomaly, predict_threat_type

# Predict anomaly score
anomaly_score = predict_anomaly(log_features)

# Classify threat type
threat_type, confidence = predict_threat_type(log_features)
```

## Model Types

1. **Anomaly Detector** (Isolation Forest)
   - Detects unusual patterns in logs
   - Returns anomaly score (0-1)
   - Unsupervised learning

2. **Threat Classifier** (Random Forest)
   - Classifies threats into categories
   - Returns class probabilities
   - Supervised learning

## Status

✅ Phase 1: Setup & Infrastructure - Complete
- Directory structure created
- Dependencies added
- Configuration file created
- Package initialization complete

## Next Steps

- Phase 2: Data Preparation
- Phase 3: Feature Engineering
- Phase 4: Model Training

