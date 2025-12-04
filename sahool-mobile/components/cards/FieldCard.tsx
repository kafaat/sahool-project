import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { MapPin, Leaf, Droplets, Activity } from "lucide-react-native";
import Animated from "react-native-reanimated";
import { usePressAnimation } from "@/hooks/useMicroInteraction";
import { Field } from "@/types";

interface FieldCardProps {
  field: Field;
  onPress?: () => void;
  selected?: boolean;
}

const AnimatedTouchable = Animated.createAnimatedComponent(TouchableOpacity);

export function FieldCard({ field, onPress, selected }: FieldCardProps) {
  const { pressIn, pressOut, animatedStyle } = usePressAnimation();

  const getStatusBadgeColor = (status: string): [string, string] => {
    switch (status) {
      case "healthy": return ["#27AE60", "#2ECC71"];
      case "warning": return ["#F39C12", "#E67E22"];
      case "critical": return ["#E74C3C", "#C0392B"];
      default: return ["#7F8C8D", "#95A5A6"];
    }
  };

  const getStatusText = (status: string): string => {
    switch (status) {
      case "healthy": return "Healthy";
      case "warning": return "Warning";
      case "critical": return "Critical";
      default: return "Inactive";
    }
  };

  return (
    <AnimatedTouchable
      onPress={onPress}
      onPressIn={pressIn}
      onPressOut={pressOut}
      style={animatedStyle}
      activeOpacity={0.8}
    >
      <LinearGradient
        colors={["#1B4D3E", "#14352B"]}
        start={[0, 0]}
        end={[1, 1]}
        style={[styles.card, selected && styles.selectedCard]}
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <View style={[styles.colorDot, { backgroundColor: field.color || "#4CAF50" }]} />
            <View>
              <Text style={styles.fieldName}>{field.nameAr || field.name}</Text>
              <Text style={styles.cropType}>{field.cropType}</Text>
            </View>
          </View>
          <LinearGradient colors={getStatusBadgeColor(field.status)} style={styles.statusBadge}>
            <Text style={styles.statusText}>{getStatusText(field.status)}</Text>
          </LinearGradient>
        </View>

        {/* Stats Grid */}
        <View style={styles.statsGrid}>
          <View style={styles.statItem}>
            <View style={[styles.statIcon, { backgroundColor: "rgba(39, 174, 96, 0.2)" }]}>
              <Leaf size={16} color="#27AE60" />
            </View>
            <Text style={styles.statValue}>{field.healthScore}%</Text>
            <Text style={styles.statLabel}>Health</Text>
          </View>

          <View style={styles.statItem}>
            <View style={[styles.statIcon, { backgroundColor: "rgba(244, 208, 63, 0.2)" }]}>
              <Activity size={16} color="#F4D03F" />
            </View>
            <Text style={styles.statValue}>{field.ndviValue.toFixed(2)}</Text>
            <Text style={styles.statLabel}>NDVI</Text>
          </View>

          <View style={styles.statItem}>
            <View style={[styles.statIcon, { backgroundColor: "rgba(52, 152, 219, 0.2)" }]}>
              <Droplets size={16} color="#3498DB" />
            </View>
            <Text style={styles.statValue}>{field.moistureLevel}%</Text>
            <Text style={styles.statLabel}>Moisture</Text>
          </View>

          <View style={styles.statItem}>
            <View style={[styles.statIcon, { backgroundColor: "rgba(155, 89, 182, 0.2)" }]}>
              <MapPin size={16} color="#9B59B6" />
            </View>
            <Text style={styles.statValue}>{field.acreage}</Text>
            <Text style={styles.statLabel}>Hectares</Text>
          </View>
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
    marginBottom: 12,
  },
  selectedCard: {
    borderColor: "#F4D03F",
    borderWidth: 2,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  },
  headerLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  colorDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  fieldName: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "700",
  },
  cropType: {
    color: "rgba(255, 255, 255, 0.6)",
    fontSize: 12,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    color: "#FFFFFF",
    fontSize: 11,
    fontWeight: "600",
  },
  statsGrid: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  statItem: {
    alignItems: "center",
    flex: 1,
  },
  statIcon: {
    width: 32,
    height: 32,
    borderRadius: 8,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 6,
  },
  statValue: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "700",
  },
  statLabel: {
    color: "rgba(255, 255, 255, 0.5)",
    fontSize: 10,
    marginTop: 2,
  },
});