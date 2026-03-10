import React, { useState, useEffect, useRef } from 'react';
import {
  ShoppingCart, Search, Plus, Minus, Trash2,
  CreditCard, Banknote, Smartphone, Printer
} from 'lucide-react';
import { productsAPI, customersAPI, posAPI } from '../services/api';

const GST_RATE = 0.18;

function POSBilling() {
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [recentBills, setRecentBills] = useState([]);
  const [cart, setCart] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [paymentMode, setPaymentMode] = useState('cash');
  const [discountType, setDiscountType] = useState('flat');
  const [discountValue, setDiscountValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [billing, setBilling] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [error, setError] = useState('');
  const searchRef = useRef(null);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowResults(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      const [prodRes, custRes, billsRes] = await Promise.all([
        productsAPI.getAll(),
        customersAPI.getAll(),
        posAPI.getBills()
      ]);
      setProducts(prodRes.data || []);
      setCustomers(custRes.data || []);
      setRecentBills(billsRes.data || []);
    } catch (err) {
      setError('Failed to load data. Please refresh.');
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = searchQuery.trim()
    ? products.filter((p) => {
        const q = searchQuery.toLowerCase();
        return (
          (p.name && p.name.toLowerCase().includes(q)) ||
          (p.barcode && p.barcode.toLowerCase().includes(q)) ||
          (p.sku && p.sku.toLowerCase().includes(q))
        );
      })
    : [];

  const addToCart = (product) => {
    setCart((prev) => {
      const existing = prev.find((item) => item.product_id === product.id);
      if (existing) {
        return prev.map((item) =>
          item.product_id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      }
      return [
        ...prev,
        {
          product_id: product.id,
          name: product.name,
          price: product.price || product.selling_price || 0,
          quantity: 1,
          stock: product.stock ?? product.quantity ?? 0
        }
      ];
    });
    setSearchQuery('');
    setShowResults(false);
  };

  const updateQuantity = (productId, delta) => {
    setCart((prev) =>
      prev
        .map((item) =>
          item.product_id === productId
            ? { ...item, quantity: Math.max(0, item.quantity + delta) }
            : item
        )
        .filter((item) => item.quantity > 0)
    );
  };

  const removeFromCart = (productId) => {
    setCart((prev) => prev.filter((item) => item.product_id !== productId));
  };

  const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const discountAmount =
    discountType === 'percentage'
      ? (subtotal * Math.min(Number(discountValue) || 0, 100)) / 100
      : Math.min(Number(discountValue) || 0, subtotal);
  const taxableAmount = subtotal - discountAmount;
  const gstAmount = taxableAmount * GST_RATE;
  const grandTotal = taxableAmount + gstAmount;

  const handleCharge = async () => {
    if (cart.length === 0) {
      setError('Cart is empty. Add products before billing.');
      return;
    }
    setBilling(true);
    setError('');
    setSuccessMsg('');
    try {
      const payload = {
        items: cart.map(({ product_id, quantity, price }) => ({
          product_id,
          quantity,
          price
        })),
        payment_mode: paymentMode,
        discount: discountAmount,
        ...(selectedCustomer && { customer_id: Number(selectedCustomer) })
      };
      const res = await posAPI.createBill(payload);
      const billNumber = res.data?.bill_number || res.data?.id || 'N/A';
      setSuccessMsg(`Bill #${billNumber} created successfully!`);
      setCart([]);
      setDiscountValue(0);
      setSelectedCustomer('');
      setPaymentMode('cash');
      // Refresh recent bills
      const billsRes = await posAPI.getBills();
      setRecentBills(billsRes.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create bill. Please try again.');
    } finally {
      setBilling(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const resetCart = () => {
    setCart([]);
    setDiscountValue(0);
    setSelectedCustomer('');
    setPaymentMode('cash');
    setSuccessMsg('');
    setError('');
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading">Loading POS...</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <ShoppingCart size={28} />
        <h1 className="page-title">POS Billing</h1>
      </div>

      {error && (
        <div className="alert alert-error" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{error}</span>
          <button onClick={() => setError('')} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18 }}>×</button>
        </div>
      )}

      {successMsg && (
        <div className="alert alert-success" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{successMsg}</span>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-secondary" onClick={handlePrint} style={{ padding: '4px 12px', display: 'flex', alignItems: 'center', gap: 4 }}>
              <Printer size={14} /> Print
            </button>
            <button onClick={() => setSuccessMsg('')} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18 }}>×</button>
          </div>
        </div>
      )}

      {/* Search Bar */}
      <div className="card" style={{ padding: 16, marginBottom: 16, position: 'relative' }} ref={searchRef}>
        <div style={{ position: 'relative' }}>
          <Search size={18} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
          <input
            className="form-input"
            style={{ paddingLeft: 40 }}
            type="text"
            placeholder="Search products by name, barcode, or SKU..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setShowResults(true);
            }}
            onFocus={() => searchQuery.trim() && setShowResults(true)}
          />
        </div>
        {showResults && filteredProducts.length > 0 && (
          <div style={{
            position: 'absolute', left: 0, right: 0, top: '100%', zIndex: 50,
            background: 'var(--card-background)', border: '1px solid var(--border-color)',
            borderRadius: 8, maxHeight: 260, overflowY: 'auto',
            boxShadow: '0 4px 12px rgba(0,0,0,0.12)', margin: '0 16px'
          }}>
            {filteredProducts.slice(0, 10).map((p) => (
              <div
                key={p.id}
                onClick={() => addToCart(p)}
                style={{
                  padding: '10px 16px', cursor: 'pointer', display: 'flex',
                  justifyContent: 'space-between', alignItems: 'center',
                  borderBottom: '1px solid var(--border-color)', transition: 'background 0.15s'
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--background-color)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
              >
                <div>
                  <div style={{ fontWeight: 500 }}>{p.name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    {p.barcode || p.sku || '—'}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontWeight: 600 }}>₹{(p.price || p.selling_price || 0).toFixed(2)}</div>
                  <div style={{ fontSize: 12, color: (p.stock ?? p.quantity ?? 0) > 0 ? 'var(--success-color)' : 'var(--danger-color)' }}>
                    Stock: {p.stock ?? p.quantity ?? 0}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        {showResults && searchQuery.trim() && filteredProducts.length === 0 && (
          <div style={{
            position: 'absolute', left: 0, right: 0, top: '100%', zIndex: 50,
            background: 'var(--card-background)', border: '1px solid var(--border-color)',
            borderRadius: 8, padding: '12px 16px', margin: '0 16px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.12)', color: 'var(--text-secondary)', textAlign: 'center'
          }}>
            No products found
          </div>
        )}
      </div>

      {/* Main POS Area */}
      <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
        {/* Cart - Left Side */}
        <div className="card" style={{ flex: '0 0 60%', minHeight: 400 }}>
          <div className="card-header">
            <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <ShoppingCart size={20} /> Cart
              {cart.length > 0 && (
                <span className="badge badge-success" style={{ marginLeft: 8 }}>{cart.length} items</span>
              )}
            </h2>
            {cart.length > 0 && (
              <button className="btn btn-danger" onClick={resetCart} style={{ padding: '6px 12px', fontSize: 13 }}>
                Clear Cart
              </button>
            )}
          </div>

          {cart.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-secondary)' }}>
              <ShoppingCart size={48} style={{ marginBottom: 12, opacity: 0.3 }} />
              <p>Cart is empty. Search and add products above.</p>
            </div>
          ) : (
            <>
              <table className="table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th style={{ textAlign: 'right' }}>Price</th>
                    <th style={{ textAlign: 'center' }}>Qty</th>
                    <th style={{ textAlign: 'right' }}>Subtotal</th>
                    <th style={{ textAlign: 'center', width: 50 }}></th>
                  </tr>
                </thead>
                <tbody>
                  {cart.map((item) => (
                    <tr key={item.product_id}>
                      <td style={{ fontWeight: 500 }}>{item.name}</td>
                      <td style={{ textAlign: 'right' }}>₹{item.price.toFixed(2)}</td>
                      <td style={{ textAlign: 'center' }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                          <button
                            className="btn"
                            style={{ padding: '4px 8px', background: 'var(--background-color)', border: '1px solid var(--border-color)' }}
                            onClick={() => updateQuantity(item.product_id, -1)}
                          >
                            <Minus size={14} />
                          </button>
                          <span style={{ minWidth: 28, textAlign: 'center', fontWeight: 600 }}>{item.quantity}</span>
                          <button
                            className="btn"
                            style={{ padding: '4px 8px', background: 'var(--background-color)', border: '1px solid var(--border-color)' }}
                            onClick={() => updateQuantity(item.product_id, 1)}
                          >
                            <Plus size={14} />
                          </button>
                        </div>
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 600 }}>₹{(item.price * item.quantity).toFixed(2)}</td>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          className="btn btn-danger"
                          style={{ padding: '4px 8px' }}
                          onClick={() => removeFromCart(item.product_id)}
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Cart Totals */}
              <div style={{ borderTop: '2px solid var(--border-color)', marginTop: 16, paddingTop: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, color: 'var(--text-secondary)' }}>
                  <span>Subtotal</span>
                  <span>₹{subtotal.toFixed(2)}</span>
                </div>
                {discountAmount > 0 && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, color: 'var(--danger-color)' }}>
                    <span>Discount</span>
                    <span>-₹{discountAmount.toFixed(2)}</span>
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, color: 'var(--text-secondary)' }}>
                  <span>GST (18%)</span>
                  <span>₹{gstAmount.toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, fontSize: 18, paddingTop: 8, borderTop: '1px solid var(--border-color)' }}>
                  <span>Grand Total</span>
                  <span>₹{grandTotal.toFixed(2)}</span>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Quick Actions - Right Side */}
        <div style={{ flex: '0 0 calc(40% - 24px)' }}>
          {/* Customer Select */}
          <div className="card">
            <div className="form-group">
              <label className="form-label">Customer (Optional)</label>
              <select
                className="form-input"
                value={selectedCustomer}
                onChange={(e) => setSelectedCustomer(e.target.value)}
              >
                <option value="">Walk-in Customer</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} {c.phone ? `(${c.phone})` : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* Payment Mode */}
            <div className="form-group">
              <label className="form-label">Payment Mode</label>
              <div style={{ display: 'flex', gap: 8 }}>
                {[
                  { mode: 'cash', label: 'Cash', icon: <Banknote size={16} /> },
                  { mode: 'card', label: 'Card', icon: <CreditCard size={16} /> },
                  { mode: 'upi', label: 'UPI', icon: <Smartphone size={16} /> }
                ].map(({ mode, label, icon }) => (
                  <button
                    key={mode}
                    className={`btn ${paymentMode === mode ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, padding: '10px 8px' }}
                    onClick={() => setPaymentMode(mode)}
                  >
                    {icon} {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Discount */}
            <div className="form-group">
              <label className="form-label">Discount</label>
              <div style={{ display: 'flex', gap: 8 }}>
                <select
                  className="form-input"
                  style={{ width: 'auto', flex: '0 0 120px' }}
                  value={discountType}
                  onChange={(e) => {
                    setDiscountType(e.target.value);
                    setDiscountValue(0);
                  }}
                >
                  <option value="flat">Flat (₹)</option>
                  <option value="percentage">Percent (%)</option>
                </select>
                <input
                  className="form-input"
                  type="number"
                  min="0"
                  max={discountType === 'percentage' ? 100 : undefined}
                  placeholder={discountType === 'percentage' ? '0%' : '₹0'}
                  value={discountValue || ''}
                  onChange={(e) => setDiscountValue(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Charge Button */}
          <button
            className="btn btn-primary"
            style={{
              width: '100%', padding: '16px 24px', fontSize: 18, fontWeight: 700,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              opacity: cart.length === 0 || billing ? 0.6 : 1
            }}
            disabled={cart.length === 0 || billing}
            onClick={handleCharge}
          >
            <ShoppingCart size={22} />
            {billing ? 'Processing...' : `Charge ₹${grandTotal.toFixed(2)}`}
          </button>
        </div>
      </div>

      {/* Recent Bills */}
      <div className="card" style={{ marginTop: 24 }}>
        <div className="card-header">
          <h2 className="card-title">Recent Bills</h2>
        </div>
        {recentBills.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '24px 0' }}>
            No recent bills found.
          </p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Bill #</th>
                <th>Customer</th>
                <th style={{ textAlign: 'right' }}>Total</th>
                <th>Payment</th>
                <th>Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {recentBills.slice(0, 10).map((bill) => (
                <tr key={bill.id}>
                  <td style={{ fontWeight: 500 }}>{bill.bill_number || `#${bill.id}`}</td>
                  <td>{bill.customer_name || bill.customer?.name || 'Walk-in'}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>₹{(bill.total || bill.grand_total || 0).toFixed(2)}</td>
                  <td>
                    <span className="badge" style={{ background: 'var(--background-color)' }}>
                      {(bill.payment_mode || '—').toUpperCase()}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>
                    {bill.created_at ? new Date(bill.created_at).toLocaleDateString() : '—'}
                  </td>
                  <td>
                    <span className={`badge ${bill.status === 'returned' ? 'badge-danger' : 'badge-success'}`}>
                      {bill.status || 'Completed'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default POSBilling;
