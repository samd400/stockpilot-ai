import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import { BarChart3, TrendingUp, TrendingDown, DollarSign, Package, AlertTriangle } from 'lucide-react';
import { analyticsAPI } from '../services/api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler);

function Analytics() {
  const [salesTrend, setSalesTrend] = useState(null);
  const [topProducts, setTopProducts] = useState([]);
  const [profitLoss, setProfitLoss] = useState(null);
  const [summary, setSummary] = useState(null);
  const [stockPredictions, setStockPredictions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      const results = await Promise.allSettled([
        analyticsAPI.getSalesTrend(),
        analyticsAPI.getTopProducts(),
        analyticsAPI.getProfitLossTrend(),
        analyticsAPI.getBusinessSummary(),
        analyticsAPI.getStockPrediction(),
      ]);

      const [salesRes, productsRes, plRes, summaryRes, stockRes] = results;

      if (salesRes.status === 'fulfilled') {
        const d = salesRes.value.data;
        setSalesTrend({ labels: d.labels || d.months || [], data: d.data || d.sales || [] });
      }

      if (productsRes.status === 'fulfilled') {
        setTopProducts((productsRes.value.data.products || productsRes.value.data || []).slice(0, 10));
      }

      if (plRes.status === 'fulfilled') {
        const d = plRes.value.data;
        setProfitLoss({ labels: d.labels || d.months || [], revenue: d.revenue || [], expenses: d.expenses || d.costs || [] });
      }

      if (summaryRes.status === 'fulfilled') {
        setSummary(summaryRes.value.data);
      }

      if (stockRes.status === 'fulfilled') {
        setStockPredictions(stockRes.value.data.predictions || stockRes.value.data || []);
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading analytics...</div>;
  }

  const salesChartData = {
    labels: salesTrend?.labels || [],
    datasets: [{
      label: 'Sales',
      data: salesTrend?.data || [],
      borderColor: '#2563eb',
      backgroundColor: 'rgba(37, 99, 235, 0.1)',
      fill: true,
      tension: 0.4,
    }],
  };

  const topProductsData = {
    labels: topProducts.map(p => p.name || p.product_name),
    datasets: [{
      label: 'Revenue',
      data: topProducts.map(p => p.revenue),
      backgroundColor: [
        '#2563eb', '#7c3aed', '#059669', '#dc2626', '#f59e0b',
        '#0891b2', '#4f46e5', '#be185d', '#15803d', '#b45309',
      ],
    }],
  };

  const profitLossData = {
    labels: profitLoss?.labels || [],
    datasets: [
      {
        label: 'Revenue',
        data: profitLoss?.revenue || [],
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Expenses',
        data: profitLoss?.expenses || [],
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'top' } },
  };

  const barOptions = {
    ...chartOptions,
    indexAxis: 'y',
  };

  const summaryStats = [
    { label: 'Total Revenue', value: `₹${(summary?.total_revenue || 0).toLocaleString()}`, icon: DollarSign, color: '#2563eb' },
    { label: 'Total Profit', value: `₹${(summary?.total_profit || 0).toLocaleString()}`, icon: TrendingUp, color: '#22c55e' },
    { label: 'Avg Order Value', value: `₹${(summary?.avg_order_value || 0).toLocaleString()}`, icon: BarChart3, color: '#7c3aed' },
    {
      label: 'Growth',
      value: `${summary?.growth_percent > 0 ? '+' : ''}${summary?.growth_percent || 0}%`,
      icon: summary?.growth_percent >= 0 ? TrendingUp : TrendingDown,
      color: summary?.growth_percent >= 0 ? '#22c55e' : '#ef4444',
    },
  ];

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Analytics</h1>
        <p style={{ color: '#64748b' }}>Business performance insights and predictions</p>
      </div>

      {/* Row 1: Summary Cards */}
      <div className="stats-grid">
        {summaryStats.map((stat, index) => {
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

      {/* Row 2: Sales Trend + Top Products */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Sales Trend</h3>
          </div>
          <div style={{ height: '300px' }}>
            <Line data={salesChartData} options={chartOptions} />
          </div>
        </div>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Top Products by Revenue</h3>
          </div>
          <div style={{ height: '300px' }}>
            <Bar data={topProductsData} options={barOptions} />
          </div>
        </div>
      </div>

      {/* Row 3: Profit/Loss + Stock Predictions */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Profit & Loss</h3>
          </div>
          <div style={{ height: '300px' }}>
            <Line data={profitLossData} options={chartOptions} />
          </div>
        </div>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={20} color="#f59e0b" />
              Stock Predictions
            </h3>
          </div>
          <div>
            {stockPredictions.length === 0 ? (
              <p style={{ color: '#64748b', textAlign: 'center', padding: '40px 0' }}>No stock alerts at this time.</p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Current Stock</th>
                    <th>Days Left</th>
                  </tr>
                </thead>
                <tbody>
                  {stockPredictions.map((item, idx) => (
                    <tr key={idx}>
                      <td style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Package size={16} color="#64748b" />
                        {item.product_name}
                      </td>
                      <td>{item.current_stock}</td>
                      <td>
                        <span className={`badge ${item.days_until_stockout <= 7 ? 'badge-danger' : item.days_until_stockout <= 14 ? 'badge-warning' : 'badge-success'}`}>
                          {item.days_until_stockout} days
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Analytics;
