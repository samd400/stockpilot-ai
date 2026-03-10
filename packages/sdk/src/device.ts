/**
 * StockPilot SDK — Device pairing & provisioning helpers.
 */

import type { DevicePairRequest, DevicePairResponse, DeviceClaimRequest } from "./types";

export interface SecureStorage {
  setItem(key: string, value: string): Promise<void>;
  getItem(key: string): Promise<string | null>;
  deleteItem(key: string): Promise<void>;
}

const DEVICE_TOKEN_KEY = "stockpilot_device_token";
const DEVICE_ID_KEY = "stockpilot_device_id";

export class DeviceManager {
  private storage: SecureStorage;

  constructor(storage: SecureStorage) {
    this.storage = storage;
  }

  /** Store device token securely after pairing. */
  async saveDeviceToken(token: string, deviceId: string): Promise<void> {
    await this.storage.setItem(DEVICE_TOKEN_KEY, token);
    await this.storage.setItem(DEVICE_ID_KEY, deviceId);
  }

  /** Retrieve stored device token. */
  async getDeviceToken(): Promise<string | null> {
    return this.storage.getItem(DEVICE_TOKEN_KEY);
  }

  /** Retrieve stored device ID. */
  async getDeviceId(): Promise<string | null> {
    return this.storage.getItem(DEVICE_ID_KEY);
  }

  /** Check if this device is paired. */
  async isPaired(): Promise<boolean> {
    const token = await this.getDeviceToken();
    return token !== null && token.length > 0;
  }

  /** Clear device credentials (unpair). */
  async unpair(): Promise<void> {
    await this.storage.deleteItem(DEVICE_TOKEN_KEY);
    await this.storage.deleteItem(DEVICE_ID_KEY);
  }

  /** Generate QR code data for pairing display. */
  generatePairingQRData(pairingResponse: DevicePairResponse): string {
    return JSON.stringify({
      type: "stockpilot_pairing",
      token: pairingResponse.pairing_token,
      device_id: pairingResponse.device_id,
      expires_at: pairingResponse.expires_at,
    });
  }

  /** Get device metadata for registration. */
  getDeviceMetadata(): Record<string, string> {
    const ua = typeof navigator !== "undefined" ? navigator.userAgent : "unknown";
    return {
      user_agent: ua,
      platform: typeof navigator !== "undefined" ? navigator.platform || "unknown" : "unknown",
      screen: typeof screen !== "undefined" ? `${screen.width}x${screen.height}` : "unknown",
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      timestamp: new Date().toISOString(),
    };
  }
}

/**
 * Default localStorage-based SecureStorage for web (non-production).
 * Production should use Keychain (mobile) or OS keychain (desktop).
 */
export class WebSecureStorage implements SecureStorage {
  async setItem(key: string, value: string): Promise<void> {
    localStorage.setItem(key, value);
  }
  async getItem(key: string): Promise<string | null> {
    return localStorage.getItem(key);
  }
  async deleteItem(key: string): Promise<void> {
    localStorage.removeItem(key);
  }
}
