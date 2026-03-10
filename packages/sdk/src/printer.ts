/**
 * StockPilot SDK — Printer abstraction for network, USB, Bluetooth, and browser printing.
 */

import type { PrinterConfig } from "./types";

export interface PrinterDriver {
  /** Send raw bytes to the printer. */
  printRaw(bytes: Uint8Array): Promise<{ success: boolean; error?: string }>;
  /** Check printer connectivity. */
  isConnected(): Promise<boolean>;
}

/**
 * Network printer — sends raw ESC/POS bytes via TCP to ip:port.
 * Only works in environments with TCP access (desktop/mobile native).
 * Requires a native bridge function to be injected.
 */
export class NetworkPrinterDriver implements PrinterDriver {
  private ip: string;
  private port: number;
  private sendTCP: (ip: string, port: number, data: Uint8Array) => Promise<void>;

  constructor(
    ip: string,
    port: number,
    sendTCP: (ip: string, port: number, data: Uint8Array) => Promise<void>
  ) {
    this.ip = ip;
    this.port = port;
    this.sendTCP = sendTCP;
  }

  async printRaw(bytes: Uint8Array) {
    try {
      await this.sendTCP(this.ip, this.port, bytes);
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || "Print failed" };
    }
  }

  async isConnected() {
    try {
      await this.sendTCP(this.ip, this.port, new Uint8Array([0x1b, 0x40])); // ESC @ (init)
      return true;
    } catch {
      return false;
    }
  }
}

/**
 * Browser printer — uses window.print() with HTML receipt.
 * Fallback for environments without native printing.
 */
export class BrowserPrinterDriver implements PrinterDriver {
  async printRaw(_bytes: Uint8Array) {
    return { success: false, error: "Browser cannot print raw ESC/POS. Use printHTML() instead." };
  }

  async isConnected() {
    return typeof window !== "undefined" && typeof window.print === "function";
  }

  /** Print HTML receipt via browser print dialog. */
  printHTML(html: string) {
    const printWindow = window.open("", "_blank", "width=400,height=600");
    if (!printWindow) return { success: false, error: "Popup blocked" };

    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.focus();

    // Delay to let styles render
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 250);

    return { success: true };
  }
}

/**
 * Local agent printer — sends print jobs to a local desktop agent API
 * running at localhost. Used when web browser needs to print via native app.
 */
export class LocalAgentPrinterDriver implements PrinterDriver {
  private agentUrl: string;

  constructor(agentUrl = "http://localhost:19100") {
    this.agentUrl = agentUrl;
  }

  async printRaw(bytes: Uint8Array) {
    try {
      // Convert to base64
      let binary = "";
      for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
      const b64 = btoa(binary);

      const res = await fetch(`${this.agentUrl}/print`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: b64, encoding: "base64" }),
      });

      if (!res.ok) return { success: false, error: `Agent error: ${res.status}` };
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || "Local agent not reachable" };
    }
  }

  async isConnected() {
    try {
      const res = await fetch(`${this.agentUrl}/health`, { signal: AbortSignal.timeout(2000) });
      return res.ok;
    } catch {
      return false;
    }
  }
}

/** Factory to create the right printer driver based on config. */
export function createPrinterDriver(
  config: PrinterConfig,
  nativeSendTCP?: (ip: string, port: number, data: Uint8Array) => Promise<void>
): PrinterDriver {
  switch (config.type) {
    case "network":
      if (!config.ip || !nativeSendTCP) {
        throw new Error("Network printer requires ip and native TCP send function");
      }
      return new NetworkPrinterDriver(config.ip, config.port || 9100, nativeSendTCP);
    case "browser":
      return new BrowserPrinterDriver();
    default:
      return new BrowserPrinterDriver();
  }
}
