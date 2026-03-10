import React, { useState, useEffect } from 'react';
import { PackageSearch, Plus, Search, Send, CheckCircle, Truck, AlertTriangle } from 'lucide-react';
import { purchaseOrdersAPI, suppliersAPI, productsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

const STATUS_STYLES = {
  draft: { background: '#f1f5f9', color: '#475569' },
  sent: { background: '#dbeafe', color: '#1d4ed8' },
  confirmed: { background: '#e0e7ff', color: '#4338ca' },
  shipped: { background: '#fef3c7', color: '#b45309' },
  fulfilled: { background: '#dcfce7', color: '#15803d' },
  cancelled: { background: '#fee2e2', color: '#dc2626' },
};

function PurchaseOrders() {
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('inventory_write');
  const [orders, setOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [reorderData, setReorderData] = useState(null);
  const [formData, setFormData] = useState({
    supplier_id: '',
    items: [{ product_id: '', quantity: 1, unit_price: 0 }],
    notes: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [ordersRes, suppliersRes, productsRes] = await Promise.allSettled([
        purchaseOrdersAPI.getAll(),
        suppliersAPI.getAll(),
        productsAPI.getAll(),
      ]);
      if (ordersRes.status === 'fulfilled') setOrders(ordersRes.value.data);
      if (suppliersRes.status === 'fulfilled') setSuppliers(suppliersRes.value.data);
      if (productsRes.status === 'fulfilled') setProducts(productsRes.value.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await purchaseOrdersAPI.create(formData);
      fetchData();
      setShowModal(false);
      setFormData({ supplier_id: '', items: [{ product_id: '', quantity: 1, unit_price: 0 }], notes: '' });
    } catch (error) {
      console.error('Error creating PO:', error);
      alert(error.response?.data?.detail || 'Failed to create purchase order');
    }
  };

  const handleSend = async (id) => {
    try {
      await purchaseOrdersAPI.send(id);
      fetchData();
    } catch (error) {
      console.error('Error sending PO:', error);
      alert(error.response?.data?.detail || 'Failed to send PO');
    }
  };

  const handleFulfill = async (id) => {
    try {
      await purchaseOrdersAPI.fulfill(id);
      fetchData();
    } catch (error) {
      console.error('Error fulfilling PO:', error);
      alert(error.response?.data?.detail || 'Failed to fulfill PO');
    }
  };

  const handleReorderAnalysis = async () => {
    try {
      const response = await purchaseOrdersAPI.reorderAnalysis();
      setReorderData(response.data);
    } catch (error) {
      console.error('Error fetching reorder analysis:', error);
      alert('Failed to fetch reorder analysis');
    }
  };

  const addItem = () => {
    setFormData({ ...formData, items: [...formData.items, { product_id: '', quantity: 1, unit_price: 0 }] });
  };

  const removeItem = (index) => {
    setFormData({ ...formData, items: formData.items.filter((_, i) => i !== index) });
  };

  const updateItem = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index] = { ...newItems[index], [field]: value };
    setFormData({ ...formData, items: newItems });
  };

  const filteredOrders = orders.filter(o =>
    o.po_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    o.supplier_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalPOs = orders.length;
  const pending = orders.filter(o => ['draft', 'sent', 'confirmed'].includes(o.status)).length;
  const shipped = orders.filter(o => o.status === 'shipped').length;
  const fulfilled = orders.filter(o => o.status === 'fulfilled').length;

  const stats = [
    { label: 'Total POs', value: totalPOs, icon: PackageSearch, color: '#2563eb' },
    { label: 'Pending', value: pending, icon: Send, color: '#f59e0b' },
    { label: 'Shipped', value: shipped, icon: Truck, color: '#7c3aed' },
    { label: 'Fulfilled', value: fulfilled, icon: CheckCircle, color: '#059669' },
  ];

  if (loading) {
    return <div className="loading">Loading purchase orders...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Purchase Orders</h1>
        <p style={{ color: '#64748b' }}>Manage procurement and purchase orders</p>
      </div>

      <div className="stats-grid">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="stat-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <p className="stat-label">{stat.label}</p>
                  <p className="stat-value">{stat.value}</p>
                </div>
                <div style={{ padding: '10px', borderRadius: '8px', backgroundColor: `${stat.color}15` }}>
                  <Icon size={24} color={stat.color} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
            <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
              <Search size={20} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
              <input
                type="text"
                placeholder="Search purchase orders..."
                className="form-input"
                style={{ paddingLeft: '40px' }}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn btn-secondary" onClick={handleReorderAnalysis}>
              <AlertTriangle size={20} style={{ marginRight: '8px' }} />
              Reorder Analysis
            </button>
            {canWrite && (
              <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                <Plus size={20} style={{ marginRight: '8px' }} />
                Create PO
              </button>
            )}
          </div>
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>PO#</th>
              <th>Supplier</th>
              <th>Items</th>
              <th>Total</th>
              <th>Currency</th>
              <th>Status</th>
              <th>Created Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredOrders.map((order) => (
              <tr key={order.id}>
                <td style={{ fontWeight: 600 }}>{order.po_number}</td>
                <td>{order.supplier_name}</td>
                <td>{Array.isArray(order.items) ? order.items.length : 0} item(s)</td>
                <td>{(order.total_amount ?? 0).toLocaleString()}</td>
                <td>{order.currency || 'INR'}</td>
                <td>
                  <span
                    style={{
                      padding: '4px 10px',
                      borderRadius: '9999px',
                      fontSize: '12px',
                      fontWeight: 600,
                      textTransform: 'capitalize',
                      ...(STATUS_STYLES[order.status] || STATUS_STYLES.draft),
                    }}
                  >
                    {order.status}
                  </span>
                </td>
                <td>{order.created_at ? new Date(order.created_at).toLocaleDateString() : '-'}</td>
                <td style={{ display: 'flex', gap: '4px' }}>
                  {['draft', 'confirmed'].includes(order.status) && (
                    <button className="btn" style={{ padding: '6px', color: '#2563eb' }} onClick={() => handleSend(order.id)} title="Send">
                      <Send size={16} />
                    </button>
                  )}
                  {['sent', 'shipped'].includes(order.status) && (
                    <button className="btn" style={{ padding: '6px', color: '#059669' }} onClick={() => handleFulfill(order.id)} title="Mark Fulfilled">
                      <CheckCircle size={16} />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {reorderData && (
        <div className="card" style={{ marginTop: '24px' }}>
          <div className="card-header">
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={20} color="#f59e0b" />
              Reorder Analysis
            </h3>
            <button className="btn" onClick={() => setReorderData(null)}>✕</button>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Current Stock</th>
                <th>Reorder Point</th>
                <th>Suggested Qty</th>
              </tr>
            </thead>
            <tbody>
              {(Array.isArray(reorderData) ? reorderData : []).map((item, i) => (
                <tr key={i}>
                  <td>{item.product_name}</td>
                  <td>
                    <span className="badge badge-danger">{item.current_stock}</span>
                  </td>
                  <td>{item.reorder_point}</td>
                  <td style={{ fontWeight: 600 }}>{item.suggested_qty}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && canWrite && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <div className="modal-header">
              <h3 className="modal-title">Create Purchase Order</h3>
              <button className="btn" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Supplier</label>
                <select
                  className="form-input"
                  value={formData.supplier_id}
                  onChange={(e) => setFormData({ ...formData, supplier_id: e.target.value })}
                  required
                >
                  <option value="">Select a supplier</option>
                  {suppliers.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Items</label>
                {formData.items.map((item, index) => (
                  <div key={index} style={{ display: 'flex', gap: '8px', marginBottom: '8px', alignItems: 'center' }}>
                    <select
                      className="form-input"
                      style={{ flex: 2 }}
                      value={item.product_id}
                      onChange={(e) => updateItem(index, 'product_id', e.target.value)}
                      required
                    >
                      <option value="">Select product</option>
                      {products.map(p => (
                        <option key={p.id} value={p.id}>{p.product_name}</option>
                      ))}
                    </select>
                    <input
                      type="number"
                      className="form-input"
                      style={{ flex: 1 }}
                      placeholder="Qty"
                      value={item.quantity}
                      onChange={(e) => updateItem(index, 'quantity', Number(e.target.value))}
                      min="1"
                      required
                    />
                    <input
                      type="number"
                      className="form-input"
                      style={{ flex: 1 }}
                      placeholder="Unit Price"
                      value={item.unit_price}
                      onChange={(e) => updateItem(index, 'unit_price', Number(e.target.value))}
                      min="0"
                      required
                    />
                    {formData.items.length > 1 && (
                      <button type="button" className="btn" style={{ padding: '6px', color: '#ef4444' }} onClick={() => removeItem(index)}>✕</button>
                    )}
                  </div>
                ))}
                <button type="button" className="btn btn-secondary" onClick={addItem} style={{ marginTop: '4px' }}>
                  <Plus size={16} style={{ marginRight: '4px' }} /> Add Item
                </button>
              </div>

              <div className="form-group">
                <label className="form-label">Notes</label>
                <textarea
                  name="notes"
                  className="form-input"
                  rows={3}
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>Create Purchase Order</button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default PurchaseOrders;
