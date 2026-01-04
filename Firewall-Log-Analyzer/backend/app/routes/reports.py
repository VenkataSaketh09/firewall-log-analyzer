from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Body
from fastapi.responses import Response
from bson import ObjectId
from app.db.mongo import saved_reports_collection
from app.services.report_service import generate_daily_report, generate_weekly_report, generate_custom_report
from app.services.export_service import export_to_json, export_to_csv, export_to_pdf_ready, export_to_pdf
from app.schemas.report_schema import (
    DailyReportResponse,
    WeeklyReportResponse,
    CustomReportResponse,
    ExportRequest,
    SecurityReport,
    SaveReportRequest,
    SaveReportResponse,
    SavedReport,
    SavedReportListItem,
    ReportHistoryResponse,
    ReportPeriod,
    ReportSummary,
    ThreatSummary
)

router = APIRouter(prefix="/api/reports", tags=["reports"])

def _apply_report_includes(
    report_data: dict,
    *,
    include_charts: bool = True,
    include_summary: bool = True,
    include_threats: bool = True,
    include_logs: bool = False,
) -> dict:
    # Mutate a shallow copy to avoid surprising callers.
    d = dict(report_data or {})
    if not include_summary:
        d.pop("summary", None)
        d.pop("recommendations", None)
    if not include_charts:
        d.pop("log_statistics", None)
        d.pop("time_breakdown", None)
    if not include_threats:
        d.pop("threat_detections", None)
        d.pop("top_threat_sources", None)
        d.pop("malicious_ip_analysis", None)
    if not include_logs:
        d.pop("detailed_logs", None)
    return d


@router.get("/daily", response_model=DailyReportResponse)
def get_daily_report(
    date: Optional[str] = Query(None, description="Date for the report (YYYY-MM-DD format, default: today)"),
    include_charts: bool = Query(True, description="Include charts/statistics sections"),
    include_summary: bool = Query(True, description="Include executive summary section"),
    include_threats: bool = Query(True, description="Include threats sections"),
    include_logs: bool = Query(False, description="Include detailed logs section (may be truncated)")
):
    """
    Generate a daily security report.
    
    Provides a comprehensive security overview for a specific day, including:
    - Log statistics and distributions
    - Threat detections (brute force and DDoS)
    - Top threat sources
    - Security score and status
    - Recommendations
    """
    try:
        report_date = None
        if date:
            try:
                report_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD format."
                )
        
        report_data = generate_daily_report(
            date=report_date,
            include_charts=include_charts,
            include_summary=include_summary,
            include_threats=include_threats,
            include_logs=include_logs,
        )
        
        # Convert to response model
        report = SecurityReport(**report_data)
        
        return DailyReportResponse(report=report)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating daily report: {str(e)}")


@router.get("/weekly", response_model=WeeklyReportResponse)
def get_weekly_report(
    start_date: Optional[str] = Query(None, description="Start date of the week (YYYY-MM-DD format, default: 7 days ago)"),
    include_charts: bool = Query(True, description="Include charts/statistics sections"),
    include_summary: bool = Query(True, description="Include executive summary section"),
    include_threats: bool = Query(True, description="Include threats sections"),
    include_logs: bool = Query(False, description="Include detailed logs section (may be truncated)")
):
    """
    Generate a weekly security report.
    
    Provides a comprehensive security overview for the past 7 days, including:
    - Aggregate log statistics
    - All threat detections in the period
    - Top threat sources
    - Security trends and patterns
    - Recommendations
    """
    try:
        week_start = None
        if start_date:
            try:
                week_start = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD format."
                )
        
        report_data = generate_weekly_report(
            start_date=week_start,
            include_charts=include_charts,
            include_summary=include_summary,
            include_threats=include_threats,
            include_logs=include_logs,
        )
        
        # Convert to response model
        report = SecurityReport(**report_data)
        
        return WeeklyReportResponse(report=report)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating weekly report: {str(e)}")


