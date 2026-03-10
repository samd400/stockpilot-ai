import axios from 'axios';

// Base URL '/api' works through nginx (production) and Vite dev proxy (development)
const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Redirect to login only when the JWT token is actually expired
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      const token = localStorage.getItem('token');
      if (!token) {
        window.location.href = '/login';
      } else {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          if (payload.exp && Date.now() / 1000 > payload.exp) {
            // Token genuinely expired — force re-login
            localStorage.removeItem('token');
            window.location.href = '/login';
          }
          // Token is still valid — 401 is a permission/service error, not an auth error
        } catch {
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// ─── Auth Service (port 8001) ────────────────────────────────────────────────
// Proxy: /api/auth/* → strips /api/auth → auth-service
// e.g. /api/auth/auth/login → auth-service handles /auth/login
export const authAPI = {
  login: (credentials) => api.post('/auth/auth/login', new URLSearchParams(credentials), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  }),
  // POST /auth/register — creates tenant + admin user
  register: (userData) => api.post('/auth/auth/register', userData),
};

export const usersAPI = {
  getMe: () => api.get('/auth/auth/me'),
  list: () => api.get('/auth/users'),
  create: (data) => api.post('/auth/users', data),
  update: (id, data) => api.patch(`/auth/users/${id}`, data),
  delete: (id) => api.delete(`/auth/users/${id}`),
  changePassword: (id, data) => api.patch(`/auth/users/${id}/password`, data),
};

export const tenantAPI = {
  getMe: () => api.get('/auth/tenants/me'),
  update: (data) => api.put('/auth/tenants/me', data),
};

export const rbacAPI = {
  getRoles: () => api.get('/auth/rbac/roles'),
  getUserRole: (userId) => api.get(`/auth/rbac/roles/${userId}`),
  assignRole: (data) => api.post('/auth/rbac/roles', data),
  updateRole: (userId, data) => api.put(`/auth/rbac/roles/${userId}`, data),
  deleteRole: (userId) => api.delete(`/auth/rbac/roles/${userId}`),
  getPermissions: () => api.get('/auth/rbac/permissions'),
};

// ─── Inventory Service (port 8002) ───────────────────────────────────────────
// Proxy: /api/inventory/* → strips /api/inventory → inventory-service
export const productsAPI = {
  getAll: (params) => api.get('/inventory/products', { params }),
  getById: (id) => api.get(`/inventory/products/${id}`),
  create: (data) => api.post('/inventory/products', data),
  update: (id, data) => api.put(`/inventory/products/${id}`, data),
  delete: (id) => api.delete(`/inventory/products/${id}`),
};

export const inventoryAPI = {
  getAll: () => api.get('/inventory/products'),
  getLowStock: () => api.get('/inventory/products', { params: { low_stock: true } }),
};

export const branchesAPI = {
  getAll: () => api.get('/inventory/branches'),
  getById: (id) => api.get(`/inventory/branches/${id}`),
  create: (data) => api.post('/inventory/branches', data),
  update: (id, data) => api.put(`/inventory/branches/${id}`, data),
  delete: (id) => api.delete(`/inventory/branches/${id}`),
  getInventory: (id) => api.get(`/inventory/branches/${id}/inventory`),
  adjustStock: (id, data) => api.post(`/inventory/branches/${id}/inventory/adjust`, data),
};

export const suppliersAPI = {
  getAll: (params) => api.get('/inventory/suppliers', { params }),
  getById: (id) => api.get(`/inventory/suppliers/${id}`),
  create: (data) => api.post('/inventory/suppliers', data),
  update: (id, data) => api.put(`/inventory/suppliers/${id}`, data),
  delete: (id) => api.delete(`/inventory/suppliers/${id}`),
};

export const purchaseOrdersAPI = {
  getAll: (params) => api.get('/inventory/purchase-orders', { params }),
  getById: (id) => api.get(`/inventory/purchase-orders/${id}`),
  create: (data) => api.post('/inventory/purchase-orders', data),
  update: (id, data) => api.put(`/inventory/purchase-orders/${id}`, data),
  receive: (id, data) => api.post(`/inventory/purchase-orders/${id}/receive`, data),
  send: (id) => api.post(`/inventory/purchase-orders/${id}/send`),
};

export const rmaAPI = {
  getAll: (params) => api.get('/inventory/rma', { params }),
  getById: (id) => api.get(`/inventory/rma/${id}`),
  create: (data) => api.post('/inventory/rma', data),
  approve: (id) => api.post(`/inventory/rma/${id}/approve`),
  reject: (id, data) => api.post(`/inventory/rma/${id}/reject`, data),
  receive: (id) => api.post(`/inventory/rma/${id}/receive`),
};

// ─── Billing Service (port 8003) ─────────────────────────────────────────────
// Proxy: /api/billing/* → strips /api/billing → billing-service
export const invoicesAPI = {
  getAll: (params) => api.get('/billing/invoices', { params }),
  getById: (id) => api.get(`/billing/invoices/${id}`),
  create: (data) => api.post('/billing/invoices', data),
  update: (id, data) => api.put(`/billing/invoices/${id}`, data),
  cancel: (id) => api.post(`/billing/invoices/${id}/cancel`),
  getPDF: (id) => api.get(`/billing/invoices/${id}/pdf`, { responseType: 'blob' }),
};

