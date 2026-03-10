from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user import User
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.product import Product
from app.models.customer import Customer
from app.models.payment import Payment, PaymentStatus, PaymentMode
from datetime import datetime
from typing import List, Optional
import uuid

router = APIRouter(prefix="/pos", tags=["POS Billing"])


class POSLineItem:
    def __init__(self, product_id: str, quantity: int, price: float):
        self.product_id = product_id
        self.quantity = quantity
        self.price = price


@router.post("/bill")
def create_pos_bill(
    customer_id: Optional[str] = None,
    items: List[dict] = None,
    payment_mode: str = "CASH",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a POS bill with immediate payment"""
    
    if not items or len(items) == 0:
        raise HTTPException(status_code=400, detail="Bill must have at least one item")
    
    # Get or create customer
    if not customer_id:
        # Create walk-in customer
        customer = Customer(
            user_id=str(current_user.id),
            name="Walk-in Customer",
            phone_number=None
        )
        db.add(customer)
        db.commit()
        customer_id = customer.id
    else:
        customer = db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.user_id == str(current_user.id)
        ).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
    
    # Generate invoice number
    invoice_number = f"{current_user.invoice_prefix}-{current_user.invoice_counter}"
    current_user.invoice_counter += 1
    
    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_number,
        user_id=current_user.id,
        customer_id=customer_id,
        invoice_type="SALES"
    )
    
    db.add(invoice)
    db.flush()
    
    # Add items
    subtotal = 0
    for item in items:
        product = db.query(Product).filter(
            Product.id == item["product_id"],
            Product.user_id == current_user.id
        ).first()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item['product_id']} not found")
        
        quantity = item["quantity"]
        price = item.get("price", product.selling_price)
        
        # Check stock
        if product.stock_quantity < quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.product_name}")
        
        # Create invoice item
        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=price,
            gst_percentage=product.gst_percentage
        )
        
        db.add(invoice_item)
        
        # Update product stock
        product.stock_quantity -= quantity
        
        # Calculate item total
        item_total = quantity * price
        gst_amount = item_total * (product.gst_percentage / 100)
        subtotal += item_total + gst_amount
    
    # Calculate totals
    gst_amount = subtotal * 0.18  # Simplified GST calculation
    total_amount = subtotal + gst_amount
    
    invoice.subtotal = subtotal
    invoice.gst_amount = gst_amount
    invoice.total_amount = total_amount
    invoice.payment_status = "PAID"
    invoice.amount_paid = total_amount
    invoice.amount_due = 0
    
    db.commit()
    db.refresh(invoice)
    
    # Create payment record
    payment = Payment(
        invoice_id=invoice.id,
        user_id=current_user.id,
        amount=total_amount,
        status=PaymentStatus.PAID,
        mode=PaymentMode[payment_mode] if payment_mode in PaymentMode.__members__ else PaymentMode.CASH,
        transaction_id=str(uuid.uuid4())
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    return {
        "invoice_id": str(invoice.id),
        "invoice_number": invoice_number,
        "customer_id": customer_id,
        "subtotal": subtotal,
        "gst_amount": gst_amount,
        "total_amount": total_amount,
        "payment_mode": payment_mode,
        "payment_status": "PAID",
        "created_at": invoice.created_at
    }


@router.get("/bills")
def get_pos_bills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """Get recent POS bills"""
    
    bills = db.query(Invoice).filter(
        Invoice.user_id == current_user.id,
        Invoice.invoice_type == "SALES"
    ).order_by(Invoice.created_at.desc()).limit(limit).all()
    
    return [
        {
            "invoice_id": str(bill.id),
            "invoice_number": bill.invoice_number,
            "customer_id": bill.customer_id,
            "total_amount": bill.total_amount,
            "payment_status": bill.payment_status,
            "created_at": bill.created_at
        }
        for bill in bills
    ]


@router.get("/bills/{invoice_id}")
def get_pos_bill_details(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get POS bill details"""
    
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    items = db.query(InvoiceItem).filter(
        InvoiceItem.invoice_id == invoice_id
    ).all()
    
    return {
        "invoice_id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "customer_id": invoice.customer_id,
        "subtotal": invoice.subtotal,
        "gst_amount": invoice.gst_amount,
        "total_amount": invoice.total_amount,
        "payment_status": invoice.payment_status,
        "items": [
            {
                "product_id": str(item.product_id),
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "gst_percentage": item.gst_percentage
            }
            for item in items
        ],
        "created_at": invoice.created_at
    }


@router.post("/bills/{invoice_id}/return")
def create_return_bill(
    invoice_id: str,
    items: List[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a return/credit note for a POS bill"""
    
    original_invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()
    
    if not original_invoice:
        raise HTTPException(status_code=404, detail="Original bill not found")
    
    # Generate return invoice number
    return_invoice_number = f"{current_user.invoice_prefix}-RET-{current_user.invoice_counter}"
    current_user.invoice_counter += 1
    
    # Create return invoice
    return_invoice = Invoice(
        invoice_number=return_invoice_number,
        user_id=current_user.id,
        customer_id=original_invoice.customer_id,
        invoice_type="CREDIT_NOTE"
    )
    
    db.add(return_invoice)
    db.flush()
    
    # Add return items
    return_total = 0
    for item in items:
        original_item = db.query(InvoiceItem).filter(
            InvoiceItem.invoice_id == invoice_id,
            InvoiceItem.product_id == item["product_id"]
        ).first()
        
        if not original_item:
            raise HTTPException(status_code=404, detail="Item not found in original bill")
        
        quantity = item["quantity"]
        
        # Create return invoice item
        return_item = InvoiceItem(
            invoice_id=return_invoice.id,
            product_id=original_item.product_id,
            quantity=quantity,
            unit_price=original_item.unit_price,
            gst_percentage=original_item.gst_percentage
        )
        
        db.add(return_item)
        
        # Restore product stock
        product = db.query(Product).filter(
            Product.id == original_item.product_id
        ).first()
        product.stock_quantity += quantity
        
        # Calculate return total
        item_total = quantity * original_item.unit_price
        gst_amount = item_total * (original_item.gst_percentage / 100)
        return_total += item_total + gst_amount
    
    # Calculate return totals
    return_gst = return_total * 0.18
    return_amount = return_total + return_gst
    
    return_invoice.subtotal = return_total
    return_invoice.gst_amount = return_gst
    return_invoice.total_amount = return_amount
    return_invoice.payment_status = "REFUNDED"
    return_invoice.amount_paid = return_amount
    
    db.commit()
    db.refresh(return_invoice)
    
    return {
        "return_invoice_id": str(return_invoice.id),
        "return_invoice_number": return_invoice_number,
        "original_invoice_number": original_invoice.invoice_number,
        "return_amount": return_amount,
        "created_at": return_invoice.created_at
    }
