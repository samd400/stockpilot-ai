import React, { useState, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import { Package, FileText, TrendingUp, DollarSign, ShoppingCart, Users, AlertTriangle } from 'lucide-react';
import { dashboardAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [revenue, setRevenue] = useState(null);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { hasPermission } = useAuth();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [summaryRes, revenueRes, insightsRes] = await Promise.allSettled([
        dashboardAPI.getSummary(),
        dashboardAPI.getRevenue(),
        dashboardAPI.getInsights ? dashboardAPI.getInsights() : Promise.reject('no endpoint'),
      ]);
      if (summaryRes.status === 'fulfilled') setSummary(summaryRes.value.data);
      if (revenueRes.status === 'fulfilled') setRevenue(revenueRes.value.data);
      if (insightsRes.status === 'fulfilled') setInsights(insightsRes.value.data);
    } catch (err) {
      setError('Failed to load dashboard data.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const stats = [
    { label: 'Total Products', value: summary?.total_products || 0, icon: Package, color: '#2563eb' },
    { label: 'Stock Value', value: `₹${(summary?.total_stock_value || 0).toLocaleString()}`, icon: DollarSign, color: '#7c3aed' },
    { label: 'Total Invoices', value: summary?.total_invoices || 0, icon: FileText, color: '#059669' },
    { label: 'Revenue Today', value: `₹${(summary?.revenue_today || 0).toLocaleString()}`, icon: TrendingUp, color: '#dc2626' },
  ];

  const monthlyBreakdown = revenue?.monthly_breakdown || [];
  const salesData = {
    labels: monthlyBreakdown.map(m => m.month),
    datasets: [{
      label: 'Revenue',
      data: monthlyBreakdown.map(m => m.revenue),
      backgroundColor: '#2563eb',
    }],
  };

  const topSelling = insights?.top_selling_products || [];
  const topSellingData = {
    labels: topSelling.map(p => p.product_name),
    datasets: [{
      data: topSelling.map(p => p.units_sold),
      backgroundColor: ['#2563eb', '#7c3aed', '#059669', '#f59e0b', '#dc2626'],
    }],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'top' } },
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p style={{ color: '#64748b' }}>Welcome to StockPilot — Your AI-powered retail management system</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

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

      {summary?.low_stock_products > 0 && (
        <div className="alert alert-error" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px' }}>
          <AlertTriangle size={20} />
          <span><strong>{summary.low_stock_products}</strong> products are low on stock (below 5 units).</span>
          <button className="btn btn-secondary" style={{ marginLeft: 'auto', padding: '4px 12px' }} onClick={() => navigate('/inventory')}>
            View Inventory
          </button>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Monthly Revenue</h3>
          </div>
          <div style={{ height: '300px' }}>
            {monthlyBreakdown.length > 0 ? (
              <Bar data={salesData} options={chartOptions} />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b' }}>
                No revenue data yet. Create invoices to see trends.
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Top Selling Products</h3>
          </div>
          <div style={{ height: '300px', display: 'flex', justifyContent: 'center' }}>
            {topSelling.length > 0 ? (
              <Doughnut data={topSellingData} options={chartOptions} />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b' }}>
                No sales data yet.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Revenue Summary */}
      {revenue && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Revenue Overview</h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
            <div style={{ textAlign: 'center', padding: '16px' }}>
              <p className="stat-label">All Time Revenue</p>
              <p className="stat-value">₹{(revenue.total_revenue_all_time || 0).toLocaleString()}</p>
            </div>
            <div style={{ textAlign: 'center', padding: '16px' }}>
              <p className="stat-label">This Month</p>
              <p className="stat-value">₹{(revenue.revenue_this_month || 0).toLocaleString()}</p>
            </div>
            <div style={{ textAlign: 'center', padding: '16px' }}>
              <p className="stat-label">Today</p>
              <p className="stat-value">₹{(revenue.revenue_today || 0).toLocaleString()}</p>
            </div>
          </div>
        </div>
      )}

      {/* Low Stock Products */}
      {insights?.low_stock_products?.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={20} color="#f59e0b" />
              Low Stock Products
            </h3>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Stock</th>
              </tr>
            </thead>
            <tbody>
              {insights.low_stock_products.map((p, i) => (
                <tr key={i}>
                  <td>{p.product_name}</td>
                  <td><span className="badge badge-danger">{p.stock_quantity}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {(hasPermission('inventory_write') || hasPermission('billing_write') || hasPermission('crm_write') || hasPermission('billing')) && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Quick Actions</h3>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px' }}>
            {hasPermission('inventory_write') && (
              <button className="btn btn-primary" style={{ padding: '16px', flex: '1 1 140px' }} onClick={() => navigate('/products')}>
                <Package size={20} style={{ marginRight: '8px' }} />
                Add Product
              </button>
            )}
            {hasPermission('billing_write') && (
              <button className="btn btn-primary" style={{ padding: '16px', flex: '1 1 140px' }} onClick={() => navigate('/invoices')}>
                <FileText size={20} style={{ marginRight: '8px' }} />
                Create Invoice
              </button>
            )}
            {hasPermission('crm_write') && (
              <button className="btn btn-primary" style={{ padding: '16px', flex: '1 1 140px' }} onClick={() => navigate('/customers')}>
                <Users size={20} style={{ marginRight: '8px' }} />
                Add Customer
              </button>
            )}
            {hasPermission('billing') && (
              <button className="btn btn-primary" style={{ padding: '16px', flex: '1 1 140px' }} onClick={() => navigate('/pos')}>
                <ShoppingCart size={20} style={{ marginRight: '8px' }} />
                POS Billing
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
