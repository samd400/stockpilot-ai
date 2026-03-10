import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, ShoppingCart, Package, Warehouse, FileText,
  ClipboardList, Users, Truck, PackageSearch, Receipt, RotateCcw,
  BarChart3, Bot, Tags, FileBarChart, Bell, Settings, LogOut, TrendingUp, Shield,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

// permission: null = visible to all authenticated users
const sections = [
  {
    title: 'MAIN',
    items: [
      { icon: LayoutDashboard, label: 'Dashboard',   path: '/',          permission: null },
      { icon: ShoppingCart,    label: 'POS Billing', path: '/pos',       permission: 'billing' },
      { icon: Package,         label: 'Products',    path: '/products',  permission: 'inventory' },
      { icon: Warehouse,       label: 'Inventory',   path: '/inventory', permission: 'inventory' },
      { icon: FileText,        label: 'Invoices',    path: '/invoices',  permission: 'billing' },
      { icon: ClipboardList,   label: 'Orders',      path: '/orders',    permission: 'crm' },
    ],
  },
  {
    title: 'MANAGEMENT',
    items: [
      { icon: Users,         label: 'Customers',       path: '/customers', permission: 'crm' },
      { icon: Truck,         label: 'Suppliers',       path: '/suppliers', permission: 'inventory' },
      { icon: PackageSearch, label: 'Purchase Orders', path: '/purchases', permission: 'inventory' },
      { icon: Receipt,       label: 'Expenses',        path: '/expenses',  permission: 'billing' },
      { icon: RotateCcw,     label: 'Returns/RMA',     path: '/rma',       permission: 'inventory' },
    ],
  },
  {
    title: 'INTELLIGENCE',
    items: [
      { icon: BarChart3,    label: 'Analytics',   path: '/analytics', permission: null },
      { icon: Bot,          label: 'AI Assistant', path: '/assistant', permission: null },
      { icon: Tags,         label: 'Pricing',      path: '/pricing',   permission: 'billing' },
      { icon: FileBarChart, label: 'Reports',      path: '/reports',   permission: 'analytics' },
    ],
  },
  {
    title: 'SYSTEM',
    items: [
      { icon: Bell,     label: 'Alerts',   path: '/alerts',   permission: null },
      { icon: Settings, label: 'Settings', path: '/settings', permission: 'settings' },
    ],
  },
];

const ROLE_LABELS = {
  admin: 'Admin',
  manager: 'Manager',
  billing_staff: 'Billing',
  inventory_staff: 'Inventory',
  crm_staff: 'CRM',
  viewer: 'Viewer',
};

const ROLE_COLORS = {
  admin: '#ef4444',
  manager: '#f59e0b',
  billing_staff: '#3b82f6',
  inventory_staff: '#10b981',
  crm_staff: '#8b5cf6',
  viewer: '#64748b',
};

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, hasPermission } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <TrendingUp size={28} />
        <div>
          <span>StockPilot</span>
          <span style={{ fontSize: '0.65rem', color: '#94a3b8', display: 'block', marginTop: '-2px' }}>v2.0</span>
        </div>
      </div>

      {/* Role badge */}
      {user && (
        <div
          style={{
            margin: '0 12px 8px',
            padding: '6px 10px',
            background: 'rgba(255,255,255,0.05)',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <Shield size={13} color={ROLE_COLORS[user.role] || '#64748b'} />
          <span
            style={{
              fontSize: '0.7rem',
              fontWeight: 600,
              color: ROLE_COLORS[user.role] || '#64748b',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            {ROLE_LABELS[user.role] || user.role}
          </span>
        </div>
      )}

      <nav style={{ flex: 1, overflowY: 'auto' }}>
        {sections.map((section) => {
          // Filter items the user can access
          const visibleItems = section.items.filter(
            (item) => item.permission === null || hasPermission(item.permission)
          );
          if (visibleItems.length === 0) return null;

          return (
            <div key={section.title}>
              <div
                style={{
                  fontSize: '0.65rem',
                  fontWeight: 600,
                  letterSpacing: '0.05em',
                  color: '#64748b',
                  padding: '16px 16px 6px',
                  textTransform: 'uppercase',
                }}
              >
                {section.title}
              </div>
              <ul className="sidebar-menu">
                {visibleItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  return (
                    <li
                      key={item.path}
                      className={`sidebar-menu-item ${isActive ? 'active' : ''}`}
                      onClick={() => navigate(item.path)}
                    >
                      <Icon size={18} />
                      <span>{item.label}</span>
                      {item.badge && (
                        <span
                          style={{
                            marginLeft: 'auto',
                            background: '#ef4444',
                            color: '#fff',
                            fontSize: '0.65rem',
                            fontWeight: 700,
                            borderRadius: '9999px',
                            minWidth: '18px',
                            height: '18px',
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            padding: '0 5px',
                          }}
                        >
                          {item.badge}
                        </span>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </nav>

      <div style={{ marginTop: 'auto', padding: '12px 0', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
        <ul className="sidebar-menu">
          <li className="sidebar-menu-item" onClick={handleLogout}>
            <LogOut size={18} />
            <span>Logout</span>
          </li>
        </ul>
      </div>
    </aside>
  );
}

export default Sidebar;
