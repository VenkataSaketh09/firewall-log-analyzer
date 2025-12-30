"""
ML Engine Configuration
Contains all configuration settings for ML models, training, and inference
"""
import os
from pathlib import Path
from typing import Dict, Any

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
DATASET_DIR = BASE_DIR / "dataset"
TRAINING_DIR = BASE_DIR / "training"
INFERENCE_DIR = BASE_DIR / "inference"

# Model file paths
ANOMALY_DETECTOR_MODEL = MODELS_DIR / "anomaly_detector.pkl"
THREAT_CLASSIFIER_MODEL = MODELS_DIR / "threat_classifier.pkl"
FEATURE_SCALER = MODELS_DIR / "feature_scaler.pkl"
LABEL_ENCODER = MODELS_DIR / "label_encoder.pkl"

# Metrics / metadata
ANOMALY_METRICS_FILE = MODELS_DIR / "anomaly_metrics.json"
CLASSIFIER_METRICS_FILE = MODELS_DIR / "classifier_metrics.json"
MODEL_METADATA_FILE = MODELS_DIR / "model_metadata.json"

# Phase 11: model versioning
MODEL_VERSIONS_DIR = MODELS_DIR / "versions"
ACTIVE_VERSION_FILE = MODELS_DIR / "ACTIVE_VERSION.txt"

# Dataset paths
DATASET_CSV = DATASET_DIR / "Linux_2k.log_structured.csv"
DATASET_TEMPLATES = DATASET_DIR / "Linux_2k.log_templates.csv"

# Training Configuration
TRAINING_CONFIG: Dict[str, Any] = {
    # Data split ratios
    "train_ratio": 0.70,
    "validation_ratio": 0.15,
    "test_ratio": 0.15,
    
    # Random seed for reproducibility
    "random_seed": 42,
    
    # Anomaly Detection Model (Isolation Forest)
    "anomaly_detector": {
        "n_estimators": 100,
        "max_samples": "auto",
        "contamination": 0.1,  # Expected proportion of anomalies
        "random_state": 42,
        "n_jobs": -1  # Use all available cores
    },
    
    # Threat Classifier Model (Random Forest)
    "threat_classifier": {
        "n_estimators": 100,
        "max_depth": 20,
        "min_samples_split": 5,
        "min_samples_leaf": 2,
        "random_state": 42,
        "n_jobs": -1,
        "class_weight": "balanced"  # Handle class imbalance
    },
    
    # Feature Engineering
    "feature_engineering": {
        "use_time_features": True,
        "use_ip_features": True,
        "use_event_features": True,
        "use_frequency_features": True,
        "use_sequence_features": False,  # Enable in Phase 3
        "normalize_features": True,
        "scaler_type": "standard"  # "standard" or "minmax"
    }
}

# Inference Configuration
INFERENCE_CONFIG: Dict[str, Any] = {
    # Confidence thresholds
    "anomaly_threshold": 0.5,  # Above this score = anomaly
    "classification_confidence_threshold": 0.6,  # Minimum confidence for classification
    "risk_score_threshold": 50.0,  # Risk score threshold (0-100)
    
    # Performance settings
    "batch_size": 100,  # Process logs in batches
    "cache_features": True,  # Cache computed features
    "max_inference_time_ms": 100  # Target inference time
}

# Model Labels
THREAT_LABELS = {
    0: "NORMAL",
    1: "BRUTE_FORCE",
    2: "SUSPICIOUS",
    3: "DDOS",  # For future use
    4: "PORT_SCAN"  # For future use
}

LABEL_TO_ID = {v: k for k, v in THREAT_LABELS.items()}

# Feature Names (will be populated during training)
FEATURE_NAMES = []

# ML Service Configuration
ML_SERVICE_CONFIG: Dict[str, Any] = {
    # Enable/disable ML features
    "enabled": os.getenv("ML_ENABLED", "true").lower() == "true",
    
    # Model loading
    "load_models_on_startup": True,
    "lazy_load": False,  # Load models on first use instead of startup
    
    # Fallback behavior
    "fallback_to_rules": True,  # Use rule-based if ML fails
    "log_ml_predictions": True,  # Log all ML predictions
    
    # Retraining
    "auto_retrain": False,  # Enable automatic retraining
    "retrain_interval_days": 7,  # Retrain every N days
    "min_logs_for_retrain": 1000  # Minimum logs needed for retraining
}

# Database Configuration for ML
ML_DB_CONFIG: Dict[str, Any] = {
    "ml_predictions_collection": "ml_predictions",
    "ml_training_history_collection": "ml_training_history",
    "ml_features_cache_collection": "ml_features_cache",
    "cache_ttl_hours": 24  # Feature cache time-to-live
}

# Logging Configuration
ML_LOGGING_CONFIG: Dict[str, Any] = {
    "log_predictions": True,
    "log_inference_time": True,
    "log_model_performance": True,
    "log_level": "INFO"
}

def get_model_path(model_name: str) -> Path:
    """Get the full path to a model file"""
    model_paths = {
        "anomaly_detector": ANOMALY_DETECTOR_MODEL,
        "threat_classifier": THREAT_CLASSIFIER_MODEL,
        "feature_scaler": FEATURE_SCALER,
        "label_encoder": LABEL_ENCODER
    }
    return model_paths.get(model_name, MODELS_DIR / f"{model_name}.pkl")

def ensure_directories():
    """Ensure all required directories exist"""
    directories = [MODELS_DIR, DATASET_DIR, TRAINING_DIR, INFERENCE_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    return directories

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Validate data split ratios
    total_ratio = (
        TRAINING_CONFIG["train_ratio"] +
        TRAINING_CONFIG["validation_ratio"] +
        TRAINING_CONFIG["test_ratio"]
    )
    if abs(total_ratio - 1.0) > 0.01:
        errors.append(f"Data split ratios must sum to 1.0, got {total_ratio}")
    
    # Validate thresholds
    if not 0 <= INFERENCE_CONFIG["anomaly_threshold"] <= 1:
        errors.append("Anomaly threshold must be between 0 and 1")
    
    if not 0 <= INFERENCE_CONFIG["classification_confidence_threshold"] <= 1:
        errors.append("Classification confidence threshold must be between 0 and 1")
    
    if errors:
        raise ValueError(f"Configuration errors: {'; '.join(errors)}")
    
    return True

# Initialize directories on import
ensure_directories()

# Validate configuration on import
try:
    validate_config()
except ValueError as e:
    print(f"Warning: Configuration validation failed: {e}")

