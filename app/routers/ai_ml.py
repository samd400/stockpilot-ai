from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.invoice_item import InvoiceItem
from app.models.invoice import Invoice
from app.models.demand_forecast import DemandForecast
from app.models.dynamic_price import DynamicPrice
from app.models.inventory_health import InventoryHealth, InventoryHealthStatus
from app.schemas.demand_forecast import DemandForecastResponse
from app.schemas.dynamic_price import DynamicPriceResponse
from app.schemas.inventory_health import InventoryHealthResponse
from typing import List
import statistics

router = APIRouter(prefix="/ai", tags=["AI/ML Features"])


@router.post("/forecast/{product_id}")
def generate_demand_forecast(
    product_id: str,
    days_ahead: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate demand forecast for a product using ML"""
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get historical sales data (last 90 days)
    ninety_days_ago = datetime.utcnow() - timedelta(days=90)
    
    historical_sales = db.query(
        func.sum(InvoiceItem.quantity).label("total_quantity")
    ).join(
        Invoice, Invoice.id == InvoiceItem.invoice_id
    ).filter(
        InvoiceItem.product_id == product_id,
        Invoice.created_at >= ninety_days_ago
    ).scalar() or 0
    
    # Calculate average daily sales
    avg_daily_sales = historical_sales / 90 if historical_sales > 0 else 0
    
    # Simple ML: Use exponential smoothing with trend
    daily_sales = db.query(
        func.date(Invoice.created_at).label("date"),
        func.sum(InvoiceItem.quantity).label("quantity")
    ).join(
        InvoiceItem, Invoice.id == InvoiceItem.invoice_id
    ).filter(
        InvoiceItem.product_id == product_id,
        Invoice.created_at >= ninety_days_ago
    ).group_by(
        func.date(Invoice.created_at)
    ).order_by(
        func.date(Invoice.created_at)
    ).all()
    
    # Calculate trend
    if len(daily_sales) > 1:
        quantities = [int(row.quantity) for row in daily_sales]
        trend = "UP" if statistics.mean(quantities[-30:]) > statistics.mean(quantities[:30]) else "DOWN"
    else:
        trend = "STABLE"
    
    # Predict future demand
    predicted_quantity = int(avg_daily_sales * days_ahead * 1.1)  # 10% buffer
    confidence_level = min(100, (len(daily_sales) / 90) * 100)
    
    # Recommended stock
    recommended_stock = int(predicted_quantity * 1.2)  # 20% safety stock
    
    # Reorder urgency
    if product.stock_quantity < recommended_stock * 0.3:
        reorder_urgency = "URGENT"
    elif product.stock_quantity < recommended_stock * 0.6:
        reorder_urgency = "HIGH"
    elif product.stock_quantity < recommended_stock:
        reorder_urgency = "NORMAL"
    else:
        reorder_urgency = "LOW"
    
    # Save forecast
    forecast = DemandForecast(
        user_id=current_user.id,
        product_id=product_id,
        forecast_date=datetime.utcnow() + timedelta(days=days_ahead),
        predicted_quantity=predicted_quantity,
        confidence_level=confidence_level,
        historical_avg_sales=avg_daily_sales,
        trend=trend,
        seasonality_factor=1.0,
        recommended_stock=recommended_stock,
        reorder_urgency=reorder_urgency
    )
    
    db.add(forecast)
    db.commit()
    db.refresh(forecast)
    
    return forecast


@router.get("/forecast/{product_id}", response_model=List[DemandForecastResponse])
def get_demand_forecasts(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get demand forecasts for a product"""
    
    forecasts = db.query(DemandForecast).filter(
        DemandForecast.product_id == product_id,
        DemandForecast.user_id == current_user.id
    ).order_by(DemandForecast.forecast_date.desc()).limit(10).all()
    
    return forecasts


@router.post("/dynamic-price/{product_id}")
def calculate_dynamic_price(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate dynamic price for a product based on demand and inventory"""
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get recent sales velocity
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_sales = db.query(func.sum(InvoiceItem.quantity)).join(
        Invoice, Invoice.id == InvoiceItem.invoice_id
    ).filter(
        InvoiceItem.product_id == product_id,
        Invoice.created_at >= seven_days_ago
    ).scalar() or 0
    
    # Demand multiplier (high sales = higher price)
    demand_multiplier = 1.0 + (recent_sales / 100) * 0.2  # Max 20% increase
    demand_multiplier = min(demand_multiplier, 1.3)  # Cap at 30%
    
    # Stock multiplier (low stock = higher price)
    stock_ratio = product.stock_quantity / max(product.stock_quantity + 100, 1)
    stock_multiplier = 1.0 + (1 - stock_ratio) * 0.15  # Max 15% increase
    
    # Calculate final price
    base_price = product.selling_price
    current_price = base_price * demand_multiplier * stock_multiplier
    
    # Set min/max bounds
    min_price = base_price * 0.8  # 20% discount floor
    max_price = base_price * 1.5  # 50% premium ceiling
    
    current_price = max(min_price, min(current_price, max_price))
    
    # Save dynamic price
    dynamic_price = db.query(DynamicPrice).filter(
        DynamicPrice.product_id == product_id,
        DynamicPrice.user_id == current_user.id
    ).first()
    
    if dynamic_price:
        dynamic_price.current_price = current_price
        dynamic_price.demand_multiplier = demand_multiplier
        dynamic_price.stock_multiplier = stock_multiplier
        dynamic_price.last_updated = datetime.utcnow()
    else:
        dynamic_price = DynamicPrice(
            user_id=current_user.id,
            product_id=product_id,
            base_price=base_price,
            current_price=current_price,
            demand_multiplier=demand_multiplier,
            stock_multiplier=stock_multiplier,
            min_price=min_price,
            max_price=max_price
        )
        db.add(dynamic_price)
    
    db.commit()
    db.refresh(dynamic_price)
    
    return {
        "product_id": product_id,
        "base_price": base_price,
        "current_price": current_price,
        "price_change_percentage": ((current_price - base_price) / base_price) * 100,
        "demand_multiplier": demand_multiplier,
        "stock_multiplier": stock_multiplier,
        "recommendation": "INCREASE" if current_price > base_price else "DECREASE" if current_price < base_price else "MAINTAIN"
    }


@router.get("/dynamic-price/{product_id}", response_model=DynamicPriceResponse)
def get_dynamic_price(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dynamic price for a product"""
    
    dynamic_price = db.query(DynamicPrice).filter(
        DynamicPrice.product_id == product_id,
        DynamicPrice.user_id == current_user.id
    ).first()
    
    if not dynamic_price:
        raise HTTPException(status_code=404, detail="Dynamic price not found")
    
    return dynamic_price


@router.post("/inventory-health/{product_id}")
def calculate_inventory_health(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate inventory health score for a product"""
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get sales data
    ninety_days_ago = datetime.utcnow() - timedelta(days=90)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    total_sales_90d = db.query(func.sum(InvoiceItem.quantity)).join(
        Invoice, Invoice.id == InvoiceItem.invoice_id
    ).filter(
        InvoiceItem.product_id == product_id,
        Invoice.created_at >= ninety_days_ago
    ).scalar() or 0
    
    sales_30d = db.query(func.sum(InvoiceItem.quantity)).join(
        Invoice, Invoice.id == InvoiceItem.invoice_id
    ).filter(
        InvoiceItem.product_id == product_id,
        Invoice.created_at >= thirty_days_ago
    ).scalar() or 0
    
    # Calculate metrics
    avg_inventory = product.stock_quantity
    turnover_ratio = total_sales_90d / max(avg_inventory, 1)
    
    # Dead stock (no sales in 90 days)
    dead_stock_percentage = 0 if total_sales_90d > 0 else 100
    
    # Carrying cost ratio (simplified)
    carrying_cost_ratio = (product.purchase_price * 0.25) / max(product.selling_price, 1)
    
    # Stock out frequency (simplified)
    stock_out_frequency = 0  # Would need more detailed tracking
    
    # Calculate health score (0-100)
    health_score = 0
    
    # Turnover score (30 points)
    if turnover_ratio > 2:
        health_score += 30
    elif turnover_ratio > 1:
        health_score += 20
    elif turnover_ratio > 0.5:
        health_score += 10
    
    # Dead stock score (30 points)
    if dead_stock_percentage == 0:
        health_score += 30
    elif dead_stock_percentage < 20:
        health_score += 20
    elif dead_stock_percentage < 50:
        health_score += 10
    
    # Carrying cost score (20 points)
    if carrying_cost_ratio < 0.1:
        health_score += 20
    elif carrying_cost_ratio < 0.2:
        health_score += 15
    elif carrying_cost_ratio < 0.3:
        health_score += 10
    
    # Stock level score (20 points)
    if product.stock_quantity > 0 and product.stock_quantity < 100:
        health_score += 20
    elif product.stock_quantity >= 100:
        health_score += 15
    
    # Determine status
    if health_score >= 80:
        status = InventoryHealthStatus.EXCELLENT
    elif health_score >= 60:
        status = InventoryHealthStatus.GOOD
    elif health_score >= 40:
        status = InventoryHealthStatus.FAIR
    elif health_score >= 20:
        status = InventoryHealthStatus.POOR
    else:
        status = InventoryHealthStatus.CRITICAL
    
    # Generate recommendations
    recommendations = []
    if turnover_ratio < 0.5:
        recommendations.append("Low turnover - consider reducing stock or running promotions")
    if dead_stock_percentage > 50:
        recommendations.append("High dead stock - consider clearance sales")
    if carrying_cost_ratio > 0.3:
        recommendations.append("High carrying costs - optimize inventory levels")
    
    # Save health record
    health = db.query(InventoryHealth).filter(
        InventoryHealth.product_id == product_id,
        InventoryHealth.user_id == current_user.id
    ).first()
    
    if health:
        health.turnover_ratio = turnover_ratio
        health.stock_out_frequency = stock_out_frequency
        health.dead_stock_percentage = dead_stock_percentage
        health.carrying_cost_ratio = carrying_cost_ratio
        health.health_score = health_score
        health.status = status
        health.recommendations = "|".join(recommendations)
    else:
        health = InventoryHealth(
            user_id=current_user.id,
            product_id=product_id,
            turnover_ratio=turnover_ratio,
            stock_out_frequency=stock_out_frequency,
            dead_stock_percentage=dead_stock_percentage,
            carrying_cost_ratio=carrying_cost_ratio,
            health_score=health_score,
            status=status,
            recommendations="|".join(recommendations)
        )
        db.add(health)
    
    db.commit()
    db.refresh(health)
    
    return health


@router.get("/inventory-health/{product_id}", response_model=InventoryHealthResponse)
def get_inventory_health(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get inventory health for a product"""
    
    health = db.query(InventoryHealth).filter(
        InventoryHealth.product_id == product_id,
        InventoryHealth.user_id == current_user.id
    ).first()
    
    if not health:
        raise HTTPException(status_code=404, detail="Inventory health not found")
    
    return health
