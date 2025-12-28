from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Body
from fastapi.responses import Response
from app.services.report_service import generate_daily_report, generate_weekly_report, generate_custom_report
from app.services.export_service import export_to_json, export_to_csv, export_to_pdf_ready, export_to_pdf
from app.schemas.report_schema import (
    DailyReportResponse,
    WeeklyReportResponse,
    CustomReportResponse,
    ExportRequest,
    SecurityReport
)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/daily", response_model=DailyReportResponse)
def get_daily_report(
    date: Optional[str] = Query(None, description="Date for the report (YYYY-MM-DD format, default: today)")
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
        
        report_data = generate_daily_report(date=report_date)
        
        # Convert to response model
        report = SecurityReport(**report_data)
        
        return DailyReportResponse(report=report)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating daily report: {str(e)}")


@router.get("/weekly", response_model=WeeklyReportResponse)
def get_weekly_report(
    start_date: Optional[str] = Query(None, description="Start date of the week (YYYY-MM-DD format, default: 7 days ago)")
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
        
        report_data = generate_weekly_report(start_date=week_start)
        
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
    end_date: str = Query(..., description="End date for the report (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
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
        
        report_data = generate_custom_report(start_date=start_dt, end_date=end_dt)
        
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
            report_data = generate_daily_report(date=report_date)
        
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
            report_data = generate_weekly_report(start_date=week_start)
        
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
            
            report_data = generate_custom_report(start_date=start_dt, end_date=end_dt)
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid report_type. Must be DAILY, WEEKLY, or CUSTOM"
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

