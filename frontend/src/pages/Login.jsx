import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { TrendingUp } from 'lucide-react';

function Login() {
  const navigate = useNavigate();
  const { reload } = useAuth();
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const response = await authAPI.login({ username: formData.username, password: formData.password });
      localStorage.setItem('token', response.data.access_token);
      reload(); // decode role from JWT into AuthContext
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', marginBottom: '8px' }}>
            <TrendingUp size={40} color="#2563eb" />
            <span style={{ fontSize: '32px', fontWeight: 'bold', color: '#2563eb' }}>StockPilot</span>
          </div>
          <p style={{ color: '#64748b' }}>AI-Powered Retail Operating System</p>
        </div>

        <h2 className="login-title">Welcome Back</h2>
        <p className="login-subtitle">Sign in to your account</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input type="email" name="username" className="form-input" value={formData.username}
              onChange={handleChange} placeholder="Enter your email" required />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input type="password" name="password" className="form-input" value={formData.password}
              onChange={handleChange} placeholder="Enter your password" required />
          </div>
          <button type="submit" className="btn btn-primary"
            style={{ width: '100%', marginTop: '16px' }} disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '24px', color: '#64748b' }}>
          Don't have an account?{' '}
          <Link to="/register" style={{ color: '#2563eb', textDecoration: 'none' }}>Register here</Link>
        </p>
      </div>
    </div>
  );
}

export default Login;
