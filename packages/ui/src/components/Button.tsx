import React from "react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  variant = "primary",
  size = "md",
  loading = false,
  children,
  disabled,
  style,
  ...props
}) => {
  const baseStyle: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: "8px",
    fontWeight: 600,
    cursor: disabled || loading ? "not-allowed" : "pointer",
    opacity: disabled || loading ? 0.6 : 1,
    border: "none",
    transition: "all 0.15s ease",
  };

  const sizes: Record<string, React.CSSProperties> = {
    sm: { padding: "6px 12px", fontSize: "13px" },
    md: { padding: "10px 20px", fontSize: "14px" },
    lg: { padding: "14px 28px", fontSize: "16px" },
  };

  const variants: Record<string, React.CSSProperties> = {
    primary: { background: "#2563eb", color: "#fff" },
    secondary: { background: "#e5e7eb", color: "#374151" },
    danger: { background: "#dc2626", color: "#fff" },
    ghost: { background: "transparent", color: "#2563eb", border: "1px solid #2563eb" },
  };

  return (
    <button
      disabled={disabled || loading}
      style={{ ...baseStyle, ...sizes[size], ...variants[variant], ...style }}
      {...props}
    >
      {loading ? "..." : children}
    </button>
  );
};
