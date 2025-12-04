import React from "react";
import { View, Text, ActivityIndicator, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

interface LoadingProps {
  message?: string;
  fullScreen?: boolean;
}

export function Loading({ message = "Loading...", fullScreen = true }: LoadingProps) {
  const content = (
    <View style={styles.container}>
      <View style={styles.loaderContainer}>
        <ActivityIndicator size="large" color="#F4D03F" />
        <Text style={styles.message}>{message}</Text>
      </View>
    </View>
  );

  if (fullScreen) {
    return (
      <LinearGradient colors={["#0D1F17", "#1B4D3E"]} style={styles.fullScreen}>
        {content}
      </LinearGradient>
    );
  }

  return content;
}

const styles = StyleSheet.create({
  fullScreen: { flex: 1 },
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  loaderContainer: {
    backgroundColor: "rgba(27, 77, 62, 0.9)",
    borderRadius: 16,
    padding: 24,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
  },
  message: {
    color: "#F4D03F",
    fontSize: 16,
    marginTop: 16,
    textAlign: "center",
  },
});