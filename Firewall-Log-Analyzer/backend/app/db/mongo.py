import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client.firewall_analyzer
logs_collection = db.firewall_logs
ip_reputation_cache = db.ip_reputation_cache
saved_reports_collection = db.saved_reports
alerts_collection = db.alerts

# ML collections (Phase 7)
ml_predictions_collection = db.ml_predictions
ml_training_history_collection = db.ml_training_history
ml_features_cache_collection = db.ml_features_cache


def create_indexes():
    """Create database indexes for optimized queries"""
    try:
        # Single field indexes
        logs_collection.create_index([("timestamp", DESCENDING)], name="timestamp_desc")
        logs_collection.create_index([("source_ip", ASCENDING)], name="source_ip_asc")
        logs_collection.create_index([("severity", ASCENDING)], name="severity_asc")
        logs_collection.create_index([("event_type", ASCENDING)], name="event_type_asc")
        logs_collection.create_index([("destination_port", ASCENDING)], name="destination_port_asc")
        logs_collection.create_index([("protocol", ASCENDING)], name="protocol_asc")
        logs_collection.create_index([("log_source", ASCENDING)], name="log_source_asc")
        
        # Compound indexes for common query patterns
        logs_collection.create_index(
            [("timestamp", DESCENDING), ("severity", ASCENDING)],
            name="timestamp_severity"
        )
        logs_collection.create_index(
            [("source_ip", ASCENDING), ("timestamp", DESCENDING)],
            name="source_ip_timestamp"
        )
        logs_collection.create_index(
            [("severity", ASCENDING), ("event_type", ASCENDING), ("timestamp", DESCENDING)],
            name="severity_event_timestamp"
        )
        logs_collection.create_index(
            [("destination_port", ASCENDING), ("timestamp", DESCENDING)],
            name="port_timestamp"
        )
        
        # Indexes for saved reports collection
        saved_reports_collection.create_index([("created_at", DESCENDING)], name="reports_created_at_desc")
        saved_reports_collection.create_index([("report_type", ASCENDING)], name="reports_type_asc")
        saved_reports_collection.create_index([("period.start", DESCENDING)], name="reports_period_start_desc")

        # Indexes for alerts collection (dashboard cache + first-class alerts)
        alerts_collection.create_index([("bucket_end", DESCENDING)], name="alerts_bucket_end_desc")
        alerts_collection.create_index([("lookback_seconds", ASCENDING)], name="alerts_lookback_asc")
        alerts_collection.create_index(
            [("bucket_end", DESCENDING), ("lookback_seconds", ASCENDING), ("severity", ASCENDING)],
            name="alerts_bucket_lookback_severity"
        )
        alerts_collection.create_index(
            [("bucket_end", DESCENDING), ("lookback_seconds", ASCENDING), ("alert_type", ASCENDING), ("source_ip", ASCENDING)],
            unique=True,
            name="alerts_bucket_type_ip_unique"
        )

        # --- ML collections ---
        ml_predictions_collection.create_index([("created_at", DESCENDING)], name="ml_pred_created_at_desc")
        ml_predictions_collection.create_index([("source_ip", ASCENDING), ("created_at", DESCENDING)], name="ml_pred_source_ip_created_at")
        ml_predictions_collection.create_index([("predicted_label", ASCENDING), ("created_at", DESCENDING)], name="ml_pred_label_created_at")
        ml_predictions_collection.create_index([("risk_score", DESCENDING), ("created_at", DESCENDING)], name="ml_pred_risk_created_at")

        ml_training_history_collection.create_index([("started_at", DESCENDING)], name="ml_train_started_at_desc")
        ml_training_history_collection.create_index([("status", ASCENDING), ("started_at", DESCENDING)], name="ml_train_status_started_at")

        # Feature cache: unique key + TTL on created_at
        ml_features_cache_collection.create_index([("cache_key", ASCENDING)], unique=True, name="ml_feat_cache_key_unique")
        ttl_hours = int(os.getenv("ML_FEATURE_CACHE_TTL_HOURS", "24"))
        ttl_seconds = max(60, ttl_hours * 3600)
        ml_features_cache_collection.create_index(
            [("created_at", ASCENDING)],
            expireAfterSeconds=ttl_seconds,
            name="ml_feat_cache_created_at_ttl",
        )
        
        print("Database indexes created successfully")
    except Exception as e:
        print(f"Error creating indexes (may already exist): {e}")


# Create indexes on module import
create_indexes()

