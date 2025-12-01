/**
 * Animated Progress Bar Component
 * مكون شريط التقدم المتحرك
 */

import React, { useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Theme } from '../../theme/design-system';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
} from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';

interface ProgressBarProps {
  progress: number; // 0-100
  height?: number;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  showLabel?: boolean;
  label?: string;
  variant?: 'default' | 'gradient' | 'striped';
  animated?: boolean;
  // Accessibility props
  accessibilityLabel?: string;
}

export default function ProgressBar({
  progress,
  height = 8,
  color = 'primary',
  showLabel = false,
  label,
  variant = 'default',
  animated = true,
  accessibilityLabel,
}: ProgressBarProps) {
  const progressValue = useSharedValue(0);

  useEffect(() => {
    if (animated) {
      progressValue.value = withSpring(progress, {
        damping: 15,
        stiffness: 100,
      });
    } else {
      progressValue.value = progress;
    }
  }, [progress, animated]);

  const animatedStyle = useAnimatedStyle(() => ({
    width: `${progressValue.value}%`,
  }));

  const getColor = () => Theme.colors[color].main;
  const getDarkColor = () => Theme.colors[color].dark;

  const progressText = `${Math.round(progress)}%`;

  return (
    <View
      style={styles.container}
      accessible={true}
      accessibilityRole="progressbar"
      accessibilityLabel={accessibilityLabel || label || `التقدم ${progressText}`}
      accessibilityValue={{ now: progress, min: 0, max: 100, text: progressText }}
    >
      {showLabel && (
        <Text style={styles.label}>
          {label || progressText}
        </Text>
      )}
      <View style={[styles.track, { height, borderRadius: height / 2 }]}>
        <Animated.View style={[animatedStyle, { height, borderRadius: height / 2 }]}>
          {variant === 'gradient' ? (
            <LinearGradient
              colors={[getColor(), getDarkColor()]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={[styles.fill, { borderRadius: height / 2 }]}
            />
          ) : (
            <View
              style={[
                styles.fill,
                { backgroundColor: getColor(), borderRadius: height / 2 },
                variant === 'striped' && styles.striped,
              ]}
            />
          )}
        </Animated.View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    marginVertical: Theme.spacing.sm,
  },
  track: {
    width: '100%',
    backgroundColor: Theme.colors.gray[200],
    overflow: 'hidden',
  },
  fill: {
    height: '100%',
    width: '100%',
  },
  striped: {
    // You would add striped pattern here using gradients or background
  },
  label: {
    fontSize: Theme.typography.fontSize.sm,
    fontWeight: Theme.typography.fontWeight.medium,
    color: Theme.colors.text.secondary,
    marginBottom: Theme.spacing.xs,
  },
});
