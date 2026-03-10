import React, { useState, useEffect } from 'react';
import { ClipboardList, Plus, Search, Truck, CheckCircle, Clock, Filter } from 'lucide-react';
import { ordersAPI, productsAPI, customersAPI } from '../services/api';

const STATUS_OPTIONS = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled'];

const statusBadgeStyle = {
  pending:    { backgroundColor: '#fef3c7', color: '#92400e' },
  confirmed:  { backgroundColor: '#dbeafe', color: '#1e40af' },
  processing: { backgroundColor: '#e0e7ff', color: '#3730a3' },
  shipped:    { backgroundColor: '#ede9fe', color: '#6b21a8' },
  delivered:  { backgroundColor: '#dcfce7', color: '#166534' },
  cancelled:  { backgroundColor: '#fee2e2', color: '#991b1b' },
};

function Orders() {
  const [orders, setOrders] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [formData, setFormData] = useState({ customer_id: '', items: [{ product_id: '', quantity: 1 }], notes: '' });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [ordersRes, customersRes, productsRes] = await Promise.allSettled([
        ordersAPI.getAll(),
        customersAPI.getAll(),
        productsAPI.getAll(),
      ]);
      setOrders(ordersRes.status === 'fulfilled' ? ordersRes.value.data : []);
      setCustomers(customersRes.status === 'fulfilled' ? customersRes.value.data : []);
      setProducts(productsRes.status === 'fulfilled' ? productsRes.value.data : []);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (id, newStatus) => {
    try {
      await ordersAPI.updateStatus(id, { status: newStatus });
      fetchData();
    } catch (error) {
      console.error('Error updating status:', error);
      setOrders(orders.map(o => o.id === id ? { ...o, status: newStatus } : o));
    }
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index] = { ...newItems[index], [field]: value };
    setFormData({ ...formData, items: newItems });
  };

  const addItem = () => {
    setFormData({ ...formData, items: [...formData.items, { product_id: '', quantity: 1 }] });
  };

  const removeItem = (index) => {
    if (formData.items.length > 1) {
      setFormData({ ...formData, items: formData.items.filter((_, i) => i !== index) });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await ordersAPI.create(formData);
      fetchData();
      setShowModal(false);
      setFormData({ customer_id: '', items: [{ product_id: '', quantity: 1 }], notes: '' });
    } catch (error) {
      console.error('Error creating order:', error);
    }
  };

  const stats = [
    { label: 'Total Orders', value: orders.length, icon: <ClipboardList size={24} color="#2563eb" /> },
    { label: 'Pending', value: orders.filter(o => o.status === 'pending').length, icon: <Clock size={24} color="#f59e0b" /> },
    { label: 'Processing', value: orders.filter(o => o.status === 'processing').length, icon: <Truck size={24} color="#6366f1" /> },
    { label: 'Delivered', value: orders.filter(o => o.status === 'delivered').length, icon: <CheckCircle size={24} color="#22c55e" /> },
  ];

  const filteredOrders = orders.filter(order => {
    const matchesSearch =
      (order.id?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
      (order.customer_name?.toLowerCase() || '').includes(searchTerm.toLowerCase());
    const matchesStatus = !statusFilter || order.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return <div className="loading">Loading orders...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Orders</h1>
        <p style={{ color: '#64748b' }}>Manage storefront and online orders</p>
      </div>

      <div className="stats-grid">
        {stats.map((stat, index) => (
          <div key={index} className="stat-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {stat.icon}
              <div>
                <p className="stat-label">{stat.label}</p>
                <p className="stat-value">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
            <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
              <Search size={20} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
              <input
                type="text"
                placeholder="Search orders..."
                className="form-input"
                style={{ paddingLeft: '40px' }}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div style={{ position: 'relative' }}>
              <Filter size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
              <select
                className="form-input"
                style={{ paddingLeft: '32px', minWidth: '160px' }}
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All Statuses</option>
                {STATUS_OPTIONS.map(s => (
                  <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                ))}
              </select>
            </div>
          </div>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={20} style={{ marginRight: '8px' }} />
            Create Order
          </button>
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Customer</th>
              <th>Items</th>
              <th>Total Amount</th>
              <th>Status</th>
              <th>Payment Status</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredOrders.map((order) => (
              <tr key={order.id}>
                <td style={{ fontFamily: 'monospace' }}>{order.id?.substring(0, 8) || '-'}</td>
                <td>{order.customer_name || '-'}</td>
                <td>{order.items?.length || 0}</td>
                <td>₹{(order.total_amount || 0).toLocaleString()}</td>
                <td>
                  <span
                    className="badge"
                    style={statusBadgeStyle[order.status] || {}}
                  >
                    {order.status || 'pending'}
                  </span>
                </td>
                <td>
                  <span className={`badge ${order.payment_status === 'paid' ? 'badge-success' : 'badge-warning'}`}>
                    {order.payment_status || 'unpaid'}
                  </span>
                </td>
                <td>{order.created_at ? new Date(order.created_at).toLocaleDateString() : '-'}</td>
                <td>
                  <select
                    className="form-input"
                    style={{ padding: '4px 8px', fontSize: '12px', minWidth: '120px' }}
                    value={order.status || 'pending'}
                    onChange={(e) => handleStatusChange(order.id, e.target.value)}
                  >
                    {STATUS_OPTIONS.map(s => (
                      <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Create New Order</h3>
              <button className="btn" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Customer</label>
                <select
                  name="customer_id"
                  className="form-input"
                  value={formData.customer_id}
                  onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                  required
                >
                  <option value="">Select Customer</option>
                  {customers.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
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
                      onChange={(e) => handleItemChange(index, 'product_id', e.target.value)}
                      required
                    >
                      <option value="">Select Product</option>
                      {products.map(p => (
                        <option key={p.id} value={p.id}>{p.product_name}</option>
                      ))}
                    </select>
                    <input
                      type="number"
                      className="form-input"
                      style={{ flex: 1 }}
                      min="1"
                      placeholder="Qty"
                      value={item.quantity}
                      onChange={(e) => handleItemChange(index, 'quantity', parseInt(e.target.value) || 1)}
                      required
                    />
                    {formData.items.length > 1 && (
                      <button type="button" className="btn" style={{ padding: '6px', color: '#ef4444' }} onClick={() => removeItem(index)}>✕</button>
                    )}
                  </div>
                ))}
                <button type="button" className="btn btn-secondary" style={{ fontSize: '13px' }} onClick={addItem}>
                  <Plus size={16} style={{ marginRight: '4px' }} /> Add Item
                </button>
              </div>

              <div className="form-group">
                <label className="form-label">Notes</label>
                <textarea
                  name="notes"
                  className="form-input"
                  rows="3"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                ></textarea>
              </div>

              <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  Create Order
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Orders;
