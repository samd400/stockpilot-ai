/** StockPilot SDK — barrel export. */

export { StockPilotClient } from "./client";
export type { StockPilotClientConfig } from "./client";

export { formatReceiptESCPOS, formatReceiptHTML, cashDrawerCommand, receiptToBase64 } from "./receipt";

export { SyncQueue } from "./sync";
export type { SyncStorage, SyncApiHandler, SyncStats } from "./sync";

export { DeviceManager, WebSecureStorage } from "./device";
export type { SecureStorage } from "./device";

export {
  NetworkPrinterDriver,
  BrowserPrinterDriver,
  LocalAgentPrinterDriver,
  createPrinterDriver,
} from "./printer";
export type { PrinterDriver } from "./printer";

export * from "./types";
