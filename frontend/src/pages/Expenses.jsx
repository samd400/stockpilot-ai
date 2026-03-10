import React, { useState, useEffect } from 'react';
import { Receipt, Plus, Search, Edit, Trash2, DollarSign, Calendar } from 'lucide-react';
import { expensesAPI } from '../services/api';

const CATEGORIES = ['Rent', 'Salary', 'Utilities', 'Supplies', 'Marketing', 'Transport', 'Other'];
const PAYMENT_MODES = ['Cash', 'Bank', 'UPI'];

function Expenses() {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    description: '',
    amount: '',
    category: 'Other',
    payment_mode: 'Cash',
    date: new Date().toISOString().split('T')[0],
    notes: '',
  });

  useEffect(() => {
    fetchExpenses();
  }, []);

  const fetchExpenses = async () => {
    try {
      const response = await expensesAPI.getAll();
      setExpenses(response.data);
    } catch (error) {
      console.error('Error fetching expenses:', error);
      setExpenses([]);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const openCreateModal = () => {
    setEditingId(null);
    setFormData({ description: '', amount: '', category: 'Other', payment_mode: 'Cash', date: new Date().toISOString().split('T')[0], notes: '' });
    setShowModal(true);
  };

  const openEditModal = (expense) => {
    setEditingId(expense.id);
    setFormData({
      description: expense.description || '',
      amount: expense.amount || '',
      category: expense.category || 'Other',
      payment_mode: expense.payment_mode || 'Cash',
      date: expense.date ? expense.date.split('T')[0] : new Date().toISOString().split('T')[0],
      notes: expense.notes || '',
    });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await expensesAPI.update(editingId, formData);
      } else {
        await expensesAPI.create(formData);
      }
      fetchExpenses();
      setShowModal(false);
    } catch (error) {
      console.error('Error saving expense:', error);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this expense?')) {
      try {
        await expensesAPI.delete(id);
        fetchExpenses();
      } catch (error) {
        console.error('Error deleting expense:', error);
        setExpenses(expenses.filter(exp => exp.id !== id));
      }
    }
  };

  const now = new Date();
  const thisMonthExpenses = expenses.filter(exp => {
    const d = new Date(exp.date || exp.created_at);
    return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
  });
  const monthlyTotal = thisMonthExpenses.reduce((sum, exp) => sum + (parseFloat(exp.amount) || 0), 0);

  // Top 3 categories by total amount
  const categoryTotals = {};
  thisMonthExpenses.forEach(exp => {
    const cat = exp.category || 'Other';
    categoryTotals[cat] = (categoryTotals[cat] || 0) + (parseFloat(exp.amount) || 0);
  });
  const topCategories = Object.entries(categoryTotals)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);

  const filteredExpenses = expenses.filter(exp =>
    (exp.description?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
    (exp.category?.toLowerCase() || '').includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <div className="loading">Loading expenses...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Expenses</h1>
        <p style={{ color: '#64748b' }}>Track and manage your business expenses</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <DollarSign size={24} color="#ef4444" />
            <div>
              <p className="stat-label">Total Expenses (This Month)</p>
              <p className="stat-value">₹{monthlyTotal.toLocaleString()}</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Calendar size={24} color="#2563eb" />
            <div>
              <p className="stat-label">Transactions This Month</p>
              <p className="stat-value">{thisMonthExpenses.length}</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Receipt size={24} color="#8b5cf6" />
            <div>
              <p className="stat-label">Top Categories</p>
              <p className="stat-value" style={{ fontSize: '14px' }}>
                {topCategories.length > 0
                  ? topCategories.map(([cat, amt]) => `${cat}: ₹${amt.toLocaleString()}`).join(', ')
                  : 'No data'}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
            <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
              <Search size={20} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
              <input
                type="text"
                placeholder="Search expenses..."
                className="form-input"
                style={{ paddingLeft: '40px' }}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <button className="btn btn-primary" onClick={openCreateModal}>
            <Plus size={20} style={{ marginRight: '8px' }} />
            Add Expense
          </button>
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Description</th>
              <th>Category</th>
              <th>Amount</th>
              <th>Payment Mode</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredExpenses.map((expense) => (
              <tr key={expense.id}>
                <td>{expense.date ? new Date(expense.date).toLocaleDateString() : '-'}</td>
                <td>{expense.description || '-'}</td>
                <td>
                  <span className="badge badge-warning">{expense.category || 'Other'}</span>
                </td>
                <td>₹{(parseFloat(expense.amount) || 0).toLocaleString()}</td>
                <td>{expense.payment_mode || '-'}</td>
                <td>
                  <button className="btn" style={{ padding: '6px', marginRight: '4px' }} onClick={() => openEditModal(expense)}>
                    <Edit size={16} />
                  </button>
                  <button className="btn" style={{ padding: '6px', color: '#ef4444' }} onClick={() => handleDelete(expense.id)}>
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan="3" style={{ fontWeight: 600, textAlign: 'right' }}>Monthly Total:</td>
              <td style={{ fontWeight: 700 }}>₹{monthlyTotal.toLocaleString()}</td>
              <td colSpan="2"></td>
            </tr>
          </tfoot>
        </table>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">{editingId ? 'Edit Expense' : 'Add New Expense'}</h3>
              <button className="btn" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Description</label>
                <input
                  type="text"
                  name="description"
                  className="form-input"
                  value={formData.description}
                  onChange={handleChange}
                  required
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Amount</label>
                  <input
                    type="number"
                    name="amount"
                    className="form-input"
                    value={formData.amount}
                    onChange={handleChange}
                    min="0"
                    step="0.01"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Category</label>
                  <select
                    name="category"
                    className="form-input"
                    value={formData.category}
                    onChange={handleChange}
                  >
                    {CATEGORIES.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Payment Mode</label>
                  <select
                    name="payment_mode"
                    className="form-input"
                    value={formData.payment_mode}
                    onChange={handleChange}
                  >
                    {PAYMENT_MODES.map(mode => (
                      <option key={mode} value={mode}>{mode}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Date</label>
                  <input
                    type="date"
                    name="date"
                    className="form-input"
                    value={formData.date}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Notes</label>
                <textarea
                  name="notes"
                  className="form-input"
                  rows="3"
                  value={formData.notes}
                  onChange={handleChange}
                ></textarea>
              </div>
              <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  {editingId ? 'Update Expense' : 'Add Expense'}
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

export default Expenses;