@router.get("/custom", response_model=CustomReportResponse)
def get_custom_report(
    start_date: str = Query(..., description="Start date for the report (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"),
    end_date: str = Query(..., description="End date for the report (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"),
    include_charts: bool = Query(True, description="Include charts/statistics sections"),
    include_summary: bool = Query(True, description="Include executive summary section"),
    include_threats: bool = Query(True, description="Include threats sections"),
    include_logs: bool = Query(False, description="Include detailed logs section (may be truncated)")
):
    """
    Generate a custom date range security report.
    
    Allows you to specify any date range for security analysis. Provides:
    - Comprehensive statistics for the specified period
    - All threats detected in the period
    - Trend analysis
    - Custom recommendations based on the period
    """
    try:
        # Try parsing as full ISO format first
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            # Try parsing as date only
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_date format. Use YYYY-MM-DD or ISO format."
                )
        
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                # Set to end of day
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid end_date format. Use YYYY-MM-DD or ISO format."
                )
        
        if start_dt >= end_dt:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before end_date"
            )
        
        report_data = generate_custom_report(
            start_date=start_dt,
            end_date=end_dt,
            include_charts=include_charts,
            include_summary=include_summary,
            include_threats=include_threats,
            include_logs=include_logs,
        )
        
        # Convert to response model
        report = SecurityReport(**report_data)
        
        return CustomReportResponse(report=report)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating custom report: {str(e)}")


@router.post("/export")
def export_report(
    export_request: ExportRequest = Body(..., description="Export configuration")
):
    """
    Export reports in various formats (JSON, CSV, PDF-ready).
    
    Supports exporting daily, weekly, or custom reports in the following formats:
    - JSON: Full structured JSON data
    - CSV: Tabular CSV format suitable for spreadsheet applications
    - PDF: Backend-generated PDF file download
    """
    try:
        # Determine include_* toggles (default to legacy behavior if omitted)
        include_charts = export_request.include_charts if export_request.include_charts is not None else True
        include_summary = export_request.include_summary if export_request.include_summary is not None else True
        include_threats = export_request.include_threats if export_request.include_threats is not None else True
        include_logs = export_request.include_logs if export_request.include_logs is not None else False

        # Generate report based on type
        report_data = None
        
        if export_request.report_type.upper() == "DAILY":
            report_date = None
            if export_request.date:
                try:
                    report_date = datetime.strptime(export_request.date, "%Y-%m-%d")
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid date format. Use YYYY-MM-DD format."
                    )
            report_data = generate_daily_report(
                date=report_date,
                include_charts=include_charts,
                include_summary=include_summary,
                include_threats=include_threats,
                include_logs=include_logs,
            )
        
        elif export_request.report_type.upper() == "WEEKLY":
            week_start = None
            if export_request.start_date:
                try:
                    week_start = datetime.strptime(export_request.start_date, "%Y-%m-%d")
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid start_date format. Use YYYY-MM-DD format."
                    )
            report_data = generate_weekly_report(
                start_date=week_start,
                include_charts=include_charts,
                include_summary=include_summary,
                include_threats=include_threats,
                include_logs=include_logs,
            )
        
        elif export_request.report_type.upper() == "CUSTOM":
            if not export_request.start_date or not export_request.end_date:
                raise HTTPException(
                    status_code=400,
                    detail="start_date and end_date are required for custom reports"
                )
            
            try:
                start_dt = datetime.fromisoformat(export_request.start_date.replace('Z', '+00:00'))
            except ValueError:
                try:
                    start_dt = datetime.strptime(export_request.start_date, "%Y-%m-%d")
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid start_date format. Use YYYY-MM-DD or ISO format."
                    )
            
            try:
                end_dt = datetime.fromisoformat(export_request.end_date.replace('Z', '+00:00'))
            except ValueError:
                try:
                    end_dt = datetime.strptime(export_request.end_date, "%Y-%m-%d")
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid end_date format. Use YYYY-MM-DD or ISO format."
                    )
            
            if start_dt >= end_dt:
                raise HTTPException(
                    status_code=400,
                    detail="start_date must be before end_date"
                )
            
            report_data = generate_custom_report(
                start_date=start_dt,
                end_date=end_dt,
                include_charts=include_charts,
                include_summary=include_summary,
                include_threats=include_threats,
                include_logs=include_logs,
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid report_type. Must be DAILY, WEEKLY, or CUSTOM"
            )
        
        # Apply include_* options before exporting
        report_data = _apply_report_includes(
            report_data,
            include_charts=include_charts,
            include_summary=include_summary,
            include_threats=include_threats,
            include_logs=include_logs,
        )

        # Export in requested format
        format_lower = export_request.format.lower()
        content = None
        content_type = None
        filename = None
        
        if format_lower == "json":
            content = export_to_json(report_data)
            content_type = "application/json"
            filename = f"security_report_{export_request.report_type.lower()}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        elif format_lower == "csv":
            content = export_to_csv(report_data)
            content_type = "text/csv"
            filename = f"security_report_{export_request.report_type.lower()}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        elif format_lower == "pdf":
            pdf_bytes = export_to_pdf(report_data)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": (
                        f"attachment; filename=security_report_{export_request.report_type.lower()}_"
                        f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
                    )
                }
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid format. Must be json, csv, or pdf"
            )
        
        # Return file as downloadable response
        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting report: {str(e)}")


