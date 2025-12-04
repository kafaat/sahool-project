import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

export default function AssistantScreen() {
  return (
    <LinearGradient colors={["#0D1F17", "#1B4D3E"]} style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>AI Assistant</Text>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { flex: 1, padding: 16, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 28, fontWeight: "700", color: "#FFFFFF" },
});