/** StockPilot SDK — API client wrapping all backend endpoints. */

import axios, { AxiosInstance, AxiosRequestConfig } from "axios";
import type {
  LoginRequest,
  TokenResponse,
  Product,
  Invoice,
  POSBillRequest,
  POSBillResponse,
  DevicePairRequest,
  DevicePairResponse,
  DeviceClaimRequest,
} from "./types";

export interface StockPilotClientConfig {
  baseURL: string;
  getToken?: () => string | null;
  onAuthError?: () => void;
}

export class StockPilotClient {
  private api: AxiosInstance;
  private config: StockPilotClientConfig;

  constructor(config: StockPilotClientConfig) {
    this.config = config;
    this.api = axios.create({
      baseURL: config.baseURL,
      headers: { "Content-Type": "application/json" },
    });

    // Auth interceptor
    this.api.interceptors.request.use((req) => {
      const token = config.getToken?.();
      if (token) req.headers.Authorization = `Bearer ${token}`;
      return req;
    });

    // Error interceptor
    this.api.interceptors.response.use(
      (res) => res,
      (err) => {
        if (err.response?.status === 401) config.onAuthError?.();
        return Promise.reject(err);
      }
    );
  }

  // ===== Auth =====
  async login(creds: LoginRequest): Promise<TokenResponse> {
    const { data } = await this.api.post("/auth/login", creds);
    return data;
  }

  // ===== Products =====
  async getProducts(): Promise<Product[]> {
    const { data } = await this.api.get("/products");
    return data;
  }

  async getProductByBarcode(barcode: string): Promise<Product | null> {
    try {
      const { data } = await this.api.get(`/products?barcode=${barcode}`);
      return Array.isArray(data) ? data[0] || null : data;
    } catch {
      return null;
    }
  }

  async getProduct(id: string): Promise<Product> {
    const { data } = await this.api.get(`/products/${id}`);
    return data;
  }

  // ===== Invoices =====
  async getInvoices(): Promise<Invoice[]> {
    const { data } = await this.api.get("/invoices");
    return data;
  }

  async createInvoice(invoice: Partial<Invoice>): Promise<Invoice> {
    const { data } = await this.api.post("/invoices", invoice);
    return data;
  }

  // ===== POS =====
  async createPOSBill(bill: POSBillRequest): Promise<POSBillResponse> {
    const { data } = await this.api.post("/pos/bill", bill);
    return data;
  }

  async getPOSBills(limit = 50): Promise<POSBillResponse[]> {
    const { data } = await this.api.get(`/pos/bills?limit=${limit}`);
    return data;
  }

  async getPOSBillDetails(invoiceId: string): Promise<any> {
    const { data } = await this.api.get(`/pos/bills/${invoiceId}`);
    return data;
  }

  // ===== Device Pairing =====
  async pairDevice(req: DevicePairRequest): Promise<DevicePairResponse> {
    const { data } = await this.api.post("/devices/pair", req);
    return data;
  }

  async claimDevice(req: DeviceClaimRequest): Promise<any> {
    const { data } = await this.api.post("/devices/claim", req);
    return data;
  }

  // ===== Sync =====
  async flushSyncQueue(): Promise<any> {
    const { data } = await this.api.post("/sync/queue/flush");
    return data;
  }

  // ===== Health =====
  async health(): Promise<{ status: string }> {
    const { data } = await this.api.get("/health");
    return data;
  }
}
