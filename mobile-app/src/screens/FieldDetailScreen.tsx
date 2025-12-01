import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import { Text, ActivityIndicator, useTheme } from 'react-native-paper';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { getFieldDetails } from '../services/api';
import {
  FieldMap,
  FieldInfo,
  QuickActions,
  HealthRecommendations,
} from '../components/field-detail';

type FieldDetailScreenProps = {
  navigation: NativeStackNavigationProp<any>;
  route: RouteProp<{ params: { fieldId: number } }, 'params'>;
};

interface FieldDetail {
  id: number;
  name: string;
  area: number;
  crop_type: string;
  health_score: number;
  ndvi_value: number;
  status: string;
  boundaries: Array<{ lat: number; lon: number }>;
  center: { lat: number; lon: number };
  planted_date: string;
  expected_harvest: string;
}

export default function FieldDetailScreen({
  navigation,
  route,
}: FieldDetailScreenProps) {
  const theme = useTheme();
  const { fieldId } = route.params;
  const [field, setField] = useState<FieldDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'map' | 'ndvi' | 'weather'>('map');

  useEffect(() => {
    loadFieldDetails();
  }, [fieldId]);

  const loadFieldDetails = async () => {
    try {
      const data = await getFieldDetails(fieldId);
      setField(data);
    } catch (error) {
      Alert.alert('خطأ', 'فشل في تحميل تفاصيل الحقل');
      navigation.goBack();
    } finally {
      setLoading(false);
    }
  };

  if (loading || !field) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={styles.loadingText}>جاري تحميل تفاصيل الحقل...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <FieldMap
        center={field.center}
        boundaries={field.boundaries}
        name={field.name}
      />

      <FieldInfo
        name={field.name}
        cropType={field.crop_type}
        status={field.status}
        area={field.area}
        healthScore={field.health_score}
        ndviValue={field.ndvi_value}
        plantedDate={field.planted_date}
        expectedHarvest={field.expected_harvest}
      />

      <QuickActions fieldId={fieldId} navigation={navigation} />

      <HealthRecommendations healthScore={field.health_score} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    color: '#666',
  },
});
