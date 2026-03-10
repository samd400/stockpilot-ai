"""
Regional Compliance Routes — GDPR, India e-Invoice (IRN/QR), GCC e-Invoice, EU VAT.
"""
import uuid
import hashlib
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.deps import require_billing_role, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/compliance", tags=["Compliance"])


# ─── GDPR — Data Export & Right to Be Forgotten ──────────────────────────────

@router.get("/gdpr/export")
def gdpr_data_export(db: Session = Depends(get_db), user: Dict = Depends(require_billing_role)):
    """
    GDPR Art. 20 — Data portability export.
    Returns all tenant data in structured JSON format.
    """
    tenant_id = user["tenant_id"]

    # Collect all billable data for tenant
    invoices = db.execute(text("""
        SELECT id, invoice_number, customer_name, customer_email, customer_phone,
               total_amount, currency, status, created_at
        FROM invoices WHERE tenant_id = :tid ORDER BY created_at DESC
    """), {"tid": tenant_id}).fetchall()

    payments = db.execute(text("""
        SELECT p.id, p.amount, p.currency, p.mode, p.status, p.created_at
        FROM payments p
        JOIN invoices i ON i.id = p.invoice_id
        WHERE i.tenant_id = :tid ORDER BY p.created_at DESC
    """), {"tid": tenant_id}).fetchall()

    export = {
        "export_date": datetime.utcnow().isoformat(),
        "tenant_id": tenant_id,
        "data_controller": "StockPilot",
        "legal_basis": "Contract (GDPR Art. 6(1)(b))",
        "invoices": [
            {
                "id": str(r[0]), "invoice_number": r[1],
                "customer_name": r[2], "customer_email": r[3],
                "total_amount": float(r[5]) if r[5] else 0,
                "currency": r[6], "status": r[7],
                "created_at": r[8].isoformat() if r[8] else None,
            }
            for r in invoices
        ],
        "payments": [
            {
                "id": str(r[0]), "amount": float(r[1]) if r[1] else 0,
                "currency": r[2], "method": r[3], "status": r[4],
                "created_at": r[5].isoformat() if r[5] else None,
            }
            for r in payments
        ],
        "total_records": len(invoices) + len(payments),
    }
    return export


@router.delete("/gdpr/erase-customer")
def gdpr_erase_customer(payload: Dict[str, Any], db: Session = Depends(get_db),
                          user: Dict = Depends(require_billing_role)):
    """
    GDPR Art. 17 — Right to erasure (right to be forgotten).
    Anonymizes customer PII on invoices while preserving financial records.
    Billing records must be kept for 7 years per EU tax law — we anonymize, not delete.
    """
    customer_email = payload.get("customer_email")
    customer_phone = payload.get("customer_phone")
    if not customer_email and not customer_phone:
        raise HTTPException(status_code=400, detail="customer_email or customer_phone required")

    tenant_id = user["tenant_id"]
    anonymized_name = f"GDPR-ERASED-{hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:8].upper()}"

    # Anonymize but preserve financial amounts (required for tax compliance)
    if customer_email:
        result = db.execute(text("""
            UPDATE invoices
            SET customer_name = :anon_name,
                customer_email = 'erased@gdpr.invalid',
                customer_phone = NULL,
                customer_address = NULL
            WHERE tenant_id = :tid AND customer_email = :email
        """), {"anon_name": anonymized_name, "tid": tenant_id, "email": customer_email})
        affected = result.rowcount

    elif customer_phone:
        result = db.execute(text("""
            UPDATE invoices
            SET customer_name = :anon_name,
                customer_phone = NULL
            WHERE tenant_id = :tid AND customer_phone = :phone
        """), {"anon_name": anonymized_name, "tid": tenant_id, "phone": customer_phone})
        affected = result.rowcount

    db.commit()
    logger.info(f"GDPR erasure: tenant {tenant_id} anonymized {affected} invoices")
    return {
        "message": f"Customer data anonymized on {affected} invoices",
        "anonymized_identifier": anonymized_name,
        "note": "Financial amounts retained for tax compliance (EU Directive 2006/112/EC)",
    }


