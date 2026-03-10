/**
 * Home Screen — main dashboard with quick actions.
 */

import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";

export default function HomeScreen({ navigation }: any) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>StockPilot POS</Text>
      <Text style={styles.subtitle}>AI-Powered Inventory & Billing</Text>

      <View style={styles.grid}>
        <TouchableOpacity style={styles.card} onPress={() => navigation.navigate("Scan")}>
          <Text style={styles.cardIcon}>📷</Text>
          <Text style={styles.cardTitle}>Scan Barcode</Text>
          <Text style={styles.cardDesc}>Scan products to add to cart</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.card} onPress={() => navigation.navigate("POS")}>
          <Text style={styles.cardIcon}>🛒</Text>
          <Text style={styles.cardTitle}>POS Billing</Text>
          <Text style={styles.cardDesc}>Create invoices & print receipts</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.card} onPress={() => navigation.navigate("Settings")}>
          <Text style={styles.cardIcon}>⚙️</Text>
          <Text style={styles.cardTitle}>Settings</Text>
          <Text style={styles.cardDesc}>Printer, sync & device config</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: "#f9fafb" },
  title: { fontSize: 28, fontWeight: "bold", color: "#2563eb", textAlign: "center", marginTop: 40 },
  subtitle: { fontSize: 14, color: "#6b7280", textAlign: "center", marginBottom: 40 },
  grid: { gap: 16 },
  card: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  cardIcon: { fontSize: 32, marginBottom: 8 },
  cardTitle: { fontSize: 18, fontWeight: "bold", color: "#111827" },
  cardDesc: { fontSize: 13, color: "#6b7280", marginTop: 4 },
});