export const paymentsAPI = {
  create: (data) => api.post('/billing/payments/', data),
  getByInvoice: (invoiceId) => api.get(`/billing/payments/invoice/${invoiceId}`),
  updateStatus: (id, data) => api.put(`/billing/payments/${id}/status`, data),
};

export const posAPI = {
  createBill: (data) => api.post('/billing/pos/bill', data),
  getBills: (params) => api.get('/billing/pos/bills', { params }),
  getBill: (id) => api.get(`/billing/pos/bills/${id}`),
  returnBill: (id) => api.post(`/billing/pos/bills/${id}/return`),
};

export const expensesAPI = {
  getAll: (params) => api.get('/billing/expenses/', { params }),
  getById: (id) => api.get(`/billing/expenses/${id}`),
  create: (data) => api.post('/billing/expenses/', data),
  update: (id, data) => api.put(`/billing/expenses/${id}`, data),
  delete: (id) => api.delete(`/billing/expenses/${id}`),
};

export const subscriptionsAPI = {
  getAll: () => api.get('/billing/subscriptions/'),
  getActive: () => api.get('/billing/subscriptions/active'),
  create: (data) => api.post('/billing/subscriptions/', data),
  cancel: (id) => api.post(`/billing/subscriptions/${id}/cancel`),
  upgrade: (id, data) => api.post(`/billing/subscriptions/${id}/upgrade`, data),
};

export const reportsAPI = {
  gstReport: (params) => api.get('/billing/compliance/india/gst-report', { params }),
  vatReport: (params) => api.get('/billing/compliance/eu/vat-report', { params }),
  gdprExport: (customerId) => api.get(`/billing/compliance/gdpr/export?customer_id=${customerId}`),
  gccEInvoice: (invoiceId) => api.post(`/billing/compliance/gcc/e-invoice/${invoiceId}`),
  indiaEInvoice: (invoiceId) => api.post(`/billing/compliance/india/e-invoice/${invoiceId}`),
};

// ─── CRM Service (port 8004) ─────────────────────────────────────────────────
// Proxy: /api/crm/* → strips /api/crm → crm-service
export const customersAPI = {
  getAll: (params) => api.get('/crm/customers', { params }),
  getById: (id) => api.get(`/crm/customers/${id}`),
  create: (data) => api.post('/crm/customers', data),
  update: (id, data) => api.put(`/crm/customers/${id}`, data),
  delete: (id) => api.delete(`/crm/customers/${id}`),
  getLoyalty: (id) => api.get(`/crm/customers/${id}/loyalty`),
  addLoyaltyPoints: (id, points) => api.post(`/crm/customers/${id}/loyalty/add-points`, { points }),
};

export const ordersAPI = {
  getAll: (params) => api.get('/crm/orders/', { params }),
  getById: (id) => api.get(`/crm/orders/${id}`),
  create: (data) => api.post('/crm/orders/', data),
  updateStatus: (id, data) => api.put(`/crm/orders/${id}/status`, data),
};

// ─── AI Service (port 8005) ──────────────────────────────────────────────────
// Proxy: /api/ai/* → strips /api/ai → ai-service
export const dashboardAPI = {
  getSummary: () => api.get('/ai/dashboard/summary'),
  getRevenue: () => api.get('/ai/dashboard/revenue'),
  getInsights: () => api.get('/ai/dashboard/insights'),
};

export const alertsAPI = {
  getAll: () => api.get('/ai/alerts/'),
  generate: () => api.post('/ai/alerts/generate'),
  markRead: (id) => api.patch(`/ai/alerts/${id}/read`),
  markAllRead: () => api.post('/ai/alerts/mark-all-read'),
};

export const agentsAPI = {
  list: () => api.get('/ai/agents/'),
  trigger: (name, payload) => api.post(`/ai/agents/${name}/trigger`, payload),
  triggerSync: (name, payload) => api.post(`/ai/agents/${name}/trigger-sync`, payload),
  status: (name) => api.get(`/ai/agents/${name}/status`),
  auditLogs: (params) => api.get('/ai/agents/audit/logs', { params }),
};

export const assistantAPI = {
  query: (query, history) => api.post('/ai/assistant/query', { query, history }),
  execute: (action, params) => api.post('/ai/assistant/execute', { action, params }),
};

export const pricingAPI = {
  createRule: (data) => api.post('/ai/pricing/rules', data),
  getRecommendations: () => api.get('/ai/pricing/recommendations'),
  getProductRecommendation: (productId) => api.get(`/ai/pricing/recommendations/${productId}`),
  apply: (productId) => api.post(`/ai/pricing/apply/${productId}`),
};

export const analyticsAPI = {
  getSalesTrend: () => api.get('/ai/analytics/sales-trend'),
  getTopProducts: () => api.get('/ai/analytics/top-products'),
  getProfitLossTrend: () => api.get('/ai/analytics/profit-loss-trend'),
  getBusinessSummary: () => api.get('/ai/analytics/business-summary'),
};

// ─── Notification Service (port 8006) ────────────────────────────────────────
// Proxy: /api/notifications/* → strips /api/notifications → notification-service
export const webhooksAPI = {
  getAll: () => api.get('/notifications/webhooks/'),
  create: (data) => api.post('/notifications/webhooks/', data),
  update: (id, data) => api.put(`/notifications/webhooks/${id}`, data),
  delete: (id) => api.delete(`/notifications/webhooks/${id}`),
};

export default api;
