/**
 * RoleGuard — renders an "Access Denied" page when the user lacks permission.
 * Usage: <RoleGuard permission="billing">...</RoleGuard>
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const PERMISSION_LABELS = {
  billing:          'Billing Staff, Manager, or Admin',
  billing_write:    'Billing Staff, Manager, or Admin',
  inventory:        'Inventory Staff, Manager, or Admin',
  inventory_write:  'Manager or Admin',
  crm:              'CRM Staff, Manager, or Admin',
  crm_write:        'CRM Staff, Manager, or Admin',
  analytics:        'Any authenticated user',
  settings:         'Manager or Admin',
  users:            'Admin only',
  compliance:       'Manager or Admin',
};

function AccessDenied({ permission }) {
  const navigate = useNavigate();
  const required = PERMISSION_LABELS[permission] || 'a higher role';

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        gap: '16px',
        color: '#64748b',
        padding: '40px',
      }}
    >
      <ShieldOff size={56} color="#94a3b8" />
      <h2 style={{ margin: 0, color: '#1e293b', fontSize: '1.5rem' }}>Access Restricted</h2>
      <p style={{ margin: 0, textAlign: 'center', maxWidth: '360px' }}>
        You don't have permission to view this page.
        <br />
        Required role: <strong>{required}</strong>
      </p>
      <button
        onClick={() => navigate('/')}
        style={{
          marginTop: '8px',
          padding: '10px 24px',
          background: '#2563eb',
          color: '#fff',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          fontWeight: 600,
        }}
      >
        Back to Dashboard
      </button>
    </div>
  );
}

function RoleGuard({ permission, children }) {
  const { hasPermission } = useAuth();

  if (!hasPermission(permission)) {
    return <AccessDenied permission={permission} />;
  }
  return children;
}

export default RoleGuard;
