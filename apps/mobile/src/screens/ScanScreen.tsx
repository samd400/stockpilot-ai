/**
 * Barcode Scanner Screen — uses expo-barcode-scanner for camera scanning.
 */

import React, { useState, useEffect } from "react";
import { View, Text, StyleSheet, Alert, TextInput, TouchableOpacity } from "react-native";
import { BarCodeScanner } from "expo-barcode-scanner";

export default function ScanScreen({ navigation }: any) {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [scanned, setScanned] = useState(false);
  const [manualCode, setManualCode] = useState("");

  useEffect(() => {
    (async () => {
      const { status } = await BarCodeScanner.requestPermissionsAsync();
      setHasPermission(status === "granted");
    })();
  }, []);

  const handleBarCodeScanned = ({ type, data }: { type: string; data: string }) => {
    setScanned(true);
    Alert.alert("Barcode Scanned", `Type: ${type}\nCode: ${data}`, [
      { text: "Add to Cart", onPress: () => navigation.navigate("POS", { barcode: data }) },
      { text: "Scan Again", onPress: () => setScanned(false) },
    ]);
  };

  const handleManualEntry = () => {
    if (manualCode.trim()) {
      navigation.navigate("POS", { barcode: manualCode.trim() });
      setManualCode("");
    }
  };

  if (hasPermission === null) {
    return <View style={styles.container}><Text>Requesting camera permission...</Text></View>;
  }
  if (hasPermission === false) {
    return (
      <View style={styles.container}>
        <Text style={styles.error}>Camera permission denied</Text>
        <Text style={styles.subtitle}>Enter barcode manually below</Text>
        <View style={styles.manualRow}>
          <TextInput
            style={styles.input}
            value={manualCode}
            onChangeText={setManualCode}
            placeholder="Enter barcode or SKU"
            onSubmitEditing={handleManualEntry}
          />
          <TouchableOpacity style={styles.btn} onPress={handleManualEntry}>
            <Text style={styles.btnText}>Search</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <BarCodeScanner
        onBarCodeScanned={scanned ? undefined : handleBarCodeScanned}
        style={StyleSheet.absoluteFillObject}
      />

      {/* Overlay */}
      <View style={styles.overlay}>
        <View style={styles.scanBox} />
        <Text style={styles.hint}>Point camera at barcode</Text>
      </View>

      {/* Manual entry fallback */}
      <View style={styles.manualBar}>
        <TextInput
          style={styles.inputDark}
          value={manualCode}
          onChangeText={setManualCode}
          placeholder="Or type barcode/SKU..."
          placeholderTextColor="#999"
          onSubmitEditing={handleManualEntry}
        />
        <TouchableOpacity style={styles.btn} onPress={handleManualEntry}>
          <Text style={styles.btnText}>Go</Text>
        </TouchableOpacity>
      </View>

      {scanned && (
        <TouchableOpacity style={styles.rescan} onPress={() => setScanned(false)}>
          <Text style={styles.rescanText}>Tap to Scan Again</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000" },
  overlay: { flex: 1, justifyContent: "center", alignItems: "center" },
  scanBox: { width: 250, height: 250, borderWidth: 2, borderColor: "#2563eb", borderRadius: 16 },
  hint: { color: "#fff", marginTop: 16, fontSize: 14 },
  manualBar: {
    position: "absolute", bottom: 40, left: 20, right: 20,
    flexDirection: "row", gap: 8,
  },
  manualRow: { flexDirection: "row", gap: 8, paddingHorizontal: 20, marginTop: 16 },
  input: { flex: 1, backgroundColor: "#fff", borderRadius: 8, padding: 12, fontSize: 16 },
  inputDark: { flex: 1, backgroundColor: "rgba(255,255,255,0.15)", borderRadius: 8, padding: 12, fontSize: 16, color: "#fff" },
  btn: { backgroundColor: "#2563eb", borderRadius: 8, paddingHorizontal: 20, justifyContent: "center" },
  btnText: { color: "#fff", fontWeight: "bold", fontSize: 16 },
  rescan: { position: "absolute", bottom: 100, alignSelf: "center", backgroundColor: "#2563eb", padding: 14, borderRadius: 12 },
  rescanText: { color: "#fff", fontWeight: "bold" },
  error: { fontSize: 18, fontWeight: "bold", color: "#dc2626", textAlign: "center", marginTop: 60 },
  subtitle: { fontSize: 14, color: "#666", textAlign: "center", marginTop: 8, marginBottom: 20 },
});
