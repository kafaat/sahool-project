/**
 * Enhanced Button Component
 * مكون الزر المحسّن
 */

import React from 'react';
import {
  Pressable,
  Text,
  StyleSheet,
  ViewStyle,
  TextStyle,
  ActivityIndicator,
} from 'react-native';
import { Theme } from '../../theme/design-system';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
} from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'contained' | 'outlined' | 'text' | 'gradient';
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  style?: ViewStyle;
  textStyle?: TextStyle;
  // Accessibility props
  accessibilityLabel?: string;
  accessibilityHint?: string;
}

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

export default function Button({
  title,
  onPress,
  variant = 'contained',
  color = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  fullWidth = false,
  icon,
  iconPosition = 'left',
  style,
  textStyle,
  accessibilityLabel,
  accessibilityHint,
}: ButtonProps) {
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const handlePressIn = () => {
    scale.value = withSpring(0.95);
  };

  const handlePressOut = () => {
    scale.value = withSpring(1);
  };

  const getButtonStyles = (): ViewStyle => {
    const baseStyles: ViewStyle = {
      ...styles.button,
      ...styles[size],
    };

    if (fullWidth) {
      baseStyles.width = '100%';
    }

    if (variant === 'contained') {
      baseStyles.backgroundColor = Theme.colors[color].main;
    } else if (variant === 'outlined') {
      baseStyles.borderWidth = 1.5;
      baseStyles.borderColor = Theme.colors[color].main;
      baseStyles.backgroundColor = 'transparent';
    } else if (variant === 'text') {
      baseStyles.backgroundColor = 'transparent';
    }

    if (disabled) {
      baseStyles.opacity = Theme.opacities.disabled;
    }

    return baseStyles;
  };

  const getTextStyles = (): TextStyle => {
    const baseStyles: TextStyle = {
      ...styles.text,
      ...styles[`${size}Text`],
    };

    if (variant === 'contained') {
      baseStyles.color = Theme.colors[color].contrastText;
    } else {
      baseStyles.color = Theme.colors[color].main;
    }

    return baseStyles;
  };

  const buttonContent = (
    <>
      {loading && (
        <ActivityIndicator
          color={variant === 'contained' ? Theme.colors[color].contrastText : Theme.colors[color].main}
          style={styles.loader}
        />
      )}
      {!loading && icon && iconPosition === 'left' && icon}
      {!loading && <Text style={[getTextStyles(), textStyle]}>{title}</Text>}
      {!loading && icon && iconPosition === 'right' && icon}
    </>
  );

  if (variant === 'gradient') {
    return (
      <AnimatedPressable
        onPress={onPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        disabled={disabled || loading}
        style={[animatedStyle, style]}
        accessible={true}
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel || title}
        accessibilityHint={accessibilityHint}
        accessibilityState={{ disabled: disabled || loading, busy: loading }}
      >
        <LinearGradient
          colors={[Theme.colors[color].main, Theme.colors[color].dark]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={[getButtonStyles(), styles.gradient]}
        >
          {buttonContent}
        </LinearGradient>
      </AnimatedPressable>
    );
  }

  return (
    <AnimatedPressable
      onPress={onPress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      disabled={disabled || loading}
      style={[animatedStyle, getButtonStyles(), style]}
      accessible={true}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel || title}
      accessibilityHint={accessibilityHint}
      accessibilityState={{ disabled: disabled || loading, busy: loading }}
    >
      {buttonContent}
    </AnimatedPressable>
  );
}

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: Theme.borderRadius.button,
    ...Theme.shadows.sm,
  },
  small: {
    paddingHorizontal: Theme.spacing.md,
    paddingVertical: Theme.spacing.sm,
    minHeight: 32,
  },
  medium: {
    paddingHorizontal: Theme.spacing.lg,
    paddingVertical: Theme.spacing.md,
    minHeight: 44,
  },
  large: {
    paddingHorizontal: Theme.spacing.xl,
    paddingVertical: Theme.spacing.lg,
    minHeight: 56,
  },
  text: {
    fontWeight: Theme.typography.fontWeight.medium,
    textAlign: 'center',
  },
  smallText: {
    fontSize: Theme.typography.fontSize.sm,
  },
  mediumText: {
    fontSize: Theme.typography.fontSize.base,
  },
  largeText: {
    fontSize: Theme.typography.fontSize.md,
  },
  loader: {
    marginRight: Theme.spacing.sm,
  },
  gradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
