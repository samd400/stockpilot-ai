/**
 * Settings Screen — printer config, device pairing, sync status.
 */

import React, { useState, useEffect } from "react";
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, Switch } from "react-native";
import * as SecureStore from "expo-secure-store";

export default function SettingsScreen() {
  const [serverUrl, setServerUrl] = useState("http://localhost:8000");
  const [printerIp, setPrinterIp] = useState("192.168.1.100");
  const [printerPort, setPrinterPort] = useState("9100");
  const [deviceToken, setDeviceToken] = useState("");
  const [kioskMode, setKioskMode] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    const url = await SecureStore.getItemAsync("server_url");
    const ip = await SecureStore.getItemAsync("printer_ip");
    const port = await SecureStore.getItemAsync("printer_port");
    const token = await SecureStore.getItemAsync("device_token");
    if (url) setServerUrl(url);
    if (ip) setPrinterIp(ip);
    if (port) setPrinterPort(port);
    if (token) setDeviceToken(token);
  }

  async function saveSettings() {
    await SecureStore.setItemAsync("server_url", serverUrl);
    await SecureStore.setItemAsync("printer_ip", printerIp);
    await SecureStore.setItemAsync("printer_port", printerPort);
    Alert.alert("Saved", "Settings saved securely");
  }

  async function handlePairDevice() {
    try {
      const res = await fetch(`${serverUrl}/devices/claim`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pairing_token: deviceToken,
          device_metadata: { platform: "mobile", app_version: "2.0.0" },
        }),
      });
      if (res.ok) {
        const data = await res.json();
        await SecureStore.setItemAsync("device_token", data.device_token);
        await SecureStore.setItemAsync("device_id", data.device_id);
        Alert.alert("Paired", "Device paired successfully!");
      } else {
        Alert.alert("Error", "Pairing failed. Check token.");
      }
    } catch (err: any) {
      Alert.alert("Error", err.message || "Network error");
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.section}>Server</Text>
      <TextInput style={styles.input} value={serverUrl} onChangeText={setServerUrl} placeholder="API Server URL" />

      <Text style={styles.section}>Printer</Text>
      <TextInput style={styles.input} value={printerIp} onChangeText={setPrinterIp} placeholder="Printer IP" />
      <TextInput style={styles.input} value={printerPort} onChangeText={setPrinterPort} placeholder="Port (9100)" keyboardType="numeric" />

      <Text style={styles.section}>Device Pairing</Text>
      <TextInput style={styles.input} value={deviceToken} onChangeText={setDeviceToken} placeholder="Enter pairing token" />
      <TouchableOpacity style={styles.pairBtn} onPress={handlePairDevice}>
        <Text style={styles.pairText}>🔗 Pair Device</Text>
      </TouchableOpacity>

      <Text style={styles.section}>Kiosk Mode</Text>
      <View style={styles.row}>
        <Text>Enable Kiosk (auto-login)</Text>
        <Switch value={kioskMode} onValueChange={setKioskMode} />
      </View>

      <TouchableOpacity style={styles.saveBtn} onPress={saveSettings}>
        <Text style={styles.saveText}>💾 Save Settings</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: "#f9fafb" },
  section: { fontSize: 16, fontWeight: "bold", color: "#374151", marginTop: 20, marginBottom: 8 },
  input: { backgroundColor: "#fff", borderWidth: 1, borderColor: "#d1d5db", borderRadius: 8, padding: 12, fontSize: 15, marginBottom: 8 },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 16 },
  pairBtn: { backgroundColor: "#7c3aed", borderRadius: 8, padding: 14, alignItems: "center", marginTop: 8 },
  pairText: { color: "#fff", fontWeight: "bold", fontSize: 16 },
  saveBtn: { backgroundColor: "#2563eb", borderRadius: 12, padding: 16, alignItems: "center", marginTop: 24 },
  saveText: { color: "#fff", fontWeight: "bold", fontSize: 16 },
});
