/**
 * StockPilot SDK — Offline sync queue (platform-agnostic logic).
 * Concrete storage backends (Dexie, SQLite) are injected via SyncStorage interface.
 */

import type { SyncQueueItem, SyncEntity, SyncAction, SyncStatus } from "./types";

export interface SyncStorage {
  addItem(item: SyncQueueItem): Promise<void>;
  getItems(status: SyncStatus): Promise<SyncQueueItem[]>;
  updateItem(id: string, updates: Partial<SyncQueueItem>): Promise<void>;
  deleteItem(id: string): Promise<void>;
  count(status?: SyncStatus): Promise<number>;
  clear(): Promise<void>;
}

export interface SyncApiHandler {
  /** Execute a sync item against the backend. Returns true on success. */
  execute(item: SyncQueueItem): Promise<{ success: boolean; error?: string; conflict?: boolean }>;
}

export class SyncQueue {
  private storage: SyncStorage;
  private api: SyncApiHandler;
  private processing = false;
  private maxRetries = 5;
  private listeners: Array<(stats: SyncStats) => void> = [];

  constructor(storage: SyncStorage, api: SyncApiHandler, maxRetries = 5) {
    this.storage = storage;
    this.api = api;
    this.maxRetries = maxRetries;
  }

  /** Enqueue a new item for sync. */
  async enqueue(entity: SyncEntity, action: SyncAction, payload: Record<string, unknown>): Promise<string> {
    const id = crypto.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const item: SyncQueueItem = {
      id,
      entity,
      action,
      payload,
      status: "pending",
      created_at: Date.now(),
      retry_count: 0,
    };
    await this.storage.addItem(item);
    this.notifyListeners();
    return id;
  }

  /** Process all pending items in the queue. */
  async processQueue(): Promise<SyncStats> {
    if (this.processing) return this.getStats();
    this.processing = true;

    try {
      const pending = await this.storage.getItems("pending");
      const failed = await this.storage.getItems("failed");
      const retryable = failed.filter((i) => i.retry_count < this.maxRetries);
      const items = [...pending, ...retryable];

      let synced = 0;
      let errors = 0;
      let conflicts = 0;

      for (const item of items) {
        await this.storage.updateItem(item.id, { status: "syncing" });

        const result = await this.api.execute(item);

        if (result.success) {
          await this.storage.deleteItem(item.id);
          synced++;
        } else if (result.conflict) {
          await this.storage.updateItem(item.id, {
            status: "conflict",
            last_error: result.error || "Server conflict (409)",
          });
          conflicts++;
        } else {
          await this.storage.updateItem(item.id, {
            status: "failed",
            retry_count: item.retry_count + 1,
            last_error: result.error || "Unknown error",
          });
          errors++;
        }
      }

      this.notifyListeners();
      return { total: items.length, synced, errors, conflicts };
    } finally {
      this.processing = false;
    }
  }

  /** Get queue statistics. */
  async getStats(): Promise<SyncStats> {
    const pending = await this.storage.count("pending");
    const failed = await this.storage.count("failed");
    const syncing = await this.storage.count("syncing");
    const conflicts = await this.storage.count("conflict");
    return { total: pending + failed + syncing + conflicts, synced: 0, errors: failed, conflicts };
  }

  /** Subscribe to queue status changes. */
  onStatusChange(listener: (stats: SyncStats) => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  private async notifyListeners() {
    const stats = await this.getStats();
    this.listeners.forEach((l) => l(stats));
  }
}

export interface SyncStats {
  total: number;
  synced: number;
  errors: number;
  conflicts: number;
}
