import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Building, Users, Shield, Bell, Sliders, Save, Globe, Trash2, UserPlus } from 'lucide-react';
import { tenantAPI, usersAPI } from '../services/api';

function Settings() {
  const [activeTab, setActiveTab] = useState('business');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Business Profile state
  const [profile, setProfile] = useState({
    business_name: '', email: '', phone: '', address: '', gst_number: '', pan_number: '',
    country_code: '', currency: 'INR', tax_region: 'india_gst', timezone: '',
    invoice_prefix: '', logo_url: '', subdomain: '',
  });

  // Team & Users state
  const [users, setUsers] = useState([]);
  const [showAddMember, setShowAddMember] = useState(false);
  const [newMember, setNewMember] = useState({ email: '', password: '', role: 'viewer' });
  const [addMemberError, setAddMemberError] = useState('');
  const [addMemberLoading, setAddMemberLoading] = useState(false);

  // Preferences state
  const [preferences, setPreferences] = useState({
    allow_autonomous_agents: false,
    allow_dynamic_pricing: false,
    allow_auto_procurement: false,
    notify_low_stock: true,
    notify_new_order: true,
    notify_payment: true,
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [tenantRes, usersRes] = await Promise.allSettled([
        tenantAPI.getMe(),
        usersAPI.list(),
      ]);
      if (tenantRes.status === 'fulfilled') {
        const d = tenantRes.value.data;
        setProfile((prev) => ({ ...prev, ...d }));
        if (d.preferences) setPreferences((prev) => ({ ...prev, ...d.preferences }));
      }
      if (usersRes.status === 'fulfilled') {
        setUsers(usersRes.value.data || []);
      }
    } catch (error) {
      console.error('Error fetching settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProfileChange = (e) => {
    setProfile({ ...profile, [e.target.name]: e.target.value });
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      const { subdomain, ...data } = profile;
      await tenantAPI.update(data);
    } catch (error) {
      console.error('Error saving profile:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleAddMember = async () => {
    if (!newMember.email || !newMember.password) {
      setAddMemberError('Email and password are required');
      return;
    }
    setAddMemberError('');
    setAddMemberLoading(true);
    try {
      const res = await usersAPI.create({
        email: newMember.email,
        password: newMember.password,
        role: newMember.role,
      });
      setUsers([...users, res.data]);
      setShowAddMember(false);
      setNewMember({ email: '', password: '', role: 'viewer' });
    } catch (error) {
      setAddMemberError(error.response?.data?.detail || 'Failed to create user');
    } finally {
      setAddMemberLoading(false);
    }
  };

  const handleRoleChange = async (index, newRole) => {
    const updated = [...users];
    updated[index] = { ...updated[index], role: newRole };
    setUsers(updated);
    try {
      await usersAPI.update(updated[index].id, { role: newRole });
    } catch (error) {
      console.error('Error updating role:', error);
    }
  };

  const handleDeactivateUser = async (index) => {
    const user = users[index];
    if (!window.confirm(`Deactivate ${user.email}?`)) return;
    try {
      await usersAPI.delete(user.id);
      setUsers(users.map((u, i) => i === index ? { ...u, is_active: false } : u));
    } catch (error) {
      console.error('Error deactivating user:', error);
    }
  };

  const handleSavePreferences = async () => {
    setSaving(true);
    try {
      await tenantAPI.update({ preferences });
    } catch (error) {
      console.error('Error saving preferences:', error);
    } finally {
      setSaving(false);
    }
  };

  const tabs = [
    { id: 'business', label: 'Business Profile', icon: Building },
    { id: 'team', label: 'Team & Roles', icon: Users },
    { id: 'preferences', label: 'Preferences', icon: Sliders },
  ];

  if (loading) {
    return <div className="loading">Loading settings...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p style={{ color: '#64748b' }}>Manage your business profile, team, and preferences</p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '24px', borderBottom: '2px solid #e2e8f0', paddingBottom: '0' }}>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              className="btn"
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '12px 20px',
                borderRadius: '8px 8px 0 0',
                borderBottom: activeTab === tab.id ? '2px solid #2563eb' : '2px solid transparent',
                color: activeTab === tab.id ? '#2563eb' : '#64748b',
                fontWeight: activeTab === tab.id ? 600 : 400,
                marginBottom: '-2px',
              }}
            >
              <Icon size={16} style={{ marginRight: '8px' }} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Business Profile Tab */}
      {activeTab === 'business' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Building size={20} color="#2563eb" />
              Business Profile
            </h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Business Name</label>
              <input type="text" name="business_name" className="form-input" value={profile.business_name} onChange={handleProfileChange} />
            </div>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input type="email" name="email" className="form-input" value={profile.email} onChange={handleProfileChange} />
            </div>
            <div className="form-group">
              <label className="form-label">Phone</label>
              <input type="text" name="phone" className="form-input" value={profile.phone} onChange={handleProfileChange} />
            </div>
            <div className="form-group">
              <label className="form-label">Address</label>
              <input type="text" name="address" className="form-input" value={profile.address} onChange={handleProfileChange} />
            </div>
            <div className="form-group">
              <label className="form-label">GST Number</label>
              <input type="text" name="gst_number" className="form-input" value={profile.gst_number} onChange={handleProfileChange} />
            </div>
            <div className="form-group">
              <label className="form-label">PAN Number</label>
              <input type="text" name="pan_number" className="form-input" value={profile.pan_number} onChange={handleProfileChange} />
            </div>
            <div className="form-group">
              <label className="form-label">Country Code</label>
              <input type="text" name="country_code" className="form-input" value={profile.country_code} onChange={handleProfileChange} />
            </div>
            <div className="form-group">
              <label className="form-label">Currency</label>
              <select name="currency" className="form-input" value={profile.currency} onChange={handleProfileChange}>
                {['INR', 'USD', 'EUR', 'GBP', 'AED', 'SAR'].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Tax Region</label>
              <select name="tax_region" className="form-input" value={profile.tax_region} onChange={handleProfileChange}>
                {[{ v: 'india_gst', l: 'India GST' }, { v: 'gcc_vat', l: 'GCC VAT' }, { v: 'eu_vat', l: 'EU VAT' }].map((r) => (
                  <option key={r.v} value={r.v}>{r.l}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Timezone</label>
              <input type="text" name="timezone" className="form-input" value={profile.timezone} onChange={handleProfileChange} placeholder="Asia/Kolkata" />
            </div>
            <div className="form-group">
              <label className="form-label">Invoice Prefix</label>
              <input type="text" name="invoice_prefix" className="form-input" value={profile.invoice_prefix} onChange={handleProfileChange} placeholder="INV-" />
            </div>
            <div className="form-group">
              <label className="form-label">Logo URL</label>
              <input type="text" name="logo_url" className="form-input" value={profile.logo_url} onChange={handleProfileChange} />
            </div>
          </div>
          {profile.subdomain && (
            <div className="form-group">
              <label className="form-label">Subdomain (read-only)</label>
              <input type="text" className="form-input" value={profile.subdomain} disabled style={{ backgroundColor: '#f1f5f9' }} />
            </div>
          )}
          <div style={{ marginTop: '24px' }}>
            <button className="btn btn-primary" onClick={handleSaveProfile} disabled={saving}>
              <Save size={16} style={{ marginRight: '8px' }} />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      )}

      {/* Team & Users Tab */}
      {activeTab === 'team' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Shield size={20} color="#7c3aed" />
              Team Members
            </h3>
            <button className="btn btn-primary" onClick={() => { setShowAddMember(true); setAddMemberError(''); }}>
              <UserPlus size={16} style={{ marginRight: '8px' }} />
              Add User
            </button>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((member, idx) => (
                <tr key={member.id || idx}>
                  <td>{member.email}</td>
                  <td>
                    <select
                      className="form-input"
                      style={{ padding: '4px 8px', width: 'auto' }}
                      value={member.role}
                      onChange={(e) => handleRoleChange(idx, e.target.value)}
                    >
                      <option value="admin">Admin</option>
                      <option value="manager">Manager</option>
                      <option value="billing_staff">Billing Staff</option>
                      <option value="inventory_staff">Inventory Staff</option>
                      <option value="crm_staff">CRM Staff</option>
                      <option value="viewer">Viewer</option>
                    </select>
                  </td>
                  <td>
                    <span className={`badge ${member.is_active !== false ? 'badge-success' : 'badge-error'}`}>
                      {member.is_active !== false ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    {member.is_active !== false && (
                      <button
                        className="btn"
                        style={{ padding: '6px', color: '#ef4444' }}
                        onClick={() => handleDeactivateUser(idx)}
                        title="Deactivate user"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr><td colSpan={4} style={{ textAlign: 'center', color: '#64748b', padding: '24px' }}>No users found</td></tr>
              )}
            </tbody>
          </table>

          {showAddMember && (
            <div className="modal-overlay" onClick={() => setShowAddMember(false)}>
              <div className="modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3 className="modal-title">Create Team Member</h3>
                  <button className="btn" onClick={() => setShowAddMember(false)}>✕</button>
                </div>
                {addMemberError && <div className="alert alert-error" style={{ marginBottom: '16px' }}>{addMemberError}</div>}
                <div className="form-group">
                  <label className="form-label">Email</label>
                  <input
                    type="email"
                    className="form-input"
                    value={newMember.email}
                    onChange={(e) => setNewMember({ ...newMember, email: e.target.value })}
                    placeholder="employee@company.com"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Password</label>
                  <input
                    type="password"
                    className="form-input"
                    value={newMember.password}
                    onChange={(e) => setNewMember({ ...newMember, password: e.target.value })}
                    placeholder="Min 8 characters"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Role</label>
                  <select
                    className="form-input"
                    value={newMember.role}
                    onChange={(e) => setNewMember({ ...newMember, role: e.target.value })}
                  >
                    <option value="manager">Manager (full access)</option>
                    <option value="billing_staff">Billing Staff (invoices, payments)</option>
                    <option value="inventory_staff">Inventory Staff (products, stock)</option>
                    <option value="crm_staff">CRM Staff (customers, orders)</option>
                    <option value="viewer">Viewer (read-only)</option>
                    <option value="admin">Admin (all access)</option>
                  </select>
                </div>
                <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                  <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleAddMember} disabled={addMemberLoading}>
                    {addMemberLoading ? 'Creating...' : 'Create User'}
                  </button>
                  <button className="btn btn-secondary" onClick={() => setShowAddMember(false)}>
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Preferences Tab */}
      {activeTab === 'preferences' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sliders size={20} color="#059669" />
              Preferences
            </h3>
          </div>

          <div style={{ marginBottom: '32px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Globe size={16} color="#64748b" />
              Feature Flags
            </h4>
            {[
              { key: 'allow_autonomous_agents', label: 'Allow Autonomous Agents' },
              { key: 'allow_dynamic_pricing', label: 'Allow Dynamic Pricing' },
              { key: 'allow_auto_procurement', label: 'Allow Auto Procurement' },
            ].map((flag) => (
              <label key={flag.key} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 0', borderBottom: '1px solid #f1f5f9', cursor: 'pointer' }}>
                <div
                  onClick={() => setPreferences({ ...preferences, [flag.key]: !preferences[flag.key] })}
                  style={{
                    width: '44px', height: '24px', borderRadius: '12px', padding: '2px', cursor: 'pointer',
                    backgroundColor: preferences[flag.key] ? '#2563eb' : '#cbd5e1', transition: 'background-color 0.2s',
                  }}
                >
                  <div style={{
                    width: '20px', height: '20px', borderRadius: '50%', backgroundColor: '#fff',
                    transform: preferences[flag.key] ? 'translateX(20px)' : 'translateX(0)', transition: 'transform 0.2s',
                  }} />
                </div>
                <span>{flag.label}</span>
              </label>
            ))}
          </div>

          <div style={{ marginBottom: '32px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Bell size={16} color="#64748b" />
              Notification Settings
            </h4>
            {[
              { key: 'notify_low_stock', label: 'Low stock alerts' },
              { key: 'notify_new_order', label: 'New order alerts' },
              { key: 'notify_payment', label: 'Payment alerts' },
            ].map((notif) => (
              <label key={notif.key} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 0', borderBottom: '1px solid #f1f5f9', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={preferences[notif.key]}
                  onChange={(e) => setPreferences({ ...preferences, [notif.key]: e.target.checked })}
                  style={{ width: '18px', height: '18px', accentColor: '#2563eb' }}
                />
                <span>{notif.label}</span>
              </label>
            ))}
          </div>

          <button className="btn btn-primary" onClick={handleSavePreferences} disabled={saving}>
            <Save size={16} style={{ marginRight: '8px' }} />
            {saving ? 'Saving...' : 'Save Preferences'}
          </button>
        </div>
      )}
    </div>
  );
}

export default Settings;
