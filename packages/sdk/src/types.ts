/** StockPilot SDK — shared types for all clients. */

// ===== Auth =====
export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  tenant_id: string;
  role: string;
}

// ===== Product =====
export interface Product {
  id: string;
  product_name: string;
  sku?: string;
  barcode?: string;
  selling_price: number;
  purchase_price: number;
  stock_quantity: number;
  gst_percentage?: number;
  currency?: string;
  category?: string;
  tenant_id?: string;
}

// ===== Invoice =====
export interface InvoiceItem {
  product_id: string;
  product_name?: string;
  quantity: number;
  price_per_unit: number;
  gst_percentage?: number;
  cgst_amount?: number;
  sgst_amount?: number;
}

export interface Invoice {
  id?: string;
  invoice_number?: string;
  tenant_id?: string;
  customer_name?: string;
  customer_phone?: string;
  items: InvoiceItem[];
  subtotal: number;
  tax: number;
  total_amount: number;
  currency: string;
  payment_status?: string;
  created_at?: string;
}

// ===== POS =====
export interface POSBillRequest {
  customer_id?: string;
  items: Array<{
    product_id: string;
    quantity: number;
    price?: number;
  }>;
  payment_mode?: string;
}

export interface POSBillResponse {
  invoice_id: string;
  invoice_number: string;
  total_amount: number;
  payment_status: string;
  created_at: string;
}

// ===== Device =====
export interface DevicePairRequest {
  device_name: string;
  device_type: "desktop" | "mobile" | "pos_terminal";
  platform: string;
}

export interface DevicePairResponse {
  pairing_token: string;
  device_id: string;
  expires_at: string;
}

export interface DeviceClaimRequest {
  pairing_token: string;
  device_metadata: Record<string, string>;
}

// ===== Sync =====
export type SyncAction = "create" | "update" | "delete";
export type SyncEntity = "invoice" | "product" | "order" | "customer";
export type SyncStatus = "pending" | "syncing" | "synced" | "failed" | "conflict";

export interface SyncQueueItem {
  id: string;
  entity: SyncEntity;
  action: SyncAction;
  payload: Record<string, unknown>;
  status: SyncStatus;
  created_at: number;
  retry_count: number;
  last_error?: string;
}

// ===== Printer =====
export interface PrinterConfig {
  type: "network" | "usb" | "bluetooth" | "browser";
  ip?: string;
  port?: number;
  name?: string;
  paperWidth?: 58 | 80;
}

export interface ReceiptOptions {
  paperWidth: 58 | 80;
  currency: string;
  showGST: boolean;
  showVAT: boolean;
  storeName: string;
  storeAddress?: string;
  storePhone?: string;
  storeGSTIN?: string;
  footerText?: string;
}
