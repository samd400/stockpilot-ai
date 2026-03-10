import uuid
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user, require_billing_role
from app.models.expense import Expense

router = APIRouter(prefix="/expenses", tags=["Expenses"])

CATEGORIES = ["rent", "salary", "utilities", "supplies", "marketing", "transport", "other"]


@router.post("/", status_code=201)
def create_expense(payload: Dict[str, Any], db: Session = Depends(get_db),
                   user: Dict = Depends(require_billing_role)):
    if payload.get("category") and payload["category"] not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Category must be one of {CATEGORIES}")
    expense = Expense(
        id=uuid.uuid4(), tenant_id=user["tenant_id"], user_id=user["user_id"],
        category=payload.get("category", "other"),
        amount=payload["amount"], currency=payload.get("currency", "INR"),
        description=payload.get("description"),
        expense_date=datetime.fromisoformat(payload["expense_date"]) if payload.get("expense_date") else datetime.utcnow(),
        receipt_url=payload.get("receipt_url"),
        reference_number=payload.get("reference_number"),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return {"id": str(expense.id), "category": expense.category, "amount": expense.amount,
            "currency": expense.currency, "description": expense.description,
            "expense_date": expense.expense_date.isoformat()}


@router.get("/")
def list_expenses(category: Optional[str] = None, skip: int = 0, limit: int = 50,
                  db: Session = Depends(get_db), user: Dict = Depends(get_current_user)):
    q = db.query(Expense).filter(Expense.tenant_id == user["tenant_id"])
    if category:
        q = q.filter(Expense.category == category)
    expenses = q.order_by(Expense.expense_date.desc()).offset(skip).limit(limit).all()
    return [{"id": str(e.id), "category": e.category, "amount": e.amount,
             "currency": e.currency, "description": e.description,
             "expense_date": e.expense_date.isoformat()} for e in expenses]


@router.delete("/{expense_id}", status_code=200)
def delete_expense(expense_id: str, db: Session = Depends(get_db),
                   user: Dict = Depends(require_billing_role)):
    expense = db.query(Expense).filter(Expense.id == expense_id,
                                        Expense.tenant_id == user["tenant_id"]).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return {"message": "Deleted"}
