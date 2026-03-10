"""
Expanded Agent Tools — all tenant-scoped actions available to agents.
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, text

logger = logging.getLogger(__name__)

# Tools schema for Gemini function calling
TOOLS_SCHEMA = [
    {
        "name": "check_inventory_health",
        "description": "Check all products below reorder level. Returns list of low-stock products.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "threshold": {"type": "NUMBER", "description": "Stock threshold (default: 10)"},
            },
        },
    },
    {
        "name": "get_revenue_summary",
        "description": "Get revenue summary for the last N days.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "days": {"type": "NUMBER", "description": "Number of days to look back (default: 30)"},
            },
        },
    },
    {
        "name": "get_top_selling_products",
        "description": "Get top selling products by revenue.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "limit": {"type": "NUMBER", "description": "Number of products (default: 10)"},
                "days": {"type": "NUMBER", "description": "Period in days (default: 30)"},
            },
        },
    },
    {
        "name": "analyze_sales_trend",
        "description": "Analyze sales trend for the last 30 vs previous 30 days.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "product_id": {"type": "STRING", "description": "Optional product ID to filter"},
            },
        },
    },
    {
        "name": "detect_price_anomalies",
        "description": "Find products with margin below 10% or selling below cost.",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
    {
        "name": "calculate_reorder_quantity",
        "description": "Calculate recommended reorder quantity for a product.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "product_id": {"type": "STRING", "description": "Product ID"},
                "days_of_supply": {"type": "NUMBER", "description": "Days of supply to target (default: 45)"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "create_alert",
        "description": "Create a business alert for the tenant.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "title": {"type": "STRING"},
                "message": {"type": "STRING"},
                "alert_type": {"type": "STRING", "description": "stock_alert|profit_alert|system_alert|pricing_alert|compliance_alert"},
                "severity": {"type": "STRING", "description": "Critical|High|Medium|Low|Info"},
            },
            "required": ["title", "message"],
        },
    },
    {
        "name": "create_dynamic_price_suggestion",
        "description": "Suggest a new price for a product.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "product_id": {"type": "STRING"},
                "suggested_price": {"type": "NUMBER"},
                "reason": {"type": "STRING"},
                "confidence": {"type": "NUMBER", "description": "0-1 confidence score"},
            },
            "required": ["product_id", "suggested_price", "reason"],
        },
    },
    {
        "name": "get_customer_segments",
        "description": "Get customer segments by purchase frequency and value.",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
    {
        "name": "analyze_dead_stock",
        "description": "Find products with no sales in the last 60 days.",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
    {
        "name": "finish",
        "description": "Call this when analysis is complete.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "summary": {"type": "STRING", "description": "Final summary of actions taken"},
            },
            "required": ["summary"],
        },
    },
]


class AgentTools:
    """Tenant-scoped tool registry for agents."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def execute(self, tool_name: str, params: Dict[str, Any]) -> Any:
        # Strip internal params
        clean_params = {k: v for k, v in params.items() if not k.startswith("_")}
        method = getattr(self, tool_name, None)
        if not method:
            raise ValueError(f"Unknown tool: {tool_name}")
        return method(**clean_params)

    # ─── Tool Implementations ─────────────────────────────────────────────────

    def check_inventory_health(self, threshold: float = 10) -> List[Dict]:
        """Return products at or below threshold stock."""
        try:
            rows = self.db.execute(
                text("""
                    SELECT id, product_name, sku, stock_quantity, reorder_level,
                           selling_price, purchase_price
                    FROM products
                    WHERE tenant_id = :tenant_id
                      AND is_active = true
                      AND stock_quantity <= :threshold
                    ORDER BY stock_quantity ASC
                    LIMIT 50
                """),
                {"tenant_id": self.tenant_id, "threshold": int(threshold)},
            ).fetchall()
            return [{"id": str(r[0]), "name": r[1], "sku": r[2], "stock": r[3],
                     "reorder_level": r[4], "selling_price": r[5], "purchase_price": r[6]}
                    for r in rows]
        except Exception as e:
            logger.error(f"check_inventory_health failed: {e}")
            return []

    def get_revenue_summary(self, days: float = 30) -> Dict:
        """Revenue summary for last N days."""
        try:
            since = datetime.utcnow() - timedelta(days=int(days))
            rows = self.db.execute(
                text("""
                    SELECT
                        COUNT(*) as invoice_count,
                        COALESCE(SUM(total_amount), 0) as total_revenue,
                        COALESCE(AVG(total_amount), 0) as avg_order_value,
                        COUNT(DISTINCT customer_phone) as unique_customers
                    FROM invoices
                    WHERE tenant_id = :tenant_id
                      AND created_at >= :since
                      AND payment_status != 'CANCELLED'
                """),
                {"tenant_id": self.tenant_id, "since": since},
            ).fetchone()
            return {
                "period_days": int(days),
                "invoice_count": rows[0] if rows else 0,
                "total_revenue": round(rows[1] if rows else 0, 2),
                "avg_order_value": round(rows[2] if rows else 0, 2),
                "unique_customers": rows[3] if rows else 0,
            }
        except Exception as e:
            logger.error(f"get_revenue_summary failed: {e}")
            return {"period_days": int(days), "invoice_count": 0, "total_revenue": 0,
                    "avg_order_value": 0, "unique_customers": 0}

    def get_top_selling_products(self, limit: float = 10, days: float = 30) -> List[Dict]:
        """Top products by sales volume."""
        try:
            since = datetime.utcnow() - timedelta(days=int(days))
            rows = self.db.execute(
                text("""
                    SELECT ii.product_name, ii.product_id,
                           SUM(ii.quantity) as total_qty,
                           SUM(ii.line_total) as total_revenue
                    FROM invoice_items ii
                    JOIN invoices i ON i.id = ii.invoice_id
                    WHERE i.tenant_id = :tenant_id
                      AND i.created_at >= :since
                    GROUP BY ii.product_name, ii.product_id
                    ORDER BY total_revenue DESC
                    LIMIT :limit
                """),
                {"tenant_id": self.tenant_id, "since": since, "limit": int(limit)},
            ).fetchall()
            return [{"name": r[0], "product_id": str(r[1]), "qty_sold": r[2],
                     "revenue": round(r[3], 2)} for r in rows]
        except Exception as e:
            logger.error(f"get_top_selling_products failed: {e}")
            return []

    def analyze_sales_trend(self, product_id: Optional[str] = None) -> Dict:
        """Compare current 30d vs previous 30d revenue."""
        try:
            now = datetime.utcnow()
            d30 = now - timedelta(days=30)
            d60 = now - timedelta(days=60)

            base = "WHERE i.tenant_id = :tenant_id"
            params = {"tenant_id": self.tenant_id}
            if product_id:
                base += " AND ii.product_id = :product_id"
                params["product_id"] = product_id

            def _get_rev(since, until):
                rows = self.db.execute(text(f"""
                    SELECT COALESCE(SUM(i.total_amount), 0)
                    FROM invoices i
                    {base.replace('ii.', 'i.')}
                      AND i.created_at >= :since AND i.created_at < :until
                """), {**params, "since": since, "until": until}).fetchone()
                return float(rows[0]) if rows else 0

            curr = _get_rev(d30, now)
            prev = _get_rev(d60, d30)
            change_pct = round(((curr - prev) / prev * 100) if prev > 0 else 0, 1)
            return {
                "current_30d": round(curr, 2), "previous_30d": round(prev, 2),
                "change_pct": change_pct,
                "trend": "increasing" if change_pct > 5 else "decreasing" if change_pct < -5 else "stable",
            }
        except Exception as e:
            logger.error(f"analyze_sales_trend failed: {e}")
            return {"current_30d": 0, "previous_30d": 0, "change_pct": 0, "trend": "unknown"}

    def detect_price_anomalies(self) -> List[Dict]:
        """Find products with unhealthy margins."""
        try:
            rows = self.db.execute(
                text("""
                    SELECT id, product_name, purchase_price, selling_price,
                           CASE WHEN selling_price > 0
                                THEN ((selling_price - purchase_price) / selling_price * 100)
                                ELSE -100 END as margin_pct
                    FROM products
                    WHERE tenant_id = :tenant_id
                      AND is_active = true
                      AND purchase_price > 0
                      AND selling_price > 0
                      AND ((selling_price - purchase_price) / selling_price * 100) < 10
                    ORDER BY margin_pct ASC
                    LIMIT 20
                """),
                {"tenant_id": self.tenant_id},
            ).fetchall()
            return [{"id": str(r[0]), "name": r[1], "cost": r[2], "price": r[3],
                     "margin_pct": round(r[4], 1)} for r in rows]
        except Exception as e:
            logger.error(f"detect_price_anomalies failed: {e}")
            return []

    def calculate_reorder_quantity(self, product_id: str, days_of_supply: float = 45) -> Dict:
        """Calculate EOQ-based reorder quantity."""
        try:
            # Get average daily sales
            since = datetime.utcnow() - timedelta(days=30)
            row = self.db.execute(
                text("""
                    SELECT COALESCE(SUM(ii.quantity), 0) / 30.0 as daily_avg,
                           p.stock_quantity, p.reorder_level, p.product_name
                    FROM products p
                    LEFT JOIN invoice_items ii ON ii.product_id = p.id
                    LEFT JOIN invoices i ON i.id = ii.invoice_id AND i.created_at >= :since
                    WHERE p.id = :product_id AND p.tenant_id = :tenant_id
                    GROUP BY p.id, p.stock_quantity, p.reorder_level, p.product_name
                """),
                {"product_id": product_id, "tenant_id": self.tenant_id, "since": since},
            ).fetchone()

            if not row:
                return {"error": "Product not found"}

            daily_avg = float(row[0])
            current_stock = row[1]
            target_qty = max(int(daily_avg * days_of_supply), row[2] * 3, 10)
            reorder_qty = max(0, target_qty - current_stock)

            return {
                "product_id": product_id, "product_name": row[3],
                "daily_avg_sales": round(daily_avg, 2),
                "current_stock": current_stock,
                "recommended_reorder_qty": reorder_qty,
                "days_of_stock_remaining": round(current_stock / daily_avg, 1) if daily_avg > 0 else 999,
                "target_stock_level": target_qty,
            }
        except Exception as e:
            logger.error(f"calculate_reorder_quantity failed: {e}")
            return {"error": str(e)}

    def create_alert(self, title: str, message: str, alert_type: str = "system_alert",
                     severity: str = "Medium") -> str:
        """Create a tenant-scoped alert."""
        try:
            from app.models.alert import Alert
            alert = Alert(
                id=uuid.uuid4(), tenant_id=self.tenant_id,
                title=title[:255], message=message[:1000],
                type=alert_type, severity=severity,
            )
            self.db.add(alert)
            self.db.commit()
            logger.info(f"Agent created alert: {title[:50]} [{severity}]")
            return str(alert.id)
        except Exception as e:
            self.db.rollback()
            logger.error(f"create_alert failed: {e}")
            return f"error: {e}"

    def create_dynamic_price_suggestion(self, product_id: str, suggested_price: float,
                                         reason: str, confidence: float = 0.8) -> str:
        """Save a dynamic price suggestion."""
        try:
            from app.models.dynamic_price import DynamicPrice
            suggestion = DynamicPrice(
                id=uuid.uuid4(), tenant_id=self.tenant_id, product_id=product_id,
                suggested_price=suggested_price, adjustment_reason=reason[:500],
                confidence=min(1.0, max(0.0, confidence)),
                valid_until=datetime.utcnow() + timedelta(days=7),
            )
            self.db.add(suggestion)
            self.db.commit()
            return str(suggestion.id)
        except Exception as e:
            self.db.rollback()
            logger.error(f"create_dynamic_price_suggestion failed: {e}")
            return f"error: {e}"

    def get_customer_segments(self) -> Dict:
        """Segment customers by purchase frequency."""
        try:
            rows = self.db.execute(
                text("""
                    SELECT
                        COUNT(*) FILTER (WHERE total_purchases >= 10000) as high_value,
                        COUNT(*) FILTER (WHERE total_purchases >= 1000 AND total_purchases < 10000) as mid_value,
                        COUNT(*) FILTER (WHERE total_purchases < 1000) as low_value,
                        COUNT(*) as total
                    FROM customers
                    WHERE tenant_id = :tenant_id AND is_active = true
                """),
                {"tenant_id": self.tenant_id},
            ).fetchone()
            if rows:
                return {"high_value": rows[0], "mid_value": rows[1],
                        "low_value": rows[2], "total": rows[3]}
            return {"high_value": 0, "mid_value": 0, "low_value": 0, "total": 0}
        except Exception as e:
            logger.error(f"get_customer_segments failed: {e}")
            return {}

    def analyze_dead_stock(self) -> List[Dict]:
        """Products with zero sales in 60 days."""
        try:
            since = datetime.utcnow() - timedelta(days=60)
            rows = self.db.execute(
                text("""
                    SELECT p.id, p.product_name, p.stock_quantity,
                           p.selling_price, p.purchase_price,
                           (p.stock_quantity * p.purchase_price) as stock_value
                    FROM products p
                    WHERE p.tenant_id = :tenant_id
                      AND p.is_active = true
                      AND p.stock_quantity > 0
                      AND NOT EXISTS (
                          SELECT 1 FROM invoice_items ii
                          JOIN invoices i ON i.id = ii.invoice_id
                          WHERE ii.product_id = p.id AND i.created_at >= :since
                      )
                    ORDER BY stock_value DESC
                    LIMIT 20
                """),
                {"tenant_id": self.tenant_id, "since": since},
            ).fetchall()
            return [{"id": str(r[0]), "name": r[1], "stock": r[2],
                     "price": r[3], "cost": r[4], "stock_value": round(r[5], 2)}
                    for r in rows]
        except Exception as e:
            logger.error(f"analyze_dead_stock failed: {e}")
            return []
