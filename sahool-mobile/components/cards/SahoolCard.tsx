import React from "react";
import { View, Text, TouchableOpacity, StyleSheet, ViewStyle } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Animated from "react-native-reanimated";
import { usePressAnimation } from "@/hooks/useMicroInteraction";

interface SahoolCardProps {
  icon: React.ReactNode;
  title: string;
  value: string | number;
  subtitle?: string;
  gradient?: [string, string];
  onPress?: () => void;
  style?: ViewStyle;
  trend?: { value: string; isPositive: boolean };
  rightContent?: React.ReactNode;
}

const AnimatedTouchable = Animated.createAnimatedComponent(TouchableOpacity);

export function SahoolCard({
  icon,
  title,
  value,
  subtitle,
  gradient = ["#1B4D3E", "#14352B"],
  onPress,
  style,
  trend,
  rightContent,
}: SahoolCardProps) {
  const { pressIn, pressOut, animatedStyle } = usePressAnimation();

  return (
    <AnimatedTouchable
      onPress={onPress}
      onPressIn={pressIn}
      onPressOut={pressOut}
      disabled={!onPress}
      style={[animatedStyle, { flex: 1 }, style]}
      activeOpacity={0.8}
    >
      <LinearGradient colors={gradient} start={[0, 0]} end={[1, 1]} style={styles.card}>
        <View style={styles.header}>
          <View style={styles.iconContainer}>{icon}</View>
          {rightContent}
        </View>

        <View style={styles.content}>
          <Text style={styles.title}>{title}</Text>
          <View style={styles.valueRow}>
            <Text style={styles.value}>{value}</Text>
            {trend && (
              <View style={[styles.trendBadge, { backgroundColor: trend.isPositive ? "#27AE6020" : "#E74C3C20" }]}>
                <Text style={[styles.trendText, { color: trend.isPositive ? "#27AE60" : "#E74C3C" }]}>
                  {trend.isPositive ? "↑" : "↓"} {trend.value}
                </Text>
              </View>
            )}
          </View>
          {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
        </View>
      </LinearGradient>
    </AnimatedTouchable>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 12,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: "rgba(244, 208, 63, 0.2)",
    justifyContent: "center",
    alignItems: "center",
  },
  content: { gap: 4 },
  title: { color: "rgba(255, 255, 255, 0.7)", fontSize: 14 },
  valueRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  value: { color: "#FFFFFF", fontSize: 28, fontWeight: "700" },
  trendBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },
  trendText: { fontSize: 12, fontWeight: "600" },
  subtitle: { color: "rgba(255, 255, 255, 0.5)", fontSize: 12, marginTop: 4 },
});