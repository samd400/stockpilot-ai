"""
Business Assistant — Conversational AI with tenant data context.
Uses RAG pattern: fetches relevant data before responding.
"""
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.gemini_service import call_gemini

logger = logging.getLogger(__name__)


def _get_business_context(db: Session, tenant_id: str) -> str:
    """Fetch recent business data to enrich assistant responses."""
    try:
        stats = db.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM invoices WHERE tenant_id = :tid AND created_at >= NOW() - INTERVAL '30 days') as invoices_30d,
                (SELECT COALESCE(SUM(total_amount), 0) FROM invoices WHERE tenant_id = :tid AND created_at >= NOW() - INTERVAL '30 days') as revenue_30d,
                (SELECT COUNT(*) FROM products WHERE tenant_id = :tid AND is_active = true) as total_products,
                (SELECT COUNT(*) FROM products WHERE tenant_id = :tid AND stock_quantity <= 10 AND is_active = true) as low_stock_count,
                (SELECT COUNT(*) FROM alerts WHERE tenant_id = :tid AND is_read = false) as unread_alerts
        """), {"tid": tenant_id}).fetchone()

        top_products = db.execute(text("""
            SELECT p.product_name, SUM(ii.quantity) as sold
            FROM invoice_items ii
            JOIN invoices i ON i.id = ii.invoice_id
            JOIN products p ON p.id = ii.product_id
            WHERE i.tenant_id = :tid AND i.created_at >= NOW() - INTERVAL '30 days'
            GROUP BY p.product_name ORDER BY sold DESC LIMIT 5
        """), {"tid": tenant_id}).fetchall()

        context = f"""Business Data (Last 30 Days):
- Invoices created: {stats[0] if stats else 'N/A'}
- Revenue: {round(stats[1], 2) if stats else 'N/A'}
- Active products: {stats[2] if stats else 'N/A'}
- Low stock items: {stats[3] if stats else 'N/A'}
- Unread alerts: {stats[4] if stats else 'N/A'}

Top 5 Products by Sales:
{chr(10).join(f"- {r[0]}: {r[1]} units" for r in top_products) if top_products else "No sales data"}"""
        return context
    except Exception as e:
        logger.error(f"Context fetch failed: {e}")
        return "Business data temporarily unavailable."


def chat(db: Session, tenant_id: str, message: str,
         conversation_history: List[Dict] = None) -> str:
    """
    Multi-turn business assistant chat with RAG context.
    conversation_history: list of {"role": "user"|"assistant", "content": "..."}
    """
    context = _get_business_context(db, tenant_id)

    # Build conversation prompt
    history_text = ""
    if conversation_history:
        for turn in conversation_history[-6:]:  # Last 6 turns
            role = turn.get("role", "user")
            content = turn.get("content", "")
            history_text += f"\n{role.upper()}: {content}"

    system_prompt = f"""You are StockPilot AI — an intelligent business assistant for inventory and billing management.
You help business owners understand their data, make decisions, and manage their operations.

Current business context:
{context}

You can help with:
- Sales and revenue analysis
- Inventory management advice
- Pricing suggestions
- Customer insights
- Invoice and billing questions
- General business strategy

Be concise, data-driven, and actionable. Use the business data above when relevant.
If asked about specific numbers, reference the context data provided."""

    full_prompt = f"{history_text}\nUSER: {message}\n\nAssistant:" if history_text else message

    response = call_gemini(full_prompt, system_prompt, temperature=0.4, max_tokens=1024)

    if not response:
        return ("I'm having trouble connecting to the AI service right now. "
                "Please try again in a moment.")

    return response.strip()
