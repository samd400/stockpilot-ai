import React, { useState, useEffect } from 'react';
import { Bell, AlertTriangle, DollarSign, CheckCircle, Filter, RefreshCw } from 'lucide-react';
import { alertsAPI } from '../services/api';

const severityStyle = {
  critical: { backgroundColor: '#fee2e2', color: '#991b1b' },
  warning:  { backgroundColor: '#fef3c7', color: '#92400e' },
  info:     { backgroundColor: '#dbeafe', color: '#1e40af' },
};

const FILTER_TABS = ['All', 'Unread', 'Low Stock', 'Price Alert', 'System'];

function getAlertIcon(type) {
  if (type === 'low_stock' || type === 'stock') return <AlertTriangle size={20} color="#f59e0b" />;
  if (type === 'price' || type === 'price_alert') return <DollarSign size={20} color="#2563eb" />;
  return <Bell size={20} color="#6366f1" />;
}

function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('All');

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await alertsAPI.getAll();
      setAlerts(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    try {
      await alertsAPI.generate();
      fetchAlerts();
    } catch (error) {
      console.error('Error generating alerts:', error);
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await alertsAPI.markRead(id);
      setAlerts(alerts.map(a => a.id === id ? { ...a, is_read: true } : a));
    } catch (error) {
      console.error('Error marking alert read:', error);
    }
  };

  const filteredAlerts = alerts.filter(alert => {
    if (activeTab === 'Unread') return !alert.is_read;
    if (activeTab === 'Low Stock') return alert.alert_type === 'low_stock' || alert.alert_type === 'stock';
    if (activeTab === 'Price Alert') return alert.alert_type === 'price' || alert.alert_type === 'price_alert';
    if (activeTab === 'System') return alert.alert_type === 'system';
    return true;
  });

  const stats = [
    { label: 'Total Alerts', value: alerts.length, icon: <Bell size={24} color="#2563eb" /> },
    { label: 'Unread', value: alerts.filter(a => !a.is_read).length, icon: <AlertTriangle size={24} color="#f59e0b" /> },
    { label: 'Critical', value: alerts.filter(a => a.severity === 'critical').length, icon: <AlertTriangle size={24} color="#ef4444" /> },
    { label: 'Resolved', value: alerts.filter(a => a.is_read).length, icon: <CheckCircle size={24} color="#22c55e" /> },
  ];

  if (loading) {
    return <div className="loading">Loading alerts...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">System Alerts</h1>
        <p style={{ color: '#64748b' }}>Monitor and manage system alerts</p>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <button className="btn btn-primary" onClick={handleGenerate}>
          <RefreshCw size={20} style={{ marginRight: '8px' }} />
          Generate Alerts
        </button>
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Filter size={16} color="#64748b" />
            {FILTER_TABS.map(tab => (
              <button
                key={tab}
                className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '6px 14px', fontSize: '13px' }}
                onClick={() => setActiveTab(tab)}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '16px' }}>
          {filteredAlerts.length === 0 && (
            <p style={{ color: '#64748b', textAlign: 'center', padding: '24px' }}>No alerts found.</p>
          )}
          {filteredAlerts.map(alert => (
            <div
              key={alert.id}
              className="card"
              style={{
                borderLeft: !alert.is_read ? '4px solid #2563eb' : '4px solid transparent',
                margin: 0,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '16px' }}>
                <div style={{ marginTop: '2px' }}>{getAlertIcon(alert.alert_type)}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <strong>{alert.title || alert.alert_type || 'Alert'}</strong>
                    <span
                      className="badge"
                      style={severityStyle[alert.severity] || severityStyle.info}
                    >
                      {alert.severity || 'info'}
                    </span>
                  </div>
                  <p style={{ color: '#475569', margin: '4px 0', fontSize: '14px' }}>{alert.message}</p>
                  <p style={{ color: '#94a3b8', fontSize: '12px', margin: 0 }}>
                    {alert.created_at ? new Date(alert.created_at).toLocaleString() : ''}
                  </p>
                </div>
                {!alert.is_read && (
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '6px 12px', fontSize: '12px', whiteSpace: 'nowrap' }}
                    onClick={() => handleMarkRead(alert.id)}
                  >
                    <CheckCircle size={14} style={{ marginRight: '4px' }} />
                    Mark Read
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Alerts;
