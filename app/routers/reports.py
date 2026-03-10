"""Reports Router — tax summaries and accounting exports."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user import User
from app.services.tax_report_service import generate_tax_summary, export_csv, export_pdf

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/tax-summary")
def tax_summary(
    start_date: Optional[str] = Query(None, description="ISO date e.g. 2024-01-01"),
    end_date: Optional[str] = Query(None, description="ISO date e.g. 2024-12-31"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate tax summary report."""
    sd = datetime.fromisoformat(start_date) if start_date else None
    ed = datetime.fromisoformat(end_date) if end_date else None
    return generate_tax_summary(db, str(current_user.tenant_id), sd, ed)


@router.get("/tax-summary/csv")
def tax_summary_csv(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export tax summary as CSV."""
    sd = datetime.fromisoformat(start_date) if start_date else None
    ed = datetime.fromisoformat(end_date) if end_date else None
    summary = generate_tax_summary(db, str(current_user.tenant_id), sd, ed)
    csv_data = export_csv(summary)
    return PlainTextResponse(csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=tax_summary.csv"})


@router.get("/tax-summary/pdf")
def tax_summary_pdf(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export tax summary as PDF (text-based)."""
    sd = datetime.fromisoformat(start_date) if start_date else None
    ed = datetime.fromisoformat(end_date) if end_date else None
    summary = generate_tax_summary(db, str(current_user.tenant_id), sd, ed)
    pdf_data = export_pdf(summary)
    return Response(pdf_data, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=tax_summary.pdf"})
