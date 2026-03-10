import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import RoleGuard from './components/RoleGuard';
import { AuthProvider, useAuth } from './context/AuthContext';

// Lazy-loaded pages
const Login = React.lazy(() => import('./pages/Login'));
const Register = React.lazy(() => import('./pages/Register'));
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const POSBilling = React.lazy(() => import('./pages/POSBilling'));
const Products = React.lazy(() => import('./pages/Products'));
const Inventory = React.lazy(() => import('./pages/Inventory'));
const Invoices = React.lazy(() => import('./pages/Invoices'));
const Orders = React.lazy(() => import('./pages/Orders'));
const Customers = React.lazy(() => import('./pages/Customers'));
const Suppliers = React.lazy(() => import('./pages/Suppliers'));
const PurchaseOrders = React.lazy(() => import('./pages/PurchaseOrders'));
const Expenses = React.lazy(() => import('./pages/Expenses'));
const RMA = React.lazy(() => import('./pages/RMA'));
const Analytics = React.lazy(() => import('./pages/Analytics'));
const Assistant = React.lazy(() => import('./pages/Assistant'));
const Pricing = React.lazy(() => import('./pages/Pricing'));
const Reports = React.lazy(() => import('./pages/Reports'));
const Alerts = React.lazy(() => import('./pages/Alerts'));
const Settings = React.lazy(() => import('./pages/Settings'));

function LoadingSpinner() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%' }}>
      <div
        style={{
          width: 36,
          height: 36,
          border: '3px solid rgba(99,102,241,0.2)',
          borderTopColor: '#6366f1',
          borderRadius: '50%',
          animation: 'spin 0.6s linear infinite',
        }}
      />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

function AppLayout({ children }) {
  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">{children}</main>
    </div>
  );
}

// Routes with their required permission (null = any authenticated user)
const protectedRoutes = [
  { path: '/',           element: <Dashboard />,      permission: null },
  { path: '/pos',        element: <POSBilling />,     permission: 'billing' },
  { path: '/products',   element: <Products />,       permission: 'inventory' },
  { path: '/inventory',  element: <Inventory />,      permission: 'inventory' },
  { path: '/invoices',   element: <Invoices />,       permission: 'billing' },
  { path: '/orders',     element: <Orders />,         permission: 'crm' },
  { path: '/customers',  element: <Customers />,      permission: 'crm' },
  { path: '/suppliers',  element: <Suppliers />,      permission: 'inventory' },
  { path: '/purchases',  element: <PurchaseOrders />, permission: 'inventory' },
  { path: '/expenses',   element: <Expenses />,       permission: 'billing' },
  { path: '/rma',        element: <RMA />,            permission: 'inventory' },
  { path: '/analytics',  element: <Analytics />,      permission: null },
  { path: '/assistant',  element: <Assistant />,      permission: null },
  { path: '/pricing',    element: <Pricing />,        permission: 'billing' },
  { path: '/reports',    element: <Reports />,        permission: 'analytics' },
  { path: '/alerts',     element: <Alerts />,         permission: null },
  { path: '/settings',   element: <Settings />,       permission: 'settings' },
];

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      {protectedRoutes.map(({ path, element, permission }) => (
        <Route
          key={path}
          path={path}
          element={
            <ProtectedRoute>
              <AppLayout>
                {permission ? (
                  <RoleGuard permission={permission}>{element}</RoleGuard>
                ) : (
                  element
                )}
              </AppLayout>
            </ProtectedRoute>
          }
        />
      ))}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<LoadingSpinner />}>
          <AppRoutes />
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
