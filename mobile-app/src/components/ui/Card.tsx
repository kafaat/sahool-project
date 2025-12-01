/**
 * Enhanced Card Component
 * مكون البطاقة المحسّن
 */

import React from 'react';
import { View, StyleSheet, ViewStyle, Pressable } from 'react-native';
import { Theme } from '../../theme/design-system';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
} from 'react-native-reanimated';

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  elevation?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'elevated' | 'outlined' | 'filled';
  onPress?: () => void;
  pressable?: boolean;
  rounded?: 'sm' | 'md' | 'lg' | 'xl';
  // Accessibility props
  accessibilityLabel?: string;
  accessibilityHint?: string;
  accessibilityRole?: 'none' | 'button' | 'link' | 'header' | 'summary';
}

export default function Card({
  children,
  style,
  elevation = 'md',
  variant = 'elevated',
  onPress,
  pressable = false,
  rounded = 'lg',
  accessibilityLabel,
  accessibilityHint,
  accessibilityRole = 'none',
}: CardProps) {
  const scale = useSharedValue(1);
  const opacity = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    opacity: opacity.value,
  }));

  const handlePressIn = () => {
    scale.value = withSpring(0.98);
    opacity.value = withTiming(0.9, { duration: 150 });
  };

  const handlePressOut = () => {
    scale.value = withSpring(1);
    opacity.value = withTiming(1, { duration: 150 });
  };

  const cardStyle = [
    styles.card,
    variant === 'elevated' && Theme.shadows[elevation],
    variant === 'outlined' && styles.outlined,
    variant === 'filled' && styles.filled,
    { borderRadius: Theme.borderRadius[rounded] },
    style,
  ];

  if (pressable || onPress) {
    return (
      <Animated.View style={[animatedStyle]}>
        <Pressable
          onPress={onPress}
          onPressIn={handlePressIn}
          onPressOut={handlePressOut}
          style={({ pressed }) => [
            cardStyle,
            pressed && styles.pressed,
          ]}
          accessible={true}
          accessibilityRole={onPress ? 'button' : accessibilityRole}
          accessibilityLabel={accessibilityLabel}
          accessibilityHint={accessibilityHint}
        >
          {children}
        </Pressable>
      </Animated.View>
    );
  }

  return (
    <View
      style={cardStyle}
      accessible={accessibilityLabel ? true : false}
      accessibilityRole={accessibilityRole}
      accessibilityLabel={accessibilityLabel}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Theme.colors.background.paper,
    padding: Theme.spacing.md,
    marginBottom: Theme.spacing.md,
  },
  outlined: {
    borderWidth: 1,
    borderColor: Theme.colors.gray[300],
  },
  filled: {
    backgroundColor: Theme.colors.gray[100],
  },
  pressed: {
    opacity: 0.9,
  },
});
