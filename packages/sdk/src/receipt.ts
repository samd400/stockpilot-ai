/**
 * StockPilot SDK — Receipt formatter producing ESC/POS bytes & HTML preview.
 * Supports 58mm and 80mm thermal printers, multi-currency, GST/VAT lines.
 */

import type { Invoice, InvoiceItem, ReceiptOptions } from "./types";

// ESC/POS command constants
const ESC = 0x1b;
const GS = 0x1d;
const LF = 0x0a;

const CMD = {
  INIT: [ESC, 0x40],                    // Initialize printer
  ALIGN_CENTER: [ESC, 0x61, 0x01],      // Center alignment
  ALIGN_LEFT: [ESC, 0x61, 0x00],        // Left alignment
  ALIGN_RIGHT: [ESC, 0x61, 0x02],       // Right alignment
  BOLD_ON: [ESC, 0x45, 0x01],           // Bold on
  BOLD_OFF: [ESC, 0x45, 0x00],          // Bold off
  DOUBLE_HEIGHT: [ESC, 0x21, 0x10],     // Double height
  NORMAL_SIZE: [ESC, 0x21, 0x00],       // Normal size
  CUT: [GS, 0x56, 0x00],               // Full cut
  PARTIAL_CUT: [GS, 0x56, 0x01],       // Partial cut
  FEED_3: [ESC, 0x64, 0x03],           // Feed 3 lines
  FEED_5: [ESC, 0x64, 0x05],           // Feed 5 lines
  CASH_DRAWER: [ESC, 0x70, 0x00, 0x19, 0xff], // Open cash drawer pin 2
};

const CHARS_58MM = 32;
const CHARS_80MM = 48;

function getLineWidth(paperWidth: 58 | 80): number {
  return paperWidth === 58 ? CHARS_58MM : CHARS_80MM;
}

function padLine(left: string, right: string, width: number): string {
  const gap = width - left.length - right.length;
  return left + " ".repeat(Math.max(gap, 1)) + right;
}

function centerText(text: string, width: number): string {
  const pad = Math.max(0, Math.floor((width - text.length) / 2));
  return " ".repeat(pad) + text;
}

function textToBytes(text: string): number[] {
  return Array.from(new TextEncoder().encode(text));
}

function formatCurrency(amount: number, currency: string): string {
  const symbols: Record<string, string> = {
    INR: "₹", USD: "$", EUR: "€", GBP: "£", AED: "AED ", SAR: "SAR ",
    BHD: "BHD ", QAR: "QAR ", KWD: "KWD ", OMR: "OMR ",
  };
  const sym = symbols[currency] || currency + " ";
  return `${sym}${amount.toFixed(2)}`;
}

/**
 * Generate ESC/POS bytes for a receipt.
 */
export function formatReceiptESCPOS(invoice: Invoice, options: ReceiptOptions): Uint8Array {
  const w = getLineWidth(options.paperWidth);
  const bytes: number[] = [];

  const push = (...data: number[][]) => data.forEach((d) => bytes.push(...d));
  const line = (text: string) => push(textToBytes(text), [LF]);
  const separator = () => line("-".repeat(w));

  // Initialize
  push(CMD.INIT);

  // Header — store name centered + bold
  push(CMD.ALIGN_CENTER, CMD.BOLD_ON, CMD.DOUBLE_HEIGHT);
  line(options.storeName);
  push(CMD.NORMAL_SIZE, CMD.BOLD_OFF);

  if (options.storeAddress) line(options.storeAddress);
  if (options.storePhone) line(`Tel: ${options.storePhone}`);
  if (options.storeGSTIN) line(`GSTIN: ${options.storeGSTIN}`);

  push(CMD.ALIGN_LEFT);
  separator();

  // Invoice info
  if (invoice.invoice_number) line(`Invoice: ${invoice.invoice_number}`);
  if (invoice.created_at) line(`Date: ${new Date(invoice.created_at).toLocaleString()}`);
  if (invoice.customer_name) line(`Customer: ${invoice.customer_name}`);
  separator();

  // Column headers
  push(CMD.BOLD_ON);
  line(padLine("Item", "Amount", w));
  push(CMD.BOLD_OFF);
  separator();

  // Items
  for (const item of invoice.items) {
    const name = (item.product_name || "Item").substring(0, w - 15);
    const amount = formatCurrency(item.quantity * item.price_per_unit, options.currency);
    line(padLine(name, amount, w));
    line(`  ${item.quantity} x ${formatCurrency(item.price_per_unit, options.currency)}`);

    if (options.showGST && item.gst_percentage) {
      const gstAmt = (item.cgst_amount || 0) + (item.sgst_amount || 0);
      if (gstAmt > 0) line(`  GST ${item.gst_percentage}%: ${formatCurrency(gstAmt, options.currency)}`);
    }
  }

  separator();

  // Totals
  push(CMD.BOLD_ON);
  line(padLine("Subtotal:", formatCurrency(invoice.subtotal, options.currency), w));

  if (options.showGST && invoice.tax > 0) {
    line(padLine("Tax/GST:", formatCurrency(invoice.tax, options.currency), w));
  }
  if (options.showVAT && invoice.tax > 0) {
    line(padLine("VAT:", formatCurrency(invoice.tax, options.currency), w));
  }

  push(CMD.DOUBLE_HEIGHT);
  line(padLine("TOTAL:", formatCurrency(invoice.total_amount, options.currency), w));
  push(CMD.NORMAL_SIZE, CMD.BOLD_OFF);

  separator();

  // Footer
  push(CMD.ALIGN_CENTER);
  line(options.footerText || "Thank you for your business!");
  line("Powered by StockPilot");

  // Feed & cut
  push(CMD.FEED_5, CMD.PARTIAL_CUT);

  return new Uint8Array(bytes);
}

