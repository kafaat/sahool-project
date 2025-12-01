/**
 * Chip Component
 * مكون الشريحة - للتصنيفات والعلامات
 */

import React from 'react';
import { View, Text, StyleSheet, Pressable, ViewStyle } from 'react-native';
import { Theme } from '../../theme/design-system';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
} from 'react-native-reanimated';

interface ChipProps {
  label: string;
  variant?: 'filled' | 'outlined';
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info' | 'default';
  size?: 'small' | 'medium';
  onPress?: () => void;
  onDelete?: () => void;
  icon?: React.ReactNode;
  deleteIcon?: React.ReactNode;
  selected?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
  // Accessibility props
  accessibilityLabel?: string;
  accessibilityHint?: string;
  deleteAccessibilityLabel?: string;
}

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

export default function Chip({
  label,
  variant = 'filled',
  color = 'default',
  size = 'medium',
  onPress,
  onDelete,
  icon,
  deleteIcon,
  selected = false,
  disabled = false,
  style,
  accessibilityLabel,
  accessibilityHint,
  deleteAccessibilityLabel,
}: ChipProps) {
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

  const getChipStyles = (): ViewStyle => {
    const baseStyles: ViewStyle = {
      ...styles.chip,
      ...styles[size],
    };

    if (variant === 'filled') {
      if (color === 'default') {
        baseStyles.backgroundColor = Theme.colors.gray[200];
      } else {
        baseStyles.backgroundColor = selected
          ? Theme.colors[color].main
          : `${Theme.colors[color].main}20`;
      }
    } else {
      baseStyles.borderWidth = 1;
      baseStyles.borderColor = color === 'default'
        ? Theme.colors.gray[400]
        : Theme.colors[color].main;
      baseStyles.backgroundColor = 'transparent';
    }

    if (disabled) {
      baseStyles.opacity = Theme.opacities.disabled;
    }

    return baseStyles;
  };

  const getTextColor = () => {
    if (variant === 'filled') {
      if (color === 'default') {
        return Theme.colors.text.primary;
      }
      return selected ? Theme.colors[color].contrastText : Theme.colors[color].dark;
    }
    return color === 'default' ? Theme.colors.text.primary : Theme.colors[color].main;
  };

  const content = (
    <View style={styles.content}>
      {icon && <View style={styles.icon}>{icon}</View>}
      <Text style={[styles.label, { color: getTextColor() }]} numberOfLines={1}>
        {label}
      </Text>
      {onDelete && (
        <Pressable
          onPress={onDelete}
          style={styles.deleteButton}
          disabled={disabled}
          accessible={true}
          accessibilityRole="button"
          accessibilityLabel={deleteAccessibilityLabel || `حذف ${label}`}
          accessibilityHint="انقر مزدوج للحذف"
        >
          {deleteIcon || <Text style={{ color: getTextColor() }}>×</Text>}
        </Pressable>
      )}
    </View>
  );

  if (onPress) {
    return (
      <AnimatedPressable
        onPress={onPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        disabled={disabled}
        style={[animatedStyle, getChipStyles(), style]}
        accessible={true}
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel || label}
        accessibilityHint={accessibilityHint}
        accessibilityState={{ selected, disabled }}
      >
        {content}
      </AnimatedPressable>
    );
  }

  return (
    <View
      style={[getChipStyles(), style]}
      accessible={true}
      accessibilityRole="text"
      accessibilityLabel={accessibilityLabel || label}
      accessibilityState={{ selected }}
    >
      {content}
    </View>
  );
}

const styles = StyleSheet.create({
  chip: {
    borderRadius: Theme.borderRadius.chip,
    alignSelf: 'flex-start',
  },
  small: {
    paddingHorizontal: Theme.spacing.sm,
    paddingVertical: Theme.spacing.xs,
    minHeight: 24,
  },
  medium: {
    paddingHorizontal: Theme.spacing.md,
    paddingVertical: Theme.spacing.sm,
    minHeight: 32,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  label: {
    fontSize: Theme.typography.fontSize.sm,
    fontWeight: Theme.typography.fontWeight.medium,
  },
  icon: {
    marginRight: Theme.spacing.xs,
  },
  deleteButton: {
    marginLeft: Theme.spacing.xs,
    padding: Theme.spacing.xs,
  },
});
