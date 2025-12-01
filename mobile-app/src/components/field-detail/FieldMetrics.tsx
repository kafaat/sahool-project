import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

interface FieldMetricsProps {
  area: number;
  healthScore: number;
  ndviValue: number;
}

function getHealthColor(score: number): string {
  if (score >= 80) return '#4CAF50';
  if (score >= 60) return '#FFC107';
  return '#F44336';
}

function getNDVIColor(value: number): string {
  if (value >= 0.6) return '#4CAF50';
  if (value >= 0.3) return '#8BC34A';
  if (value >= 0.2) return '#FFC107';
  return '#F44336';
}

export default function FieldMetrics({
  area,
  healthScore,
  ndviValue,
}: FieldMetricsProps) {
  return (
    <View style={styles.metricsGrid}>
      <View style={styles.metricCard}>
        <Icon name="ruler-square" size={24} color="#2E7D32" />
        <Text variant="bodySmall" style={styles.metricLabel}>
          المساحة
        </Text>
        <Text variant="titleMedium" style={styles.metricValue}>
          {area.toFixed(1)}
        </Text>
        <Text variant="bodySmall" style={styles.metricUnit}>
          هكتار
        </Text>
      </View>

      <View style={styles.metricCard}>
        <Icon
          name="heart-pulse"
          size={24}
          color={getHealthColor(healthScore)}
        />
        <Text variant="bodySmall" style={styles.metricLabel}>
          الصحة
        </Text>
        <Text
          variant="titleMedium"
          style={[
            styles.metricValue,
            { color: getHealthColor(healthScore) },
          ]}
        >
          {healthScore}
        </Text>
        <Text variant="bodySmall" style={styles.metricUnit}>
          %
        </Text>
      </View>

      <View style={styles.metricCard}>
        <Icon
          name="image-filter-hdr"
          size={24}
          color={getNDVIColor(ndviValue)}
        />
        <Text variant="bodySmall" style={styles.metricLabel}>
          NDVI
        </Text>
        <Text
          variant="titleMedium"
          style={[
            styles.metricValue,
            { color: getNDVIColor(ndviValue) },
          ]}
        >
          {ndviValue.toFixed(2)}
        </Text>
        <Text variant="bodySmall" style={styles.metricUnit}>
          قيمة
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  metricsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  metricCard: {
    flex: 1,
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    marginHorizontal: 4,
  },
  metricLabel: {
    color: '#666',
    marginTop: 4,
  },
  metricValue: {
    fontWeight: 'bold',
    marginTop: 4,
  },
  metricUnit: {
    color: '#999',
    fontSize: 11,
  },
});
