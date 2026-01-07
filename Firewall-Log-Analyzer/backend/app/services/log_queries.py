from datetime import datetime, timedelta
from typing import Optional
from pymongo import DESCENDING, ASCENDING
from app.db.mongo import logs_collection


def build_log_query(
    source_ip: Optional[str] = None,
    severity: Optional[str] = None,
    event_type: Optional[str] = None,
    destination_port: Optional[int] = None,
    protocol: Optional[str] = None,
    log_source: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None
):
    """Build MongoDB query from filter parameters"""
    query = {}
    
    if source_ip:
        query["source_ip"] = source_ip
    
    if severity:
        query["severity"] = severity
    
    if event_type:
        query["event_type"] = event_type
    
    if destination_port is not None:
        # Ensure destination_port is an integer for exact match
        # MongoDB is type-sensitive, so we match both int and string representations
        try:
            port_int = int(destination_port)
            query["destination_port"] = port_int
        except (ValueError, TypeError):
            # If conversion fails, skip this filter
            pass
    
    if protocol:
        query["protocol"] = protocol
    
    if log_source:
        query["log_source"] = log_source
    
    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            query["timestamp"]["$gte"] = start_date
        if end_date:
            query["timestamp"]["$lte"] = end_date
    
    if search:
        query["$or"] = [
            {"source_ip": {"$regex": search, "$options": "i"}},
            {"raw_log": {"$regex": search, "$options": "i"}},
            {"username": {"$regex": search, "$options": "i"}}
        ]
    
    return query


def get_logs(
    page: int = 1,
    page_size: int = 50,
    source_ip: Optional[str] = None,
    severity: Optional[str] = None,
    event_type: Optional[str] = None,
    destination_port: Optional[int] = None,
    protocol: Optional[str] = None,
    log_source: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc"
):
    """Retrieve logs with filtering, pagination, and sorting"""
    query = build_log_query(
        source_ip=source_ip,
        severity=severity,
        event_type=event_type,
        destination_port=destination_port,
        protocol=protocol,
        log_source=log_source,
        start_date=start_date,
        end_date=end_date,
        search=search
    )
    
    # Calculate skip for pagination
    skip = (page - 1) * page_size
    
    # Get total count
    total = logs_collection.count_documents(query)
    
    # Special handling for severity sorting (custom order: CRITICAL > HIGH > MEDIUM > LOW)
    if sort_by == "severity":
        # Severity order mapping: CRITICAL=0, HIGH=1, MEDIUM=2, LOW=3
        sort_direction = -1 if sort_order.lower() == "desc" else 1
        
        # Use aggregation pipeline for custom severity sorting
        pipeline = [
            {"$match": query},
            {
                "$addFields": {
                    "severity_order": {
                        "$switch": {
                            "branches": [
                                {"case": {"$eq": ["$severity", "CRITICAL"]}, "then": 0},
                                {"case": {"$eq": ["$severity", "HIGH"]}, "then": 1},
                                {"case": {"$eq": ["$severity", "MEDIUM"]}, "then": 2},
                                {"case": {"$eq": ["$severity", "LOW"]}, "then": 3}
                            ],
                            "default": 99  # Unknown severity values go to end
                        }
                    }
                }
            },
            {"$sort": {"severity_order": sort_direction}},
            {"$skip": skip},
            {"$limit": page_size},
            {"$project": {"severity_order": 0}}  # Remove temporary field
        ]
        
        logs = list(logs_collection.aggregate(pipeline))
    else:
        # Standard sorting for other fields
        sort_direction = DESCENDING if sort_order.lower() == "desc" else ASCENDING
        sort_fields = {
            "timestamp": ("timestamp", sort_direction),
            "source_ip": ("source_ip", sort_direction),
            "event_type": ("event_type", sort_direction),
            "destination_port": ("destination_port", sort_direction),
            "protocol": ("protocol", sort_direction),
        }
        sort_criteria = [sort_fields.get(sort_by, ("timestamp", DESCENDING))]
        
        # Get paginated logs
        cursor = logs_collection.find(query).sort(sort_criteria).skip(skip).limit(page_size)
        logs = list(cursor)
    
    # Convert ObjectId to string for JSON serialization
    for log in logs:
        log["_id"] = str(log["_id"])
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "logs": logs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


def get_log_by_id(log_id: str):
    """Get a single log entry by ID"""
    from bson import ObjectId
    try:
        log = logs_collection.find_one({"_id": ObjectId(log_id)})
        if log:
            log["_id"] = str(log["_id"])
        return log
    except Exception:
        return None