@router.post("/save", response_model=SaveReportResponse)
def save_report(save_request: SaveReportRequest = Body(...)):
    """
    Save a generated report to the database for later retrieval.
    
    Allows users to save reports with optional name and notes for future reference.
    """
    try:
        report_doc = {
            "report_name": save_request.report_name,
            "report": save_request.report.dict(),
            "created_at": datetime.utcnow().isoformat(),
            "notes": save_request.notes
        }
        
        result = saved_reports_collection.insert_one(report_doc)
        
        return SaveReportResponse(
            id=str(result.inserted_id),
            message="Report saved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving report: {str(e)}")


@router.get("/history", response_model=ReportHistoryResponse)
def get_report_history(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of reports to return"),
    skip: int = Query(0, ge=0, description="Number of reports to skip for pagination"),
    report_type: Optional[str] = Query(None, description="Filter by report type (DAILY, WEEKLY, CUSTOM)")
):
    """
    Get a list of saved reports.
    
    Returns a paginated list of saved reports, optionally filtered by report type.
    """
    try:
        query = {}
        if report_type:
            query["report.report_type"] = report_type.upper()
        
        # Get total count
        total = saved_reports_collection.count_documents(query)
        
        # Get reports sorted by created_at descending
        cursor = saved_reports_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        
        reports = []
        for doc in cursor:
            try:
                report_data = doc.get("report", {})
                period_data = report_data.get("period", {})
                summary_data = report_data.get("summary", {})
                
                # Create SavedReportListItem using id field (which maps to _id via alias)
                report_item = SavedReportListItem(
                    id=str(doc["_id"]),
                    report_name=doc.get("report_name"),
                    report_type=report_data.get("report_type", ""),
                    report_date=report_data.get("report_date", ""),
                    period=ReportPeriod(**period_data) if period_data else ReportPeriod(start="", end=""),
                    summary=ReportSummary(**summary_data) if summary_data else ReportSummary(
                        total_logs=0,
                        security_score=0,
                        security_status="UNKNOWN",
                        threat_summary=ThreatSummary(
                            total_brute_force_attacks=0,
                            total_ddos_attacks=0,
                            total_port_scan_attacks=0,
                            total_threats=0,
                            critical_threats=0,
                            high_threats=0,
                            medium_threats=0,
                            low_threats=0
                        )
                    ),
                    created_at=doc.get("created_at", ""),
                    notes=doc.get("notes")
                )
                reports.append(report_item)
            except Exception as e:
                # Log error but continue processing other reports
                print(f"Error processing report {doc.get('_id')}: {str(e)}")
                continue
        
        return ReportHistoryResponse(
            reports=reports,
            total=total
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving report history: {str(e)}")


@router.get("/history/{report_id}", response_model=SavedReport)
def get_saved_report(report_id: str):
    """
    Get a specific saved report by ID.
    
    Returns the full report data including all details.
    """
    try:
        if not ObjectId.is_valid(report_id):
            raise HTTPException(status_code=400, detail="Invalid report ID format")
        
        doc = saved_reports_collection.find_one({"_id": ObjectId(report_id)})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return SavedReport(
            _id=str(doc["_id"]),
            report_name=doc.get("report_name"),
            report=SecurityReport(**doc["report"]),
            created_at=doc.get("created_at", ""),
            notes=doc.get("notes")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving report: {str(e)}")


@router.delete("/history/{report_id}")
def delete_saved_report(report_id: str):
    """
    Delete a saved report by ID.
    
    Permanently removes the report from the database.
    """
    try:
        if not ObjectId.is_valid(report_id):
            raise HTTPException(status_code=400, detail="Invalid report ID format")
        
        result = saved_reports_collection.delete_one({"_id": ObjectId(report_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {"message": "Report deleted successfully", "id": report_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting report: {str(e)}")

