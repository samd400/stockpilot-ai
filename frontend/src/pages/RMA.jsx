import React, { useState, useEffect } from 'react';
import { RotateCcw, Plus, CheckCircle, XCircle, Package, Search } from 'lucide-react';
import { rmaAPI } from '../services/api';

const statusBadgeStyle = {
  pending:  { backgroundColor: '#fef3c7', color: '#92400e' },
  approved: { backgroundColor: '#dbeafe', color: '#1e40af' },
  rejected: { backgroundColor: '#fee2e2', color: '#991b1b' },
  received: { backgroundColor: '#dcfce7', color: '#166534' },
  refunded: { backgroundColor: '#ede9fe', color: '#6b21a8' },
};

const REASON_OPTIONS = ['Defective', 'Wrong Item', 'Damaged', 'Not as Described', 'Other'];

function RMA() {
  const [returns, setReturns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({
    product_id: '', invoice_id: '', reason: 'Defective', quantity: 1, notes: '',
  });

  useEffect(() => {
    fetchReturns();
  }, []);

  const fetchReturns = async () => {
    try {
      const response = await rmaAPI.getAll();
      setReturns(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error fetching RMAs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await rmaAPI.create(formData);
      fetchReturns();
      setShowModal(false);
      setFormData({ product_id: '', invoice_id: '', reason: 'Defective', quantity: 1, notes: '' });
    } catch (error) {
      console.error('Error creating RMA:', error);
    }
  };

  const handleAction = async (id, action) => {
    try {
      if (action === 'approve') await rmaAPI.approve(id);
      else if (action === 'reject') await rmaAPI.reject(id);
      else if (action === 'receive') await rmaAPI.receive(id);
      fetchReturns();
    } catch (error) {
      console.error(`Error ${action} RMA:`, error);
    }
  };

  const filteredReturns = returns.filter(r =>
    (r.id?.toString() || '').includes(searchTerm.toLowerCase()) ||
    (r.product_name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
    (r.customer_name?.toLowerCase() || '').includes(searchTerm.toLowerCase())
  );

  const stats = [
    { label: 'Total Returns', value: returns.length, icon: <RotateCcw size={24} color="#2563eb" /> },
    { label: 'Pending Approval', value: returns.filter(r => r.status === 'pending').length, icon: <Package size={24} color="#f59e0b" /> },
    { label: 'Approved', value: returns.filter(r => r.status === 'approved').length, icon: <CheckCircle size={24} color="#2563eb" /> },
    { label: 'Completed', value: returns.filter(r => r.status === 'received' || r.status === 'refunded').length, icon: <CheckCircle size={24} color="#22c55e" /> },
  ];

  if (loading) {
    return <div className="loading">Loading returns...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Returns / RMA</h1>
        <p style={{ color: '#64748b' }}>Manage product returns and RMA requests</p>
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
                placeholder="Search returns..."
                className="form-input"
                style={{ paddingLeft: '40px' }}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={20} style={{ marginRight: '8px' }} />
            Create Return
          </button>
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>RMA #</th>
              <th>Product</th>
              <th>Customer</th>
              <th>Reason</th>
              <th>Status</th>
              <th>Requested Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredReturns.map((rma) => (
              <tr key={rma.id}>
                <td style={{ fontFamily: 'monospace' }}>{rma.id?.toString().substring(0, 8) || '-'}</td>
                <td>{rma.product_name || rma.product_id || '-'}</td>
                <td>{rma.customer_name || '-'}</td>
                <td>{rma.reason || '-'}</td>
                <td>
                  <span className="badge" style={statusBadgeStyle[rma.status] || {}}>
                    {rma.status || 'pending'}
                  </span>
                </td>
                <td>{rma.created_at ? new Date(rma.created_at).toLocaleDateString() : '-'}</td>
                <td style={{ display: 'flex', gap: '4px' }}>
                  {rma.status === 'pending' && (
                    <>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '4px 8px', fontSize: '12px', color: '#22c55e' }}
                        onClick={() => handleAction(rma.id, 'approve')}
                      >
                        <CheckCircle size={14} style={{ marginRight: '4px' }} />
                        Approve
                      </button>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '4px 8px', fontSize: '12px', color: '#ef4444' }}
                        onClick={() => handleAction(rma.id, 'reject')}
                      >
                        <XCircle size={14} style={{ marginRight: '4px' }} />
                        Reject
                      </button>
                    </>
                  )}
                  {rma.status === 'approved' && (
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '4px 8px', fontSize: '12px' }}
                      onClick={() => handleAction(rma.id, 'receive')}
                    >
                      <Package size={14} style={{ marginRight: '4px' }} />
                      Mark Received
                    </button>
                  )}
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
              <h3 className="modal-title">Create Return</h3>
              <button className="btn" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Product ID</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.product_id}
                    onChange={(e) => setFormData({ ...formData, product_id: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Invoice ID</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.invoice_id}
                    onChange={(e) => setFormData({ ...formData, invoice_id: e.target.value })}
                  />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Reason</label>
                  <select
                    className="form-input"
                    value={formData.reason}
                    onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                    required
                  >
                    {REASON_OPTIONS.map(r => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Quantity</label>
                  <input
                    type="number"
                    className="form-input"
                    min="1"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 1 })}
                    required
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Notes</label>
                <textarea
                  className="form-input"
                  rows="3"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                ></textarea>
              </div>
              <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  Create Return
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

export default RMA;
