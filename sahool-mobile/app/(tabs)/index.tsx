import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";

export default function DashboardScreen() {
  const insets = useSafeAreaInsets();

  return (
    <LinearGradient colors={["#0D1F17", "#1B4D3E"]} style={styles.container}>
      <View style={[styles.content, { paddingTop: insets.top + 20 }]}>
        <Text style={styles.title}>SAHOOL Dashboard</Text>
        <Text style={styles.subtitle}>Smart Agriculture Platform</Text>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { flex: 1, padding: 16, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 28, fontWeight: "700", color: "#FFFFFF" },
  subtitle: { fontSize: 16, color: "#F4D03F", marginTop: 8 },
});