import React from "react";
import { View, Text, TouchableOpacity, Image, StyleSheet, ViewStyle } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Animated from "react-native-reanimated";
import { usePressAnimation } from "../../hooks/useMicroInteraction";
import { LucideIcon } from "lucide-react-native";

interface SahoolCardProps {
  icon?: LucideIcon;
  image?: string;
  title: string;
  subtitle?: string;
  value?: string;
  badge?: string;
  gradient?: [string, string];
  onPress?: () => void;
  variant?: "default" | "compact" | "featured";
  style?: ViewStyle;
}

const AnimatedTouchable = Animated.createAnimatedComponent(TouchableOpacity);

export function SahoolCard({
  icon: Icon,
  image,
  title,
  subtitle,
  value,
  badge,
  gradient = ["#1B4D3E", "#14352B"],
  onPress,
  variant = "default",
  style,
}: SahoolCardProps) {
  const { pressIn, pressOut, animatedStyle } = usePressAnimation();

  const variantStyles: Record<string, ViewStyle> = {
    default: { padding: 20 },
    compact: { padding: 12 },
    featured: { padding: 24 },
  };

  return (
    <AnimatedTouchable
      onPressIn={pressIn}
      onPressOut={pressOut}
      onPress={onPress}
      activeOpacity={0.7}
      style={[animatedStyle, style]}
    >
      <LinearGradient
        colors={gradient}
        style={[styles.card, variantStyles[variant]]}
      >
        {image && (
          <Image
            source={{ uri: image }}
            style={styles.image}
            resizeMode="cover"
          />
        )}

        <View style={styles.content}>
          <View style={styles.header}>
            {Icon && (
              <View style={styles.iconContainer}>
                <Icon size={20} color="#F4D03F" />
              </View>
            )}
            <View style={styles.titleContainer}>
              <Text style={styles.title}>{title}</Text>
              {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
            </View>
          </View>

          {badge && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{badge}</Text>
            </View>
          )}
        </View>

        {value && (
          <Text style={styles.value}>{value}</Text>
        )}
      </LinearGradient>
    </AnimatedTouchable>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
  },
  image: {
    width: "100%",
    height: 128,
    borderRadius: 12,
    marginBottom: 12,
  },
  content: {
    flex: 1,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    marginBottom: 8,
  },
  iconContainer: {
    width: 40,
    height: 40,
    backgroundColor: "rgba(244, 208, 63, 0.2)",
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  titleContainer: {
    flex: 1,
  },
  title: {
    color: "#FFFFFF",
    fontWeight: "700",
    fontSize: 18,
  },
  subtitle: {
    color: "rgba(255, 255, 255, 0.6)",
    fontSize: 14,
  },
  badge: {
    backgroundColor: "rgba(244, 208, 63, 0.2)",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 9999,
    alignSelf: "flex-start",
    marginTop: 8,
  },
  badgeText: {
    color: "#F4D03F",
    fontSize: 12,
    fontWeight: "500",
  },
  value: {
    color: "#F4D03F",
    fontSize: 24,
    fontWeight: "900",
    marginLeft: 16,
  },
});
