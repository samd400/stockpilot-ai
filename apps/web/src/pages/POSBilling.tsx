/**
 * POS Billing Page — scan barcodes, add products, create invoice, print receipt.
 * Works offline via Dexie sync queue.
 */

import React, { useState, useEffect, useCallback } from "react";
import { findProductByBarcode, findProductBySku, getLocalProducts, cacheProducts } from "../lib/offlineDb";
import { enqueuePOSBill, getQueueStatus, processQueue } from "../lib/syncWorker";
import type { Product, Invoice, ReceiptOptions } from "@stockpilot/sdk";
import { formatReceiptHTML } from "@stockpilot/sdk";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface CartItem {
  product: Product;
  quantity: number;
}

interface QueueStatus {
  pending: number;
  failed: number;
  total: number;
}

export default function POSBilling() {
  const [cart, setCart] = useState<CartItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [showScanner, setShowScanner] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [queueStatus, setQueueStatus] = useState<QueueStatus>({ pending: 0, failed: 0, total: 0 });
  const [lastReceipt, setLastReceipt] = useState<Invoice | null>(null);
  const [paymentMode, setPaymentMode] = useState("CASH");
  const [message, setMessage] = useState("");

  // Monitor online status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  // Load products (from API or local cache)
  useEffect(() => {
    loadProducts();
    refreshQueueStatus();
    const interval = setInterval(refreshQueueStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  async function loadProducts() {
    try {
      if (navigator.onLine) {
        const token = localStorage.getItem("token");
        const res = await fetch(`${API_BASE}/products`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setProducts(data);
          await cacheProducts(data);
          return;
        }
      }
    } catch {}
    // Fallback: load from local DB
    const local = await getLocalProducts();
    setProducts(local);
  }

  async function refreshQueueStatus() {
    const status = await getQueueStatus();
    setQueueStatus(status);
  }

  // Barcode / SKU search
  const handleSearch = useCallback(async (query: string) => {
    if (!query.trim()) return;
    // Try barcode first, then SKU, then name search
    let product = await findProductByBarcode(query);
    if (!product) product = await findProductBySku(query);
    if (!product) {
      product = products.find(
        (p) =>
          p.product_name.toLowerCase().includes(query.toLowerCase()) ||
          p.sku?.toLowerCase() === query.toLowerCase()
      );
    }

    if (product) {
      addToCart(product);
      setSearchQuery("");
    } else {
      setMessage(`Product not found: ${query}`);
      setTimeout(() => setMessage(""), 3000);
    }
  }, [products]);

  function addToCart(product: Product) {
    setCart((prev) => {
      const existing = prev.find((c) => c.product.id === product.id);
      if (existing) {
        return prev.map((c) =>
          c.product.id === product.id ? { ...c, quantity: c.quantity + 1 } : c
        );
      }
      return [...prev, { product, quantity: 1 }];
    });
  }

  function removeFromCart(productId: string) {
    setCart((prev) => prev.filter((c) => c.product.id !== productId));
  }

  function updateQuantity(productId: string, qty: number) {
    if (qty <= 0) return removeFromCart(productId);
    setCart((prev) => prev.map((c) => (c.product.id === productId ? { ...c, quantity: qty } : c)));
  }

  const subtotal = cart.reduce((sum, c) => sum + c.product.selling_price * c.quantity, 0);
  const taxRate = 0.18;
  const tax = subtotal * taxRate;
  const total = subtotal + tax;

  // Create POS bill
  async function handleCheckout() {
    if (cart.length === 0) return;

    const billData = {
      items: cart.map((c) => ({
        product_id: c.product.id,
        quantity: c.quantity,
        price: c.product.selling_price,
      })),
      payment_mode: paymentMode,
    };

    const invoice: Invoice = {
      invoice_number: `POS-${Date.now().toString(36).toUpperCase()}`,
      items: cart.map((c) => ({
        product_id: c.product.id,
        product_name: c.product.product_name,
        quantity: c.quantity,
        price_per_unit: c.product.selling_price,
        gst_percentage: c.product.gst_percentage || 18,
      })),
      subtotal,
      tax,
      total_amount: total,
      currency: "INR",
      payment_status: "PAID",
      created_at: new Date().toISOString(),
    };

    try {
      if (navigator.onLine) {
        const token = localStorage.getItem("token");
        const res = await fetch(`${API_BASE}/pos/bill`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify(billData),
        });
        if (res.ok) {
          const data = await res.json();
          invoice.invoice_number = data.invoice_number;
          invoice.id = data.invoice_id;
          setMessage("✅ Bill created successfully!");
        } else {
          throw new Error("API error");
        }
      } else {
        throw new Error("Offline");
      }
    } catch {
      // Queue for offline sync
      await enqueuePOSBill(billData);
      setMessage("📱 Saved offline — will sync when online");
    }

    setLastReceipt(invoice);
    setCart([]);
    await refreshQueueStatus();
    setTimeout(() => setMessage(""), 4000);
  }

  // Print receipt
  function handlePrint() {
    if (!lastReceipt) return;
    const options: ReceiptOptions = {
      paperWidth: 80,
      currency: "INR",
      showGST: true,
      showVAT: false,
      storeName: "StockPilot Store",
      footerText: "Thank you! Visit again.",
    };
    const html = formatReceiptHTML(lastReceipt, options);
    const win = window.open("", "_blank", "width=400,height=600");
    if (!win) return;
    win.document.write(html);
    win.document.close();
    win.focus();
    setTimeout(() => { win.print(); win.close(); }, 300);
  }

  // Manual sync
  async function handleManualSync() {
    const result = await processQueue();
    await refreshQueueStatus();
    setMessage(`Synced: ${result.synced}, Failed: ${result.failed}, Conflicts: ${result.conflicts}`);
    setTimeout(() => setMessage(""), 4000);
  }

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "system-ui, sans-serif" }}>
      {/* Left: Product search & list */}
      <div style={{ flex: 1, padding: "16px", overflowY: "auto", borderRight: "1px solid #e5e7eb" }}>
        <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch(searchQuery)}
            placeholder="🔍 Scan barcode or enter SKU..."
            autoFocus
            style={{
              flex: 1, padding: "12px", borderRadius: "8px", border: "1px solid #d1d5db",
              fontSize: "16px", outline: "none",
            }}
          />
          <button
            onClick={() => handleSearch(searchQuery)}
            style={{ padding: "12px 20px", background: "#2563eb", color: "#fff", border: "none", borderRadius: "8px", cursor: "pointer", fontWeight: 600 }}
          >
            Add
          </button>
        </div>

        {/* Status bar */}
        <div style={{ display: "flex", gap: "12px", marginBottom: "16px", fontSize: "13px" }}>
          <span style={{ color: isOnline ? "#16a34a" : "#dc2626" }}>
            {isOnline ? "🟢 Online" : "🔴 Offline"}
          </span>
          {queueStatus.total > 0 && (
            <span style={{ color: "#f59e0b" }}>
              📤 {queueStatus.total} pending sync
              <button onClick={handleManualSync} style={{ marginLeft: "8px", padding: "2px 8px", fontSize: "12px", cursor: "pointer" }}>
                Sync Now
              </button>
            </span>
          )}
        </div>

        {message && (
          <div style={{ padding: "10px", background: "#f0f9ff", borderRadius: "8px", marginBottom: "12px", fontSize: "14px" }}>
            {message}
          </div>
        )}

        {/* Quick product grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: "8px" }}>
          {products.slice(0, 20).map((p) => (
            <div
              key={p.id}
              onClick={() => addToCart(p)}
              style={{
                padding: "12px", border: "1px solid #e5e7eb", borderRadius: "8px",
                cursor: "pointer", background: "#fff", transition: "all 0.1s",
              }}
            >
              <div style={{ fontWeight: 600, fontSize: "13px", marginBottom: "4px" }}>{p.product_name}</div>
              <div style={{ fontSize: "12px", color: "#666" }}>Stock: {p.stock_quantity}</div>
              <div style={{ fontWeight: 700, color: "#2563eb" }}>₹{p.selling_price}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Right: Cart & Checkout */}
      <div style={{ width: "380px", display: "flex", flexDirection: "column", background: "#f9fafb" }}>
        <div style={{ padding: "16px", borderBottom: "1px solid #e5e7eb" }}>
          <h2 style={{ margin: 0, fontSize: "18px" }}>🛒 Cart ({cart.length})</h2>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: "8px 16px" }}>
          {cart.length === 0 ? (
            <p style={{ textAlign: "center", color: "#999", padding: "40px 0" }}>Scan a barcode to start</p>
          ) : (
            cart.map((c) => (
              <div key={c.product.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: "1px solid #f0f0f0" }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: "14px" }}>{c.product.product_name}</div>
                  <div style={{ fontSize: "12px", color: "#666" }}>₹{c.product.selling_price} each</div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <button onClick={() => updateQuantity(c.product.id, c.quantity - 1)} style={{ width: "28px", height: "28px", cursor: "pointer" }}>-</button>
                  <span style={{ fontWeight: 600, minWidth: "24px", textAlign: "center" }}>{c.quantity}</span>
                  <button onClick={() => updateQuantity(c.product.id, c.quantity + 1)} style={{ width: "28px", height: "28px", cursor: "pointer" }}>+</button>
                  <span style={{ fontWeight: 700, minWidth: "70px", textAlign: "right" }}>₹{(c.product.selling_price * c.quantity).toFixed(2)}</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Totals & Checkout */}
        <div style={{ padding: "16px", borderTop: "1px solid #e5e7eb", background: "#fff" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
            <span>Subtotal</span><span>₹{subtotal.toFixed(2)}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px", fontSize: "13px", color: "#666" }}>
            <span>Tax (18% GST)</span><span>₹{tax.toFixed(2)}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 700, fontSize: "20px", marginBottom: "12px" }}>
            <span>Total</span><span>₹{total.toFixed(2)}</span>
          </div>

          <select
            value={paymentMode}
            onChange={(e) => setPaymentMode(e.target.value)}
            style={{ width: "100%", padding: "8px", marginBottom: "12px", borderRadius: "8px", border: "1px solid #d1d5db" }}
          >
            <option value="CASH">💵 Cash</option>
            <option value="UPI">📱 UPI</option>
            <option value="CARD">💳 Card</option>
          </select>

          <button
            onClick={handleCheckout}
            disabled={cart.length === 0}
            style={{
              width: "100%", padding: "14px", background: cart.length > 0 ? "#16a34a" : "#d1d5db",
              color: "#fff", border: "none", borderRadius: "8px", cursor: cart.length > 0 ? "pointer" : "default",
              fontWeight: 700, fontSize: "16px",
            }}
          >
            💰 Charge ₹{total.toFixed(2)}
          </button>

          {lastReceipt && (
            <button
              onClick={handlePrint}
              style={{
                width: "100%", padding: "10px", marginTop: "8px", background: "#2563eb",
                color: "#fff", border: "none", borderRadius: "8px", cursor: "pointer", fontWeight: 600,
              }}
            >
              🖨️ Print Last Receipt
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