/**
 * Generate ESC/POS cash drawer open command.
 */
export function cashDrawerCommand(): Uint8Array {
  return new Uint8Array(CMD.CASH_DRAWER);
}

/**
 * Generate printable HTML receipt preview.
 */
export function formatReceiptHTML(invoice: Invoice, options: ReceiptOptions): string {
  const width = options.paperWidth === 58 ? "58mm" : "80mm";
  const cur = (amount: number) => formatCurrency(amount, options.currency);

  const itemRows = invoice.items
    .map(
      (item) => `
    <tr>
      <td>${item.product_name || "Item"}</td>
      <td class="qty">${item.quantity}</td>
      <td class="price">${cur(item.price_per_unit)}</td>
      <td class="amount">${cur(item.quantity * item.price_per_unit)}</td>
    </tr>
    ${
      options.showGST && item.gst_percentage
        ? `<tr class="tax-row"><td colspan="3">GST ${item.gst_percentage}%</td><td class="amount">${cur((item.cgst_amount || 0) + (item.sgst_amount || 0))}</td></tr>`
        : ""
    }`
    )
    .join("");

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Receipt - ${invoice.invoice_number || ""}</title>
<style>
  @media print {
    @page { margin: 0; size: ${width} auto; }
    body { margin: 0; }
  }
  body {
    font-family: 'Courier New', monospace;
    font-size: 12px;
    width: ${width};
    margin: 0 auto;
    padding: 8px;
    color: #000;
  }
  .header { text-align: center; margin-bottom: 8px; }
  .store-name { font-size: 18px; font-weight: bold; }
  .separator { border-top: 1px dashed #000; margin: 6px 0; }
  table { width: 100%; border-collapse: collapse; }
  td { padding: 2px 0; vertical-align: top; }
  .qty, .price, .amount { text-align: right; }
  .tax-row td { font-size: 10px; color: #555; }
  .totals td { font-weight: bold; }
  .total-row td { font-size: 16px; font-weight: bold; border-top: 2px solid #000; padding-top: 4px; }
  .footer { text-align: center; margin-top: 10px; font-size: 10px; }
</style>
</head>
<body>
  <div class="header">
    <div class="store-name">${options.storeName}</div>
    ${options.storeAddress ? `<div>${options.storeAddress}</div>` : ""}
    ${options.storePhone ? `<div>Tel: ${options.storePhone}</div>` : ""}
    ${options.storeGSTIN ? `<div>GSTIN: ${options.storeGSTIN}</div>` : ""}
  </div>

  <div class="separator"></div>

  <div>
    ${invoice.invoice_number ? `<div>Invoice: ${invoice.invoice_number}</div>` : ""}
    ${invoice.created_at ? `<div>Date: ${new Date(invoice.created_at).toLocaleString()}</div>` : ""}
    ${invoice.customer_name ? `<div>Customer: ${invoice.customer_name}</div>` : ""}
  </div>

  <div class="separator"></div>

  <table>
    <tr style="font-weight:bold">
      <td>Item</td><td class="qty">Qty</td><td class="price">Price</td><td class="amount">Amount</td>
    </tr>
    ${itemRows}
  </table>

  <div class="separator"></div>

  <table class="totals">
    <tr><td>Subtotal</td><td class="amount">${cur(invoice.subtotal)}</td></tr>
    ${options.showGST && invoice.tax > 0 ? `<tr><td>Tax/GST</td><td class="amount">${cur(invoice.tax)}</td></tr>` : ""}
    ${options.showVAT && invoice.tax > 0 ? `<tr><td>VAT</td><td class="amount">${cur(invoice.tax)}</td></tr>` : ""}
    <tr class="total-row"><td>TOTAL</td><td class="amount">${cur(invoice.total_amount)}</td></tr>
  </table>

  <div class="separator"></div>

  <div class="footer">
    <div>${options.footerText || "Thank you for your business!"}</div>
    <div>Powered by StockPilot</div>
  </div>
</body>
</html>`;
}

/**
 * Convert receipt bytes to base64 (for Tauri/mobile native bridge).
 */
export function receiptToBase64(bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}
