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
    
    if destination_port:
        query["destination_port"] = destination_port
    
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
    
    # Build sort criteria
    sort_direction = DESCENDING if sort_order.lower() == "desc" else ASCENDING
    sort_fields = {
        "timestamp": ("timestamp", sort_direction),
        "severity": ("severity", ASCENDING),
        "source_ip": ("source_ip", ASCENDING),
        "event_type": ("event_type", ASCENDING),
    }
    sort_criteria = [sort_fields.get(sort_by, ("timestamp", DESCENDING))]
    
    # Calculate skip for pagination
    skip = (page - 1) * page_size
    
    # Get total count
    total = logs_collection.count_documents(query)
    
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
    
    # Severity counts
    severity_pipeline = [
        {"$match": query},
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
    ]
    severity_counts = {
        item["_id"]: item["count"]
        for item in logs_collection.aggregate(severity_pipeline)
    }
    
    # Event type counts
    event_type_pipeline = [
        {"$match": query},
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}}
    ]
    event_type_counts = {
        item["_id"]: item["count"]
        for item in logs_collection.aggregate(event_type_pipeline)
    }
    
    # Protocol counts
    protocol_pipeline = [
        {"$match": {**query, "protocol": {"$ne": None}}},
        {"$group": {"_id": "$protocol", "count": {"$sum": 1}}}
    ]
    protocol_counts = {
        item["_id"]: item["count"]
        for item in logs_collection.aggregate(protocol_pipeline)
    }
    
    # Logs by hour (last 24 hours if no date range specified)
    if not start_date and not end_date:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=24)
    
    # Use $dateToString for compatibility with all MongoDB versions
    hour_query = {**query}
    if start_date or end_date:
        hour_query["timestamp"] = {}
        if start_date:
            hour_query["timestamp"]["$gte"] = start_date
        if end_date:
            hour_query["timestamp"]["$lte"] = end_date
    
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
    
    # Top source IPs with severity breakdown
    top_ips_pipeline = [
        {"$match": query},
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
    query = {}
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

