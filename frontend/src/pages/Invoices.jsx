import React, { useState, useEffect } from 'react';
import { FileText, Plus, Search, Download, Eye } from 'lucide-react';
import { invoicesAPI, productsAPI, customersAPI } from '../services/api';

function Invoices() {
  const [invoices, setInvoices] = useState([]);
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_phone: '',
    items: [{ product_id: '', quantity: 1 }],
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [invRes, prodRes, custRes] = await Promise.allSettled([
        invoicesAPI.getAll(),
        productsAPI.getAll(),
        customersAPI.getAll(),
      ]);
      if (invRes.status === 'fulfilled') setInvoices(invRes.value.data);
      if (prodRes.status === 'fulfilled') setProducts(prodRes.value.data);
      if (custRes.status === 'fulfilled') setCustomers(custRes.value.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewPDF = async (id) => {
    try {
      const response = await invoicesAPI.getPDF(id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `invoice-${id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Failed to download PDF');
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
      await invoicesAPI.create(formData);
      fetchData();
      setShowModal(false);
      setFormData({ customer_name: '', customer_phone: '', items: [{ product_id: '', quantity: 1 }] });
    } catch (error) {
      console.error('Error creating invoice:', error);
      alert(error.response?.data?.detail || 'Failed to create invoice');
    }
  };

  const selectCustomer = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    if (customer) {
      setFormData({ ...formData, customer_name: customer.name, customer_phone: customer.phone_number || '' });
    }
  };

  const filteredInvoices = invoices.filter(invoice =>
    invoice.invoice_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    invoice.customer_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <div className="loading">Loading invoices...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Invoices</h1>
        <p style={{ color: '#64748b' }}>Manage GST-compliant invoices</p>
      </div>

      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
            <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
              <Search size={20} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
              <input
                type="text"
                placeholder="Search invoices..."
                className="form-input"
                style={{ paddingLeft: '40px' }}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={20} style={{ marginRight: '8px' }} />
            Create Invoice
          </button>
        </div>

        {filteredInvoices.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 0', color: '#64748b' }}>
            <FileText size={48} style={{ marginBottom: '16px', opacity: 0.4 }} />
            <p>No invoices found. Create your first invoice.</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Invoice Number</th>
                <th>Customer</th>
                <th>Amount</th>
                <th>GST</th>
                <th>Date</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredInvoices.map((invoice) => (
                <tr key={invoice.id}>
                  <td style={{ fontWeight: 600 }}>{invoice.invoice_number}</td>
                  <td>{invoice.customer_name || '-'}</td>
                  <td>₹{(invoice.total_amount || 0).toLocaleString()}</td>
                  <td>₹{(invoice.gst_amount || 0).toLocaleString()}</td>
                  <td>{invoice.created_at ? new Date(invoice.created_at).toLocaleDateString() : '-'}</td>
                  <td>
                    <span className={`badge ${invoice.status === 'PAID' ? 'badge-success' : 'badge-warning'}`}>
                      {invoice.status || 'PENDING'}
                    </span>
                  </td>
                  <td>
                    <button className="btn" style={{ padding: '6px', marginRight: '4px' }} title="View">
                      <Eye size={16} />
                    </button>
                    <button className="btn" style={{ padding: '6px' }} onClick={() => handleViewPDF(invoice.id)} title="Download PDF">
                      <Download size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <div className="modal-header">
              <h3 className="modal-title">Create New Invoice</h3>
              <button className="btn" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Select Customer</label>
                <select className="form-input" onChange={(e) => selectCustomer(e.target.value)}>
                  <option value="">Select existing customer (optional)</option>
                  {customers.map(c => (
                    <option key={c.id} value={c.id}>{c.name} {c.phone_number ? `(${c.phone_number})` : ''}</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Customer Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.customer_name}
                    onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Phone (optional)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.customer_phone}
                    onChange={(e) => setFormData({ ...formData, customer_phone: e.target.value })}
                  />
                </div>
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
                      <option value="">Select product</option>
                      {products.map(p => (
                        <option key={p.id} value={p.id}>{p.product_name} (₹{p.selling_price} • Stock: {p.stock_quantity})</option>
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
                <button type="button" className="btn btn-secondary" onClick={addItem} style={{ marginTop: '4px' }}>
                  <Plus size={16} style={{ marginRight: '4px' }} /> Add Item
                </button>
              </div>

              <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  Create Invoice
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

export default Invoices;
