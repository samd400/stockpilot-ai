import React from "react";
import type { Invoice, ReceiptOptions } from "@stockpilot/sdk";
import { formatReceiptHTML } from "@stockpilot/sdk";

export interface ReceiptViewProps {
  invoice: Invoice;
  options: ReceiptOptions;
  onPrint?: () => void;
}

/**
 * ReceiptView — renders an HTML receipt preview with print button.
 */
export const ReceiptView: React.FC<ReceiptViewProps> = ({ invoice, options, onPrint }) => {
  const html = formatReceiptHTML(invoice, options);

  const handlePrint = () => {
    if (onPrint) {
      onPrint();
      return;
    }
    // Default: open print window
    const win = window.open("", "_blank", "width=400,height=600");
    if (!win) return;
    win.document.write(html);
    win.document.close();
    win.focus();
    setTimeout(() => { win.print(); win.close(); }, 250);
  };

  return (
    <div>
      <div
        style={{
          border: "1px solid #e5e7eb",
          borderRadius: "8px",
          maxWidth: options.paperWidth === 58 ? "232px" : "320px",
          margin: "0 auto",
          background: "#fff",
          boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
        }}
      >
        <div dangerouslySetInnerHTML={{ __html: html }} />
      </div>
      <div style={{ textAlign: "center", marginTop: "12px" }}>
        <button
          onClick={handlePrint}
          style={{
            padding: "10px 24px",
            background: "#2563eb",
            color: "#fff",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: "14px",
          }}
        >
          🖨️ Print Receipt
        </button>
      </div>
    </div>
  );
};
