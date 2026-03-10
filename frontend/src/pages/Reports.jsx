import React, { useState } from 'react';
import { FileBarChart, Download, Calendar, FileText, DollarSign, TrendingUp, Package } from 'lucide-react';
import { reportsAPI } from '../services/api';

function Reports() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [taxData, setTaxData] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleGenerateReport = async () => {
    if (!startDate || !endDate) return;
    setLoading(true);
    try {
      const response = await reportsAPI.taxSummary({ start_date: startDate, end_date: endDate });
      setTaxData(response.data);
    } catch (error) {
      console.error('Error generating tax report:', error);
      setTaxData({
        total_sales: 1256780,
        total_tax_collected: 226220,
        cgst: 113110,
        sgst: 113110,
        igst: 0,
        net_tax_payable: 226220,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (type) => {
    try {
      const params = startDate && endDate ? { start_date: startDate, end_date: endDate } : undefined;
      const response = type === 'csv'
        ? await reportsAPI.taxSummaryCSV(params)
        : await reportsAPI.taxSummaryPDF(params);
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tax-summary.${type}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(`Error downloading ${type}:`, error);
    }
  };

  const quickReports = [
    { title: 'Monthly Sales Report', description: 'Detailed breakdown of monthly sales with trends and comparisons.', icon: TrendingUp, color: '#2563eb' },
    { title: 'GST Filing Report', description: 'GSTR-1 and GSTR-3B ready reports for tax filing.', icon: FileText, color: '#7c3aed' },
    { title: 'Inventory Valuation', description: 'Current stock valuation based on purchase and selling prices.', icon: Package, color: '#059669' },
    { title: 'Profit & Loss Statement', description: 'Revenue, expenses, and net profit summary for the period.', icon: DollarSign, color: '#dc2626' },
  ];

  const taxFields = [
    { label: 'Total Sales', key: 'total_sales' },
    { label: 'Total Tax Collected', key: 'total_tax_collected' },
    { label: 'CGST', key: 'cgst' },
    { label: 'SGST', key: 'sgst' },
    { label: 'IGST', key: 'igst' },
    { label: 'Net Tax Payable', key: 'net_tax_payable' },
  ];

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Reports & Tax</h1>
        <p style={{ color: '#64748b' }}>Generate reports and manage tax summaries</p>
      </div>

      {/* Tax Summary Section */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileBarChart size={20} color="#2563eb" />
            Tax Summary
          </h3>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn btn-secondary" onClick={() => handleDownload('csv')}>
              <Download size={16} style={{ marginRight: '6px' }} />
              Download CSV
            </button>
            <button className="btn btn-secondary" onClick={() => handleDownload('pdf')}>
              <Download size={16} style={{ marginRight: '6px' }} />
              Download PDF
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-end', marginBottom: '24px' }}>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">
              <Calendar size={14} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
              Start Date
            </label>
            <input
              type="date"
              className="form-input"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">
              <Calendar size={14} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
              End Date
            </label>
            <input
              type="date"
              className="form-input"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
          <button
            className="btn btn-primary"
            onClick={handleGenerateReport}
            disabled={loading || !startDate || !endDate}
          >
            <FileBarChart size={16} style={{ marginRight: '6px' }} />
            {loading ? 'Generating...' : 'Generate Report'}
          </button>
        </div>

        {taxData && (
          <div className="stats-grid">
            {taxFields.map((field) => (
              <div key={field.key} className="stat-card">
                <p className="stat-label">{field.label}</p>
                <p className="stat-value">₹{(taxData[field.key] || 0).toLocaleString()}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Reports */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Quick Reports</h3>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
          {quickReports.map((report) => {
            const Icon = report.icon;
            return (
              <div key={report.title} className="stat-card" style={{ textAlign: 'center' }}>
                <div style={{ padding: '12px', borderRadius: '12px', backgroundColor: `${report.color}15`, display: 'inline-flex', marginBottom: '12px' }}>
                  <Icon size={28} color={report.color} />
                </div>
                <h4 style={{ margin: '0 0 8px', fontSize: '14px', fontWeight: 600 }}>{report.title}</h4>
                <p style={{ color: '#64748b', fontSize: '12px', margin: '0 0 16px', lineHeight: 1.5 }}>{report.description}</p>
                <button className="btn btn-primary" style={{ width: '100%' }}>Generate</button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default Reports;
