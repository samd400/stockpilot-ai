/**
 * POS Screen — cart management, checkout, and receipt printing (mobile).
 */

import React, { useState, useEffect } from "react";
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert, TextInput } from "react-native";
import TcpSocket from "react-native-tcp-socket";
import { formatReceiptESCPOS, type ReceiptOptions, type Invoice, type Product } from "@stockpilot/sdk";

const API_BASE = "http://localhost:8000"; // Replace with your server IP

interface CartItem {
  product: Product;
  quantity: number;
}

export default function POSScreen({ route }: any) {
  const [cart, setCart] = useState<CartItem[]>([]);
  const [printerIp, setPrinterIp] = useState("192.168.1.100");

  // If navigated from scanner, look up product and add
  useEffect(() => {
    if (route?.params?.barcode) {
      lookupAndAdd(route.params.barcode);
    }
  }, [route?.params?.barcode]);

  async function lookupAndAdd(barcode: string) {
    try {
      // TODO: Use local SQLite for offline lookup
      const token = ""; // Get from SecureStore
      const res = await fetch(`${API_BASE}/products?barcode=${barcode}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const products = await res.json();
        if (products.length > 0) addToCart(products[0]);
        else Alert.alert("Not Found", `No product found for barcode: ${barcode}`);
      }
    } catch {
      Alert.alert("Offline", "Product lookup failed. Ensure you're connected.");
    }
  }

  function addToCart(product: Product) {
    setCart((prev) => {
      const existing = prev.find((c) => c.product.id === product.id);
      if (existing) return prev.map((c) => c.product.id === product.id ? { ...c, quantity: c.quantity + 1 } : c);
      return [...prev, { product, quantity: 1 }];
    });
  }

  function removeItem(productId: string) {
    setCart((prev) => prev.filter((c) => c.product.id !== productId));
  }

  const subtotal = cart.reduce((s, c) => s + c.product.selling_price * c.quantity, 0);
  const tax = subtotal * 0.18;
  const total = subtotal + tax;

  async function handleCheckout() {
    if (cart.length === 0) return;

    const invoice: Invoice = {
      invoice_number: `M-${Date.now().toString(36).toUpperCase()}`,
      items: cart.map((c) => ({
        product_id: c.product.id,
        product_name: c.product.product_name,
        quantity: c.quantity,
        price_per_unit: c.product.selling_price,
      })),
      subtotal,
      tax,
      total_amount: total,
      currency: "INR",
      created_at: new Date().toISOString(),
    };

    Alert.alert("Bill Created", `Total: ₹${total.toFixed(2)}`, [
      { text: "Print Receipt", onPress: () => printReceipt(invoice) },
      { text: "Done", onPress: () => setCart([]) },
    ]);
  }

  async function printReceipt(invoice: Invoice) {
    const options: ReceiptOptions = {
      paperWidth: 80,
      currency: "INR",
      showGST: true,
      showVAT: false,
      storeName: "StockPilot Store",
    };

    const bytes = formatReceiptESCPOS(invoice, options);

    try {
      await sendToNetworkPrinter(printerIp, 9100, bytes);
      Alert.alert("Printed", "Receipt sent to printer");
      setCart([]);
    } catch (err: any) {
      Alert.alert("Print Failed", err.message || "Could not connect to printer");
    }
  }

  function sendToNetworkPrinter(ip: string, port: number, data: Uint8Array): Promise<void> {
    return new Promise((resolve, reject) => {
      const client = TcpSocket.createConnection({ port, host: ip }, () => {
        client.write(Buffer.from(data));
        client.destroy();
        resolve();
      });
      client.on("error", (err) => reject(err));
      setTimeout(() => { client.destroy(); reject(new Error("Timeout")); }, 5000);
    });
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={cart}
        keyExtractor={(c) => c.product.id}
        ListEmptyComponent={<Text style={styles.empty}>Scan a barcode to add products</Text>}
        renderItem={({ item }) => (
          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <Text style={styles.name}>{item.product.product_name}</Text>
              <Text style={styles.price}>₹{item.product.selling_price} × {item.quantity}</Text>
            </View>
            <Text style={styles.amount}>₹{(item.product.selling_price * item.quantity).toFixed(2)}</Text>
            <TouchableOpacity onPress={() => removeItem(item.product.id)}>
              <Text style={styles.remove}>✕</Text>
            </TouchableOpacity>
          </View>
        )}
      />

      <View style={styles.footer}>
        <View style={styles.totalRow}>
          <Text style={styles.totalLabel}>Subtotal</Text>
          <Text>₹{subtotal.toFixed(2)}</Text>
        </View>
        <View style={styles.totalRow}>
          <Text style={styles.totalLabel}>GST (18%)</Text>
          <Text>₹{tax.toFixed(2)}</Text>
        </View>
        <View style={styles.totalRow}>
          <Text style={styles.grandTotal}>Total</Text>
          <Text style={styles.grandTotal}>₹{total.toFixed(2)}</Text>
        </View>

        <TextInput
          style={styles.input}
          value={printerIp}
          onChangeText={setPrinterIp}
          placeholder="Printer IP (e.g. 192.168.1.100)"
        />

        <TouchableOpacity style={styles.checkoutBtn} onPress={handleCheckout} disabled={cart.length === 0}>
          <Text style={styles.checkoutText}>💰 Charge ₹{total.toFixed(2)}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f9fafb" },
  empty: { textAlign: "center", color: "#999", padding: 40 },
  row: { flexDirection: "row", alignItems: "center", padding: 14, borderBottomWidth: 1, borderBottomColor: "#f0f0f0", backgroundColor: "#fff" },
  name: { fontWeight: "bold", fontSize: 15 },
  price: { color: "#666", fontSize: 13 },
  amount: { fontWeight: "bold", fontSize: 15, marginRight: 12 },
  remove: { color: "#dc2626", fontSize: 18, paddingHorizontal: 8 },
  footer: { padding: 16, borderTopWidth: 1, borderTopColor: "#e5e7eb", backgroundColor: "#fff" },
  totalRow: { flexDirection: "row", justifyContent: "space-between", marginBottom: 4 },
  totalLabel: { color: "#6b7280" },
  grandTotal: { fontWeight: "bold", fontSize: 20 },
  input: { borderWidth: 1, borderColor: "#d1d5db", borderRadius: 8, padding: 10, marginVertical: 10, fontSize: 14 },
  checkoutBtn: { backgroundColor: "#16a34a", borderRadius: 12, padding: 16, alignItems: "center" },
  checkoutText: { color: "#fff", fontWeight: "bold", fontSize: 18 },
});