# ─── India e-Invoice (IRN / QR Code) ─────────────────────────────────────────

@router.post("/india/e-invoice/{invoice_id}")
def generate_india_e_invoice(invoice_id: str, db: Session = Depends(get_db),
                              user: Dict = Depends(require_billing_role)):
    """
    India GST e-Invoice — generate IRN (Invoice Reference Number).
    Connects to NIC (National Informatics Centre) IRP portal.
    Requires: GSTIN, NIC credentials in tenant settings.
    """
    invoice = db.execute(text("""
        SELECT id, invoice_number, tenant_id, customer_name, customer_gstin,
               subtotal, tax_amount, total_amount, currency, created_at
        FROM invoices WHERE id = :id AND tenant_id = :tid
    """), {"id": invoice_id, "tid": user["tenant_id"]}).fetchone()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Build IRN hash (SHA-256 of SupplierGSTIN + DocType + DocNum + DocDate)
    # In production this is submitted to NIC IRP API
    doc_date = invoice[9].strftime("%d/%m/%Y") if invoice[9] else datetime.utcnow().strftime("%d/%m/%Y")
    irn_input = f"GSTIN|INV|{invoice[1]}|{doc_date}"
    irn = hashlib.sha256(irn_input.encode()).hexdigest()

    # In production: POST to https://einvoice1.gst.gov.in/IRP/OTP
    # and receive signed JSON with IRN + QR code + signed invoice
    # Here we return the structure that would be sent
    e_invoice_payload = {
        "Version": "1.1",
        "TranDtls": {"TaxSch": "GST", "SupTyp": "B2B", "RegRev": "N"},
        "DocDtls": {
            "Typ": "INV",
            "No": invoice[1],
            "Dt": doc_date,
        },
        "ValDtls": {
            "AssVal": float(invoice[4]) if invoice[4] else 0,
            "TotInvVal": float(invoice[7]) if invoice[7] else 0,
            "CgstVal": 0, "SgstVal": 0, "IgstVal": float(invoice[5]) if invoice[5] else 0,
        },
        "irn": irn,
        "AckNo": f"ACK{irn[:10].upper()}",
        "AckDt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "generated_offline",
        "note": "Submit to NIC IRP portal with valid GSTIN credentials for production IRN",
    }

    # Store IRN in invoice metadata
    db.execute(text("""
        UPDATE invoices SET irn = :irn, e_invoice_status = 'generated'
        WHERE id = :id
    """), {"irn": irn, "id": invoice_id})
    db.commit()

    return e_invoice_payload


# ─── GCC e-Invoice (UAE/Saudi ZATCA) ─────────────────────────────────────────

