import React, { useState, useEffect } from 'react';
import { Truck, Plus, Search, Star, Mail, Phone, Clock } from 'lucide-react';
import { suppliersAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

function Suppliers() {
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('inventory_write');
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    contact_email: '',
    phone: '',
    lead_time_days: 7,
    min_order_qty: 1,
    currency: 'INR',
    preferred: false,
  });

  useEffect(() => {
    fetchSuppliers();
  }, []);

  const fetchSuppliers = async () => {
    try {
      const response = await suppliersAPI.getAll();
      setSuppliers(response.data);
    } catch (error) {
      console.error('Error fetching suppliers:', error);
      setSuppliers([
        { id: '1', name: 'Acme Supplies', contact_email: 'sales@acme.com', phone: '+91-9876543210', lead_time_days: 5, min_order_qty: 10, currency: 'INR', preferred: true },
        { id: '2', name: 'Global Parts Ltd', contact_email: 'orders@globalparts.com', phone: '+91-9876543211', lead_time_days: 14, min_order_qty: 50, currency: 'USD', preferred: false },
        { id: '3', name: 'Quick Ship Co', contact_email: 'info@quickship.com', phone: '+91-9876543212', lead_time_days: 3, min_order_qty: 5, currency: 'INR', preferred: true },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await suppliersAPI.create({
        ...formData,
        lead_time_days: Number(formData.lead_time_days),
        min_order_qty: Number(formData.min_order_qty),
      });
      fetchSuppliers();
      setShowModal(false);
      setFormData({ name: '', contact_email: '', phone: '', lead_time_days: 7, min_order_qty: 1, currency: 'INR', preferred: false });
    } catch (error) {
      console.error('Error creating supplier:', error);
      setSuppliers([...suppliers, { ...formData, id: Date.now().toString(), lead_time_days: Number(formData.lead_time_days), min_order_qty: Number(formData.min_order_qty) }]);
      setShowModal(false);
    }
  };

  const filteredSuppliers = suppliers.filter(s =>
    s.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.contact_email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalSuppliers = suppliers.length;
  const preferredSuppliers = suppliers.filter(s => s.preferred).length;

  const stats = [
    { label: 'Total Suppliers', value: totalSuppliers, icon: Truck, color: '#2563eb' },
    { label: 'Preferred Suppliers', value: preferredSuppliers, icon: Star, color: '#f59e0b' },
    { label: 'Active POs', value: 0, icon: Clock, color: '#059669' },
  ];

  if (loading) {
    return <div className="loading">Loading suppliers...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Suppliers</h1>
        <p style={{ color: '#64748b' }}>Manage your supplier network</p>
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
                placeholder="Search suppliers..."
                className="form-input"
                style={{ paddingLeft: '40px' }}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          {canWrite && (
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>
              <Plus size={20} style={{ marginRight: '8px' }} />
              Add Supplier
            </button>
          )}
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>Supplier Name</th>
              <th>Contact Email</th>
              <th>Phone</th>
              <th>Lead Time (days)</th>
              <th>Min Order Qty</th>
              <th>Currency</th>
              <th>Preferred</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredSuppliers.map((supplier) => (
              <tr key={supplier.id}>
                <td>{supplier.name}</td>
                <td>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Mail size={14} color="#64748b" />
                    {supplier.contact_email || '-'}
                  </span>
                </td>
                <td>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Phone size={14} color="#64748b" />
                    {supplier.phone || '-'}
                  </span>
                </td>
                <td>{supplier.lead_time_days ?? '-'}</td>
                <td>{supplier.min_order_qty ?? '-'}</td>
                <td>{supplier.currency || 'INR'}</td>
                <td>
                  {supplier.preferred ? (
                    <span className="badge badge-warning" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <Star size={12} /> Preferred
                    </span>
                  ) : (
                    <span className="badge">—</span>
                  )}
                </td>
                <td>
                  <button className="btn" style={{ padding: '6px' }} onClick={() => {}}>
                    Edit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && canWrite && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Add New Supplier</h3>
              <button className="btn" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Supplier Name</label>
                <input type="text" name="name" className="form-input" value={formData.name} onChange={handleChange} required />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Contact Email</label>
                  <input type="email" name="contact_email" className="form-input" value={formData.contact_email} onChange={handleChange} />
                </div>
                <div className="form-group">
                  <label className="form-label">Phone</label>
                  <input type="text" name="phone" className="form-input" value={formData.phone} onChange={handleChange} />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Lead Time (days)</label>
                  <input type="number" name="lead_time_days" className="form-input" value={formData.lead_time_days} onChange={handleChange} min="1" required />
                </div>
                <div className="form-group">
                  <label className="form-label">Min Order Qty</label>
                  <input type="number" name="min_order_qty" className="form-input" value={formData.min_order_qty} onChange={handleChange} min="1" required />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Currency</label>
                  <select name="currency" className="form-input" value={formData.currency} onChange={handleChange}>
                    <option value="INR">INR</option>
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                    <option value="AED">AED</option>
                    <option value="SAR">SAR</option>
                  </select>
                </div>
                <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '8px', paddingTop: '28px' }}>
                  <input type="checkbox" name="preferred" checked={formData.preferred} onChange={handleChange} id="preferred-check" />
                  <label htmlFor="preferred-check" className="form-label" style={{ margin: 0 }}>Preferred Supplier</label>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>Add Supplier</button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Suppliers;
