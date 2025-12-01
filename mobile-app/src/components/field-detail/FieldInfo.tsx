import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Card, Text, Chip } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import FieldMetrics from './FieldMetrics';
import FieldDates from './FieldDates';

interface FieldInfoProps {
  name: string;
  cropType: string;
  status: string;
  area: number;
  healthScore: number;
  ndviValue: number;
  plantedDate: string;
  expectedHarvest: string;
}

export default function FieldInfo({
  name,
  cropType,
  status,
  area,
  healthScore,
  ndviValue,
  plantedDate,
  expectedHarvest,
}: FieldInfoProps) {
  return (
    <Card style={styles.card}>
      <Card.Content>
        <View style={styles.header}>
          <View style={styles.titleContainer}>
            <Text variant="headlineSmall" style={styles.title}>
              {name}
            </Text>
            <Text variant="bodyMedium" style={styles.cropType}>
              <Icon name="sprout" size={16} /> {cropType}
            </Text>
          </View>
          <Chip
            mode="outlined"
            style={[
              styles.statusChip,
              { borderColor: status === 'active' ? '#4CAF50' : '#999' },
            ]}
          >
            {status === 'active' ? 'نشط' : 'غير نشط'}
          </Chip>
        </View>

        <FieldMetrics
          area={area}
          healthScore={healthScore}
          ndviValue={ndviValue}
        />

        <FieldDates
          plantedDate={plantedDate}
          expectedHarvest={expectedHarvest}
        />
      </Card.Content>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    margin: 16,
    marginTop: 0,
    elevation: 2,
    borderRadius: 12,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 20,
  },
  titleContainer: {
    flex: 1,
  },
  title: {
    fontWeight: 'bold',
    marginBottom: 4,
  },
  cropType: {
    color: '#666',
  },
  statusChip: {
    height: 32,
  },
});
