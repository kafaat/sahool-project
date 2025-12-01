/**
 * Stat Card Component
 * بطاقة الإحصائيات - لعرض المقاييس الرئيسية
 */

import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { Theme } from '../../theme/design-system';
import Card from './Card';
import { LinearGradient } from 'expo-linear-gradient';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  variant?: 'default' | 'gradient' | 'minimal';
  style?: ViewStyle;
}

export default function StatCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  color = 'primary',
  variant = 'default',
  style,
}: StatCardProps) {
  const getTrendColor = () => {
    if (!trend) return Theme.colors.text.secondary;
    return trend.isPositive ? Theme.colors.success.main : Theme.colors.error.main;
  };

  const getTrendIcon = () => {
    if (!trend) return null;
    return trend.isPositive ? '↑' : '↓';
  };

  if (variant === 'gradient') {
    return (
      <Card elevation="lg" rounded="xl" style={[styles.container, style]}>
        <LinearGradient
          colors={[Theme.colors[color].main, Theme.colors[color].dark]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.gradient}
        >
          <View style={styles.header}>
            {icon && <View style={styles.iconContainer}>{icon}</View>}
            <Text style={[styles.title, styles.whiteText]}>{title}</Text>
          </View>

          <Text style={[styles.value, styles.whiteText]}>{value}</Text>

          {subtitle && (
            <Text style={[styles.subtitle, styles.whiteText]}>{subtitle}</Text>
          )}

          {trend && (
            <View style={styles.trend}>
              <Text style={[styles.trendText, styles.whiteText]}>
                {getTrendIcon()} {Math.abs(trend.value)}%
              </Text>
            </View>
          )}
        </LinearGradient>
      </Card>
    );
  }

  if (variant === 'minimal') {
    return (
      <View style={[styles.minimal, style]}>
        <View style={styles.header}>
          {icon && <View style={styles.iconContainer}>{icon}</View>}
          <Text style={styles.titleMinimal}>{title}</Text>
        </View>

        <Text style={styles.valueMinimal}>{value}</Text>

        {trend && (
          <Text style={[styles.trendText, { color: getTrendColor() }]}>
            {getTrendIcon()} {Math.abs(trend.value)}%
          </Text>
        )}
      </View>
    );
  }

  // Default variant
  return (
    <Card elevation="md" rounded="lg" style={[styles.container, style]}>
      <View style={styles.header}>
        {icon && (
          <View style={[styles.iconContainer, { backgroundColor: `${Theme.colors[color].main}20` }]}>
            {icon}
          </View>
        )}
        <Text style={styles.title}>{title}</Text>
      </View>

      <Text style={[styles.value, { color: Theme.colors[color].main }]}>{value}</Text>

      {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}

      {trend && (
        <View style={styles.trend}>
          <Text style={[styles.trendText, { color: getTrendColor() }]}>
            {getTrendIcon()} {Math.abs(trend.value)}%
          </Text>
        </View>
      )}
    </Card>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    minWidth: 150,
  },
  gradient: {
    padding: Theme.spacing.md,
    borderRadius: Theme.borderRadius.lg,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Theme.spacing.sm,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: Theme.borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Theme.spacing.sm,
  },
  title: {
    fontSize: Theme.typography.fontSize.sm,
    color: Theme.colors.text.secondary,
    fontWeight: Theme.typography.fontWeight.medium,
    flex: 1,
  },
  value: {
    fontSize: Theme.typography.fontSize['3xl'],
    fontWeight: Theme.typography.fontWeight.bold,
    marginBottom: Theme.spacing.xs,
  },
  subtitle: {
    fontSize: Theme.typography.fontSize.xs,
    color: Theme.colors.text.secondary,
    marginBottom: Theme.spacing.xs,
  },
  trend: {
    marginTop: Theme.spacing.xs,
  },
  trendText: {
    fontSize: Theme.typography.fontSize.sm,
    fontWeight: Theme.typography.fontWeight.medium,
  },
  whiteText: {
    color: '#FFFFFF',
  },
  minimal: {
    padding: Theme.spacing.md,
    flex: 1,
  },
  titleMinimal: {
    fontSize: Theme.typography.fontSize.sm,
    color: Theme.colors.text.secondary,
    marginBottom: Theme.spacing.sm,
  },
  valueMinimal: {
    fontSize: Theme.typography.fontSize['2xl'],
    fontWeight: Theme.typography.fontWeight.bold,
    color: Theme.colors.text.primary,
  },
});
