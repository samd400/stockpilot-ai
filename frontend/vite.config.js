import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      // Auth Service (8001) — /auth, /users, /tenants, /rbac
      '/api/auth': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/auth/, '')
      },
      // Inventory Service (8002) — /products, /branches, /suppliers, /purchase-orders, /devices, /rma
      '/api/inventory': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/inventory/, '')
      },
      // Billing Service (8003) — /invoices, /payments, /pos, /expenses, /compliance
      '/api/billing': {
        target: 'http://localhost:8003',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/billing/, '')
      },
      // CRM Service (8004) — /customers, /orders
      '/api/crm': {
        target: 'http://localhost:8004',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/crm/, '')
      },
      // AI Service (8005) — /agents, /assistant, /dashboard, /alerts
      '/api/ai': {
        target: 'http://localhost:8005',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/ai/, '')
      },
      // Notification Service (8006) — /notifications, /webhooks
      '/api/notifications': {
        target: 'http://localhost:8006',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/notifications/, '')
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  }
})
