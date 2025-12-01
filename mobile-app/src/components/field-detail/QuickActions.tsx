import React from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import { Card, Text, Button } from 'react-native-paper';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

interface QuickActionsProps {
  fieldId: number;
  navigation: NativeStackNavigationProp<any>;
}

export default function QuickActions({
  fieldId,
  navigation,
}: QuickActionsProps) {
  return (
    <Card style={styles.card}>
      <Card.Content>
        <Text variant="titleMedium" style={styles.sectionTitle}>
          إجراءات سريعة
        </Text>

        <View style={styles.actionButtons}>
          <Button
            mode="outlined"
            icon="image-filter-hdr"
            style={styles.actionButton}
            onPress={() => navigation.navigate('NDVI', { fieldId })}
          >
            عرض NDVI
          </Button>

          <Button
            mode="outlined"
            icon="weather-partly-cloudy"
            style={styles.actionButton}
            onPress={() => Alert.alert('الطقس', 'سيتم إضافة بيانات الطقس قريباً')}
          >
            الطقس
          </Button>

          <Button
            mode="outlined"
            icon="robot"
            style={styles.actionButton}
            onPress={() => Alert.alert('مساعد AI', 'سيتم إضافة المساعد الذكي قريباً')}
          >
            مساعد AI
          </Button>

          <Button
            mode="outlined"
            icon="chart-line"
            style={styles.actionButton}
            onPress={() => Alert.alert('التحليلات', 'سيتم إضافة التحليلات قريباً')}
          >
            التحليلات
          </Button>
        </View>
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
  sectionTitle: {
    fontWeight: 'bold',
    marginBottom: 16,
  },
  actionButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  actionButton: {
    flex: 1,
    minWidth: '45%',
  },
});
