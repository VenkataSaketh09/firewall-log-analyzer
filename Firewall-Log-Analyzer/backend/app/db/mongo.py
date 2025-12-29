import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client.firewall_analyzer
logs_collection = db.firewall_logs
ip_reputation_cache = db.ip_reputation_cache
saved_reports_collection = db.saved_reports


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
        
        print("Database indexes created successfully")
    except Exception as e:
        print(f"Error creating indexes (may already exist): {e}")


# Create indexes on module import
create_indexes()

