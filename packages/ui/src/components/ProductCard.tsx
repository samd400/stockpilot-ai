import React from "react";
import type { Product } from "@stockpilot/sdk";

export interface ProductCardProps {
  product: Product;
  onAdd?: (product: Product) => void;
  compact?: boolean;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product, onAdd, compact = false }) => {
  const formatPrice = (price: number) => {
    const symbols: Record<string, string> = { INR: "₹", USD: "$", EUR: "€", GBP: "£", AED: "AED " };
    const sym = symbols[product.currency || "INR"] || (product.currency || "") + " ";
    return `${sym}${price.toFixed(2)}`;
  };

  if (compact) {
    return (
      <div
        onClick={() => onAdd?.(product)}
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "10px 14px",
          borderBottom: "1px solid #f0f0f0",
          cursor: "pointer",
        }}
      >
        <div>
          <div style={{ fontWeight: 600, fontSize: "14px" }}>{product.product_name}</div>
          <div style={{ fontSize: "12px", color: "#666" }}>
            {product.sku || ""} · Stock: {product.stock_quantity}
          </div>
        </div>
        <div style={{ fontWeight: 700, color: "#2563eb" }}>{formatPrice(product.selling_price)}</div>
      </div>
    );
  }

  return (
    <div
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: "12px",
        padding: "16px",
        background: "#fff",
      }}
    >
      <h3 style={{ margin: "0 0 8px", fontSize: "16px" }}>{product.product_name}</h3>
      <p style={{ margin: "0 0 4px", fontSize: "13px", color: "#666" }}>
        SKU: {product.sku || "N/A"} · Stock: {product.stock_quantity}
      </p>
      <p style={{ margin: "0 0 12px", fontSize: "18px", fontWeight: 700, color: "#2563eb" }}>
        {formatPrice(product.selling_price)}
      </p>
      {onAdd && (
        <button
          onClick={() => onAdd(product)}
          style={{
            width: "100%",
            padding: "8px",
            background: "#2563eb",
            color: "#fff",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          Add to Cart
        </button>
      )}
    </div>
  );
};
