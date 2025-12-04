import React from "react";
import { View, Text, ActivityIndicator, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

interface LoadingProps {
  message?: string;
  size?: "small" | "large";
  style?: "default" | "overlay";
}

export function Loading({ message = "Loading...", size = "large", style = "default" }: LoadingProps) {
  if (style === "overlay") {
    return (
      <View style={styles.overlay}>
        <LinearGradient colors={["#1B4D3E", "#14352B"]} style={styles.overlayBox}>
          <ActivityIndicator size={size} color="#F4D03F" />
          <Text style={styles.message}>{message}</Text>
        </LinearGradient>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <LinearGradient colors={["#1B4D3E", "#14352B"]} style={styles.box}>
        <ActivityIndicator size={size} color="#F4D03F" />
        <Text style={styles.message}>{message}</Text>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0D1F17",
    alignItems: "center",
    justifyContent: "center",
  },
  overlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(13, 31, 23, 0.8)",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 50,
  },
  box: {
    padding: 32,
    borderRadius: 24,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "rgba(244, 208, 63, 0.2)",
  },
  overlayBox: {
    padding: 24,
    borderRadius: 16,
    alignItems: "center",
  },
  message: {
    color: "#F4D03F",
    marginTop: 24,
    fontSize: 18,
  },
});
