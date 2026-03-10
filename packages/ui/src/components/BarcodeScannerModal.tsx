import React, { useEffect, useRef, useState, useCallback } from "react";
import { Button } from "./Button";
import { Input } from "./Input";

export interface BarcodeScannerModalProps {
  open: boolean;
  onClose: () => void;
  onScan: (barcode: string) => void;
  /** If true, use QuaggaJS camera scanner. If false or unavailable, show manual input. */
  enableCamera?: boolean;
}

/**
 * Barcode Scanner Modal — camera scanning via QuaggaJS with manual SKU fallback.
 * QuaggaJS must be loaded externally (script tag or import).
 */
export const BarcodeScannerModal: React.FC<BarcodeScannerModalProps> = ({
  open,
  onClose,
  onScan,
  enableCamera = true,
}) => {
  const [manualCode, setManualCode] = useState("");
  const [cameraActive, setCameraActive] = useState(false);
  const [error, setError] = useState("");
  const videoRef = useRef<HTMLDivElement>(null);

  const startCamera = useCallback(async () => {
    if (!enableCamera) return;
    try {
      // Dynamic import for QuaggaJS (must be installed: npm i @ericblade/quagga2)
      const Quagga = (await import("@ericblade/quagga2")).default;
      if (!videoRef.current) return;

      Quagga.init(
        {
          inputStream: {
            type: "LiveStream",
            target: videoRef.current,
            constraints: { facingMode: "environment", width: 640, height: 480 },
          },
          decoder: {
            readers: [
              "ean_reader",
              "ean_8_reader",
              "code_128_reader",
              "code_39_reader",
              "upc_reader",
              "upc_e_reader",
            ],
          },
          locate: true,
        },
        (err: any) => {
          if (err) {
            setError("Camera not available. Use manual entry.");
            setCameraActive(false);
            return;
          }
          Quagga.start();
          setCameraActive(true);
        }
      );

      Quagga.onDetected((result: any) => {
        const code = result.codeResult?.code;
        if (code) {
          Quagga.stop();
          setCameraActive(false);
          onScan(code);
        }
      });
    } catch {
      setError("Barcode scanner library not available. Use manual entry.");
    }
  }, [enableCamera, onScan]);

  const stopCamera = useCallback(async () => {
    try {
      const Quagga = (await import("@ericblade/quagga2")).default;
      Quagga.stop();
    } catch {}
    setCameraActive(false);
  }, []);

  useEffect(() => {
    if (open && enableCamera) startCamera();
    return () => { stopCamera(); };
  }, [open, enableCamera, startCamera, stopCamera]);

  const handleManualSubmit = () => {
    if (manualCode.trim()) {
      onScan(manualCode.trim());
      setManualCode("");
    }
  };

  if (!open) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
      }}
    >
      <div style={{ background: "#fff", borderRadius: "16px", padding: "24px", width: "420px", maxWidth: "95vw" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "16px" }}>
          <h2 style={{ margin: 0, fontSize: "18px" }}>Scan Barcode</h2>
          <button onClick={() => { stopCamera(); onClose(); }} style={{ background: "none", border: "none", fontSize: "20px", cursor: "pointer" }}>
            ✕
          </button>
        </div>

        {/* Camera viewport */}
        {enableCamera && (
          <div
            ref={videoRef}
            style={{
              width: "100%",
              height: "240px",
              background: "#000",
              borderRadius: "8px",
              overflow: "hidden",
              marginBottom: "12px",
              position: "relative",
            }}
          >
            {!cameraActive && (
              <div style={{ color: "#fff", textAlign: "center", paddingTop: "100px", fontSize: "14px" }}>
                {error || "Starting camera..."}
              </div>
            )}
          </div>
        )}

        {/* Manual entry fallback */}
        <div style={{ display: "flex", gap: "8px" }}>
          <div style={{ flex: 1 }}>
            <Input
              placeholder="Enter barcode or SKU manually"
              value={manualCode}
              onChange={(e) => setManualCode(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleManualSubmit()}
            />
          </div>
          <Button onClick={handleManualSubmit} size="md">
            Search
          </Button>
        </div>
      </div>
    </div>
  );
};
