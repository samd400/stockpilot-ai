import React from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({ label, error, style, ...props }) => {
  return (
    <div style={{ marginBottom: "12px" }}>
      {label && (
        <label style={{ display: "block", marginBottom: "4px", fontSize: "13px", fontWeight: 500, color: "#374151" }}>
          {label}
        </label>
      )}
      <input
        style={{
          width: "100%",
          padding: "10px 12px",
          borderRadius: "8px",
          border: error ? "1px solid #dc2626" : "1px solid #d1d5db",
          fontSize: "14px",
          outline: "none",
          boxSizing: "border-box",
          ...style,
        }}
        {...props}
      />
      {error && <span style={{ fontSize: "12px", color: "#dc2626", marginTop: "2px" }}>{error}</span>}
    </div>
  );
};