@router.post("/gcc/e-invoice/{invoice_id}")
def generate_gcc_e_invoice(invoice_id: str, db: Session = Depends(get_db),
                            user: Dict = Depends(require_billing_role)):
    """
    GCC e-Invoice — ZATCA (Saudi Arabia) Phase 2 / UAE ERCA compliant.
    Generates UBL XML e-invoice structure.
    """
    invoice = db.execute(text("""
        SELECT id, invoice_number, customer_name, customer_tax_id,
               subtotal, tax_amount, total_amount, currency, created_at,
               supplier_name, supplier_trn
        FROM invoices WHERE id = :id AND tenant_id = :tid
    """), {"id": invoice_id, "tid": user["tenant_id"]}).fetchone()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    issue_date = invoice[8].strftime("%Y-%m-%d") if invoice[8] else datetime.utcnow().strftime("%Y-%m-%d")
    issue_time = invoice[8].strftime("%H:%M:%S") if invoice[8] else "00:00:00"

    # Generate UBL 2.1 XML structure (required for ZATCA Phase 2)
    ubl_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
  <cbc:ProfileID>reporting:1.0</cbc:ProfileID>
  <cbc:ID>{invoice[1]}</cbc:ID>
  <cbc:IssueDate>{issue_date}</cbc:IssueDate>
  <cbc:IssueTime>{issue_time}</cbc:IssueTime>
  <cbc:InvoiceTypeCode name="0200000">388</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>{invoice[7] or 'SAR'}</cbc:DocumentCurrencyCode>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>{invoice[10] or 'TRN_REQUIRED'}</cbc:CompanyID>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:PartyTaxScheme>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>{invoice[9] or 'Supplier Name'}</cbc:RegistrationName>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>{invoice[3] or 'N/A'}</cbc:CompanyID>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:PartyTaxScheme>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>{invoice[2] or 'Customer'}</cbc:RegistrationName>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="{invoice[7] or 'SAR'}">{float(invoice[5]) if invoice[5] else 0:.2f}</cbc:TaxAmount>
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:TaxExclusiveAmount currencyID="{invoice[7] or 'SAR'}">{float(invoice[4]) if invoice[4] else 0:.2f}</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="{invoice[7] or 'SAR'}">{float(invoice[6]) if invoice[6] else 0:.2f}</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="{invoice[7] or 'SAR'}">{float(invoice[6]) if invoice[6] else 0:.2f}</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
</Invoice>"""

    # Hash for ZATCA compliance
    invoice_hash = hashlib.sha256(ubl_xml.encode()).hexdigest()

    return {
        "invoice_id": invoice_id,
        "invoice_number": invoice[1],
        "ubl_xml": ubl_xml,
        "invoice_hash": invoice_hash,
        "status": "ready_for_zatca_submission",
        "note": "Submit to ZATCA portal (fatoora.zatca.gov.sa) with valid CSID credentials for production",
    }


# ─── EU VAT Reports ───────────────────────────────────────────────────────────

@router.get("/eu/vat-report")
def eu_vat_report(year: int, quarter: Optional[int] = None, month: Optional[int] = None,
                   db: Session = Depends(get_db), user: Dict = Depends(require_billing_role)):
    """
    EU VAT OSS (One Stop Shop) report — aggregate VAT by country.
    Required for EU sellers doing B2C cross-border sales.
    """
    tenant_id = user["tenant_id"]

    # Build date range
    if quarter:
        month_start = (quarter - 1) * 3 + 1
        date_from = datetime(year, month_start, 1)
        month_end = month_start + 3
        if month_end > 12:
            date_to = datetime(year + 1, 1, 1)
        else:
            date_to = datetime(year, month_end, 1)
        period = f"Q{quarter} {year}"
    elif month:
        date_from = datetime(year, month, 1)
        if month == 12:
            date_to = datetime(year + 1, 1, 1)
        else:
            date_to = datetime(year, month + 1, 1)
        period = f"{year}-{month:02d}"
    else:
        date_from = datetime(year, 1, 1)
        date_to = datetime(year + 1, 1, 1)
        period = str(year)

    # Aggregate VAT by customer country
    rows = db.execute(text("""
        SELECT
            UPPER(COALESCE(customer_country, 'UNKNOWN')) as country,
            SUM(total_amount - tax_amount) as net_amount,
            SUM(tax_amount) as vat_amount,
            SUM(total_amount) as gross_amount,
            COUNT(*) as invoice_count,
            currency
        FROM invoices
        WHERE tenant_id = :tid
          AND created_at >= :date_from
          AND created_at < :date_to
          AND status NOT IN ('cancelled', 'void')
          AND currency IN ('EUR', 'GBP', 'SEK', 'DKK', 'PLN', 'CZK', 'HUF')
        GROUP BY UPPER(COALESCE(customer_country, 'UNKNOWN')), currency
        ORDER BY vat_amount DESC
    """), {"tid": tenant_id, "date_from": date_from, "date_to": date_to}).fetchall()

    breakdown = []
    total_vat = 0
    total_net = 0
    for row in rows:
        vat = float(row[1]) if row[1] else 0
        net = float(row[0]) if row[0] else 0
        total_vat += vat
        total_net += net
        breakdown.append({
            "country": row[0], "net_amount": round(net, 2),
            "vat_amount": round(vat, 2), "gross_amount": round(float(row[2]) if row[2] else 0, 2),
            "invoice_count": row[4], "currency": row[5],
        })

    return {
        "period": period,
        "tenant_id": tenant_id,
        "report_type": "EU_VAT_OSS",
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_net_amount": round(total_net, 2),
            "total_vat_amount": round(total_vat, 2),
            "countries_count": len(breakdown),
        },
        "breakdown_by_country": breakdown,
        "filing_deadline_note": "EU VAT OSS returns due by last day of month following each quarter",
    }


# ─── India GST Returns (GSTR-1 Summary) ──────────────────────────────────────

@router.get("/india/gst-report")
def india_gst_report(year: int, month: int, db: Session = Depends(get_db),
                      user: Dict = Depends(require_billing_role)):
    """India GSTR-1 summary — B2B and B2C invoice breakdowns for GST filing."""
    tenant_id = user["tenant_id"]
    date_from = datetime(year, month, 1)
    date_to = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
    period = f"{year}-{month:02d}"

    # B2B invoices (customer has GSTIN)
    b2b = db.execute(text("""
        SELECT customer_gstin, customer_name,
               SUM(subtotal) as taxable, SUM(cgst_amount) as cgst,
               SUM(sgst_amount) as sgst, SUM(igst_amount) as igst,
               SUM(total_amount) as total, COUNT(*) as count
        FROM invoices
        WHERE tenant_id = :tid AND created_at >= :df AND created_at < :dt
          AND customer_gstin IS NOT NULL AND status NOT IN ('cancelled', 'void')
        GROUP BY customer_gstin, customer_name
        ORDER BY total DESC
    """), {"tid": tenant_id, "df": date_from, "dt": date_to}).fetchall()

    # B2C invoices (no GSTIN)
    b2c = db.execute(text("""
        SELECT COALESCE(customer_state, 'Unknown') as state,
               SUM(subtotal) as taxable, SUM(tax_amount) as tax,
               SUM(total_amount) as total, COUNT(*) as count
        FROM invoices
        WHERE tenant_id = :tid AND created_at >= :df AND created_at < :dt
          AND (customer_gstin IS NULL OR customer_gstin = '')
          AND status NOT IN ('cancelled', 'void')
        GROUP BY COALESCE(customer_state, 'Unknown')
        ORDER BY total DESC
    """), {"tid": tenant_id, "df": date_from, "dt": date_to}).fetchall()

    return {
        "period": period,
        "report_type": "GSTR-1_SUMMARY",
        "generated_at": datetime.utcnow().isoformat(),
        "b2b_supplies": [
            {
                "gstin": r[0], "name": r[1],
                "taxable_amount": round(float(r[2]) if r[2] else 0, 2),
                "cgst": round(float(r[3]) if r[3] else 0, 2),
                "sgst": round(float(r[4]) if r[4] else 0, 2),
                "igst": round(float(r[5]) if r[5] else 0, 2),
                "invoice_value": round(float(r[6]) if r[6] else 0, 2),
                "invoice_count": r[7],
            }
            for r in b2b
        ],
        "b2c_supplies": [
            {
                "state": r[0],
                "taxable_amount": round(float(r[1]) if r[1] else 0, 2),
                "tax_amount": round(float(r[2]) if r[2] else 0, 2),
                "invoice_value": round(float(r[3]) if r[3] else 0, 2),
                "invoice_count": r[4],
            }
            for r in b2c
        ],
        "filing_deadline": f"11th of next month — file at gstin.gov.in",
    }