def get_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get aggregated statistics"""
    query = {}
    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            query["timestamp"]["$gte"] = start_date
        if end_date:
            query["timestamp"]["$lte"] = end_date
    
    # Total logs
    total_logs = logs_collection.count_documents(query)
    
    # Severity counts - filter out None values
    severity_pipeline = [
        {"$match": {**query, "severity": {"$ne": None}}},
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
    ]
    severity_counts = {
        str(item["_id"]): item["count"]
        for item in logs_collection.aggregate(severity_pipeline)
        if item["_id"] is not None
    }
    
    # Event type counts - filter out None values
    event_type_pipeline = [
        {"$match": {**query, "event_type": {"$ne": None}}},
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}}
    ]
    event_type_counts = {
        str(item["_id"]): item["count"]
        for item in logs_collection.aggregate(event_type_pipeline)
        if item["_id"] is not None
    }
    
    # Protocol counts - filter out None values
    protocol_pipeline = [
        {"$match": {**query, "protocol": {"$ne": None}}},
        {"$group": {"_id": "$protocol", "count": {"$sum": 1}}}
    ]
    protocol_counts = {
        str(item["_id"]): item["count"]
        for item in logs_collection.aggregate(protocol_pipeline)
        if item["_id"] is not None
    }
    
    # Logs by hour - if no date range, show last 7 days or all available data
    hour_start_date = start_date
    hour_end_date = end_date
    
    if not hour_start_date and not hour_end_date:
        # Try to get last 7 days first
        hour_end_date = datetime.utcnow()
        hour_start_date = hour_end_date - timedelta(days=7)
        
        # Check if we have any logs in last 7 days
        test_query = {
            "timestamp": {
                "$gte": hour_start_date,
                "$lte": hour_end_date
            }
        }
        has_recent_logs = logs_collection.count_documents(test_query) > 0
        
        # If no recent logs, expand to last 30 days, then all-time
        if not has_recent_logs:
            hour_start_date = hour_end_date - timedelta(days=30)
            test_query = {
                "timestamp": {
                    "$gte": hour_start_date,
                    "$lte": hour_end_date
                }
            }
            has_recent_logs = logs_collection.count_documents(test_query) > 0
            if not has_recent_logs:
                # Show all available data - no date filter
                hour_start_date = None
                hour_end_date = None
    
    # Use $dateToString for compatibility with all MongoDB versions
    hour_query = {**query}
    if hour_start_date or hour_end_date:
        hour_query["timestamp"] = {}
        if hour_start_date:
            hour_query["timestamp"]["$gte"] = hour_start_date
        if hour_end_date:
            hour_query["timestamp"]["$lte"] = hour_end_date
    
    hour_pipeline = [
        {"$match": hour_query},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%dT%H:00:00",
                        "date": "$timestamp"
                    }
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}},
        {"$project": {"hour": "$_id", "count": 1, "_id": 0}}
    ]
    logs_by_hour = list(logs_collection.aggregate(hour_pipeline))
    
    # Top source IPs with severity breakdown - filter out None source_ip
    top_ips_pipeline = [
        {"$match": {**query, "source_ip": {"$ne": None}}},
        {"$group": {
            "_id": "$source_ip",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": DESCENDING}},
        {"$limit": 10},
        {"$project": {
            "source_ip": "$_id",
            "count": 1,
            "_id": 0
        }}
    ]
    top_source_ips = list(logs_collection.aggregate(top_ips_pipeline))
    
    # Add severity breakdown for each IP
    for ip_item in top_source_ips:
        ip = ip_item["source_ip"]
        ip_query = {**query, "source_ip": ip}
        severity_breakdown = {}
        for severity in ["HIGH", "MEDIUM", "LOW"]:
            count = logs_collection.count_documents({**ip_query, "severity": severity})
            if count > 0:
                severity_breakdown[severity] = count
        ip_item["severity_breakdown"] = severity_breakdown
    
    # Top ports
    top_ports_pipeline = [
        {"$match": {**query, "destination_port": {"$ne": None}}},
        {"$group": {
            "_id": "$destination_port",
            "count": {"$sum": 1},
            "protocols": {"$addToSet": "$protocol"}
        }},
        {"$sort": {"count": DESCENDING}},
        {"$limit": 10},
        {"$project": {
            "port": "$_id",
            "count": 1,
            "protocol": {"$arrayElemAt": ["$protocols", 0]},
            "_id": 0
        }}
    ]
    top_ports = list(logs_collection.aggregate(top_ports_pipeline))
    
    return {
        "total_logs": total_logs,
        "severity_counts": severity_counts,
        "event_type_counts": event_type_counts,
        "protocol_counts": protocol_counts,
        "logs_by_hour": logs_by_hour,
        "top_source_ips": top_source_ips,
        "top_ports": top_ports
    }


def get_top_ips(limit: int = 10, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
    """Get top source IPs by log count"""
    query = {"source_ip": {"$ne": None}}
    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            query["timestamp"]["$gte"] = start_date
        if end_date:
            query["timestamp"]["$lte"] = end_date
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$source_ip",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": DESCENDING}},
        {"$limit": limit},
        {"$project": {
            "source_ip": "$_id",
            "count": 1,
            "_id": 0
        }}
    ]
    
    results = list(logs_collection.aggregate(pipeline))
    
    # Add severity breakdown
    for item in results:
        ip = item["source_ip"]
        ip_query = {**query, "source_ip": ip}
        severity_breakdown = {}
        for severity in ["HIGH", "MEDIUM", "LOW"]:
            count = logs_collection.count_documents({**ip_query, "severity": severity})
            if count > 0:
                severity_breakdown[severity] = count
        item["severity_breakdown"] = severity_breakdown
    
    return results


def get_top_ports(limit: int = 10, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
    """Get top destination ports by log count"""
    query = {"destination_port": {"$ne": None}}
    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            query["timestamp"]["$gte"] = start_date
        if end_date:
            query["timestamp"]["$lte"] = end_date
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$destination_port",
            "count": {"$sum": 1},
            "protocols": {"$addToSet": "$protocol"}
        }},
        {"$sort": {"count": DESCENDING}},
        {"$limit": limit},
        {"$project": {
            "port": "$_id",
            "count": 1,
            "protocol": {"$arrayElemAt": ["$protocols", 0]},
            "_id": 0
        }}
    ]
    
    return list(logs_collection.aggregate(pipeline))

