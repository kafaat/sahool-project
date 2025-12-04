import React from "react";
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  ViewStyle,
  TextStyle,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Animated from "react-native-reanimated";
import { usePressAnimation } from "@/hooks/useMicroInteraction";

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "outline" | "danger";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  fullWidth?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

const AnimatedTouchable = Animated.createAnimatedComponent(TouchableOpacity);

export function Button({
  title,
  onPress,
  variant = "primary",
  size = "md",
  disabled = false,
  loading = false,
  icon,
  iconPosition = "left",
  fullWidth = false,
  style,
  textStyle,
}: ButtonProps) {
  const { pressIn, pressOut, animatedStyle } = usePressAnimation();
  const isDisabled = disabled || loading;

  const getGradientColors = (): [string, string] => {
    if (isDisabled) return ["#4A5568", "#2D3748"];
    switch (variant) {
      case "primary": return ["#F4D03F", "#F7DC6F"];
      case "secondary": return ["#1B4D3E", "#2D6A4F"];
      case "danger": return ["#E74C3C", "#C0392B"];
      default: return ["transparent", "transparent"];
    }
  };

  const getTextColor = (): string => {
    if (isDisabled) return "#A0AEC0";
    switch (variant) {
      case "primary": return "#1B4D3E";
      case "outline": return "#F4D03F";
      default: return "#FFFFFF";
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case "sm": return { paddingVertical: 8, paddingHorizontal: 16, fontSize: 14 };
      case "lg": return { paddingVertical: 16, paddingHorizontal: 32, fontSize: 18 };
      default: return { paddingVertical: 12, paddingHorizontal: 24, fontSize: 16 };
    }
  };

  const sizeStyles = getSizeStyles();

  const content = (
    <>
      {loading ? (
        <ActivityIndicator color={getTextColor()} size="small" />
      ) : (
        <>
          {icon && iconPosition === "left" && icon}
          <Text style={[styles.text, { color: getTextColor(), fontSize: sizeStyles.fontSize }, textStyle]}>
            {title}
          </Text>
          {icon && iconPosition === "right" && icon}
        </>
      )}
    </>
  );

  const buttonStyle: ViewStyle = {
    ...styles.button,
    paddingVertical: sizeStyles.paddingVertical,
    paddingHorizontal: sizeStyles.paddingHorizontal,
    width: fullWidth ? "100%" : undefined,
    borderWidth: variant === "outline" ? 1 : 0,
    borderColor: variant === "outline" ? "#F4D03F" : undefined,
  };

  if (variant === "outline") {
    return (
      <AnimatedTouchable
        onPress={onPress}
        onPressIn={pressIn}
        onPressOut={pressOut}
        disabled={isDisabled}
        style={[animatedStyle, buttonStyle, style]}
        activeOpacity={0.7}
      >
        {content}
      </AnimatedTouchable>
    );
  }

  return (
    <AnimatedTouchable
      onPress={onPress}
      onPressIn={pressIn}
      onPressOut={pressOut}
      disabled={isDisabled}
      style={[animatedStyle, style]}
      activeOpacity={0.7}
    >
      <LinearGradient colors={getGradientColors()} start={[0, 0]} end={[1, 1]} style={buttonStyle}>
        {content}
      </LinearGradient>
    </AnimatedTouchable>
  );
}

const styles = StyleSheet.create({
  button: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 12,
    gap: 8,
  },
  text: {
    fontWeight: "600",
    textAlign: "center",
  },
});