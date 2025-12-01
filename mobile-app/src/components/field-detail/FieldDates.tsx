import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

interface FieldDatesProps {
  plantedDate: string;
  expectedHarvest: string;
}

export default function FieldDates({
  plantedDate,
  expectedHarvest,
}: FieldDatesProps) {
  return (
    <View style={styles.dates}>
      <View style={styles.dateItem}>
        <Icon name="calendar-start" size={20} color="#666" />
        <Text variant="bodySmall" style={styles.dateLabel}>
          تاريخ الزراعة:
        </Text>
        <Text variant="bodyMedium" style={styles.dateValue}>
          {new Date(plantedDate).toLocaleDateString('ar-SA')}
        </Text>
      </View>

      <View style={styles.dateItem}>
        <Icon name="calendar-check" size={20} color="#666" />
        <Text variant="bodySmall" style={styles.dateLabel}>
          الحصاد المتوقع:
        </Text>
        <Text variant="bodyMedium" style={styles.dateValue}>
          {new Date(expectedHarvest).toLocaleDateString('ar-SA')}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  dates: {
    gap: 12,
  },
  dateItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  dateLabel: {
    color: '#666',
  },
  dateValue: {
    fontWeight: '500',
  },
});
