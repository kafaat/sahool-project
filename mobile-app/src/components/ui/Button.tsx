import React from "react";
import { Text, TouchableOpacity, ActivityIndicator, StyleSheet, ViewStyle } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Animated from "react-native-reanimated";
import { usePressAnimation } from "../../hooks/useMicroInteraction";
import { LucideIcon } from "lucide-react-native";

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  icon?: LucideIcon;
  loading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
}

const AnimatedTouchable = Animated.createAnimatedComponent(TouchableOpacity);

export function Button({
  title,
  onPress,
  variant = "primary",
  size = "md",
  icon: Icon,
  loading = false,
  disabled = false,
  style,
}: ButtonProps) {
  const { pressIn, pressOut, animatedStyle } = usePressAnimation();

  const gradients: Record<string, [string, string]> = {
    primary: ["#F4D03F", "#F7DC6F"],
    secondary: ["#1B4D3E", "#2D6A4F"],
    danger: ["#E74C3C", "#C0392B"],
    ghost: ["transparent", "transparent"],
  };

  const sizes: Record<string, ViewStyle> = {
    sm: { paddingHorizontal: 16, paddingVertical: 8 },
    md: { paddingHorizontal: 24, paddingVertical: 12 },
    lg: { paddingHorizontal: 32, paddingVertical: 16 },
  };

  const textColor = variant === "primary" ? "#1B4D3E" : "#FFFFFF";

  return (
    <AnimatedTouchable
      onPressIn={pressIn}
      onPressOut={pressOut}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
      style={[animatedStyle, style]}
    >
      <LinearGradient
        colors={gradients[variant]}
        style={[styles.button, sizes[size]]}
      >
        {loading ? (
          <ActivityIndicator color={textColor} />
        ) : (
          <>
            {Icon && <Icon size={20} color={textColor} style={styles.icon} />}
            <Text style={[styles.text, { color: textColor }]}>
              {title}
            </Text>
          </>
        )}
      </LinearGradient>
    </AnimatedTouchable>
  );
}

const styles = StyleSheet.create({
  button: {
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
  },
  text: {
    fontWeight: "600",
    fontSize: 16,
  },
  icon: {
    marginRight: 8,
  },
});
