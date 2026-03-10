import React, { useState, useEffect } from 'react';
import { Tags, Plus, TrendingUp, TrendingDown, DollarSign, Zap, CheckCircle } from 'lucide-react';
import { pricingAPI } from '../services/api';

const ruleTypeBadge = {
  discount:   { backgroundColor: '#dcfce7', color: '#166534' },
  markup:     { backgroundColor: '#fef3c7', color: '#92400e' },
  time_based: { backgroundColor: '#dbeafe', color: '#1e40af' },
};

function Pricing() {
  const [rules, setRules] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '', rule_type: 'discount', product_id: '', value: '', conditions: '', active: true,
  });

  const handleCreateRule = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        value: parseFloat(formData.value) || 0,
        conditions: formData.conditions ? JSON.parse(formData.conditions) : {},
      };
      await pricingAPI.createRule(payload);
      setShowModal(false);
      setFormData({ name: '', rule_type: 'discount', product_id: '', value: '', conditions: '', active: true });
    } catch (error) {
      console.error('Error creating rule:', error);
    }
  };

  const handleGetRecommendations = async () => {
    setLoading(true);
    try {
      const response = await pricingAPI.getRecommendations();
      setRecommendations(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async (productId) => {
    try {
      await pricingAPI.apply(productId);
      setRecommendations(recommendations.filter(r => r.product_id !== productId));
    } catch (error) {
      console.error('Error applying recommendation:', error);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Dynamic Pricing</h1>
        <p style={{ color: '#64748b' }}>Manage pricing rules and recommendations</p>
      </div>

      {/* Pricing Rules */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Tags size={20} color="#2563eb" />
            <h3 style={{ margin: 0 }}>Pricing Rules</h3>
          </div>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={20} style={{ marginRight: '8px' }} />
            Add Rule
          </button>
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>Rule Name</th>
              <th>Type</th>
              <th>Product / Category</th>
              <th>Value</th>
              <th>Active</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rules.length === 0 && (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', color: '#64748b', padding: '24px' }}>
                  No pricing rules yet. Click "Add Rule" to create one.
                </td>
              </tr>
            )}
            {rules.map((rule, idx) => (
              <tr key={rule.id || idx}>
                <td>{rule.name}</td>
                <td>
                  <span className="badge" style={ruleTypeBadge[rule.rule_type] || {}}>
                    {rule.rule_type}
                  </span>
                </td>
                <td>{rule.product_id || rule.category || '-'}</td>
                <td>{rule.value}%</td>
                <td>
                  <span className={`badge ${rule.active ? 'badge-success' : 'badge-danger'}`}>
                    {rule.active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>-</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Price Recommendations */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={20} color="#f59e0b" />
            <h3 style={{ margin: 0 }}>Price Recommendations</h3>
          </div>
          <button className="btn btn-primary" onClick={handleGetRecommendations} disabled={loading}>
            <TrendingUp size={20} style={{ marginRight: '8px' }} />
            {loading ? 'Loading...' : 'Get Recommendations'}
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px', padding: '16px' }}>
          {recommendations.length === 0 && (
            <p style={{ color: '#64748b', padding: '8px' }}>
              Click "Get Recommendations" to fetch AI-powered pricing suggestions.
            </p>
          )}
          {recommendations.map((rec, idx) => {
            const changePercent = rec.current_price
              ? (((rec.recommended_price - rec.current_price) / rec.current_price) * 100).toFixed(1)
              : 0;
            const isIncrease = parseFloat(changePercent) >= 0;
            return (
              <div key={rec.product_id || idx} className="card" style={{ margin: 0 }}>
                <div style={{ padding: '16px' }}>
                  <h4 style={{ margin: '0 0 8px 0' }}>{rec.product_name || `Product ${rec.product_id}`}</h4>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <div>
                      <p className="stat-label">Current Price</p>
                      <p style={{ fontWeight: 600, margin: 0 }}>₹{(rec.current_price || 0).toLocaleString()}</p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <p className="stat-label">Recommended</p>
                      <p style={{ fontWeight: 600, margin: 0, color: '#2563eb' }}>₹{(rec.recommended_price || 0).toLocaleString()}</p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '8px' }}>
                    {isIncrease ? <TrendingUp size={16} color="#22c55e" /> : <TrendingDown size={16} color="#ef4444" />}
                    <span style={{ color: isIncrease ? '#22c55e' : '#ef4444', fontWeight: 600, fontSize: '14px' }}>
                      {changePercent}%
                    </span>
                  </div>
                  {rec.reason && (
                    <p style={{ color: '#64748b', fontSize: '13px', margin: '0 0 12px 0' }}>{rec.reason}</p>
                  )}
                  <button
                    className="btn btn-primary"
                    style={{ width: '100%', fontSize: '13px' }}
                    onClick={() => handleApply(rec.product_id)}
                  >
                    <CheckCircle size={14} style={{ marginRight: '4px' }} />
                    Apply
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Add Rule Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Add Pricing Rule</h3>
              <button className="btn" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateRule}>
              <div className="form-group">
                <label className="form-label">Rule Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Rule Type</label>
                  <select
                    className="form-input"
                    value={formData.rule_type}
                    onChange={(e) => setFormData({ ...formData, rule_type: e.target.value })}
                  >
                    <option value="discount">Discount</option>
                    <option value="markup">Markup</option>
                    <option value="time_based">Time Based</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Product ID</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.product_id}
                    onChange={(e) => setFormData({ ...formData, product_id: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Value (%)</label>
                <input
                  type="number"
                  className="form-input"
                  value={formData.value}
                  onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Conditions (JSON)</label>
                <textarea
                  className="form-input"
                  rows="3"
                  placeholder='{"min_quantity": 10}'
                  value={formData.conditions}
                  onChange={(e) => setFormData({ ...formData, conditions: e.target.value })}
                ></textarea>
              </div>
              <div className="form-group">
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input
                    type="checkbox"
                    checked={formData.active}
                    onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                  />
                  Active
                </label>
              </div>
              <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  Create Rule
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

export default Pricing;
