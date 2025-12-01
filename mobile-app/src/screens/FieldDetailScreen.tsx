import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Dimensions,
  Alert
} from 'react-native';
import {
  Text,
  Card,
  Chip,
  Button,
  ActivityIndicator,
  useTheme
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import MapView, { Polygon, Marker } from 'react-native-maps';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { getFieldDetails, getFieldNDVI, getFieldWeather } from '../services/api';

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

  const getHealthColor = (score: number) => {
    if (score >= 80) return '#4CAF50';
    if (score >= 60) return '#FFC107';
    return '#F44336';
  };

  const getNDVIColor = (value: number) => {
    if (value >= 0.6) return '#4CAF50';
    if (value >= 0.3) return '#8BC34A';
    if (value >= 0.2) return '#FFC107';
    return '#F44336';
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
      {/* Map Section */}
      <Card style={styles.mapCard}>
        <MapView
          style={styles.map}
          initialRegion={{
            latitude: field.center.lat,
            longitude: field.center.lon,
            latitudeDelta: 0.01,
            longitudeDelta: 0.01,
          }}
        >
          {field.boundaries && field.boundaries.length > 0 && (
            <Polygon
              coordinates={field.boundaries.map((point) => ({
                latitude: point.lat,
                longitude: point.lon,
              }))}
              fillColor="rgba(46, 125, 50, 0.2)"
              strokeColor="#2E7D32"
              strokeWidth={2}
            />
          )}
          <Marker
            coordinate={{
              latitude: field.center.lat,
              longitude: field.center.lon,
            }}
            title={field.name}
          />
        </MapView>
      </Card>

      {/* Field Info Card */}
      <Card style={styles.card}>
        <Card.Content>
          <View style={styles.header}>
            <View style={styles.titleContainer}>
              <Text variant="headlineSmall" style={styles.title}>
                {field.name}
              </Text>
              <Text variant="bodyMedium" style={styles.cropType}>
                <Icon name="sprout" size={16} /> {field.crop_type}
              </Text>
            </View>
            <Chip
              mode="outlined"
              style={[
                styles.statusChip,
                { borderColor: field.status === 'active' ? '#4CAF50' : '#999' },
              ]}
            >
              {field.status === 'active' ? 'نشط' : 'غير نشط'}
            </Chip>
          </View>

          <View style={styles.metricsGrid}>
            <View style={styles.metricCard}>
              <Icon name="ruler-square" size={24} color="#2E7D32" />
              <Text variant="bodySmall" style={styles.metricLabel}>
                المساحة
              </Text>
              <Text variant="titleMedium" style={styles.metricValue}>
                {field.area.toFixed(1)}
              </Text>
              <Text variant="bodySmall" style={styles.metricUnit}>
                هكتار
              </Text>
            </View>

            <View style={styles.metricCard}>
              <Icon
                name="heart-pulse"
                size={24}
                color={getHealthColor(field.health_score)}
              />
              <Text variant="bodySmall" style={styles.metricLabel}>
                الصحة
              </Text>
              <Text
                variant="titleMedium"
                style={[
                  styles.metricValue,
                  { color: getHealthColor(field.health_score) },
                ]}
              >
                {field.health_score}
              </Text>
              <Text variant="bodySmall" style={styles.metricUnit}>
                %
              </Text>
            </View>

            <View style={styles.metricCard}>
              <Icon
                name="image-filter-hdr"
                size={24}
                color={getNDVIColor(field.ndvi_value)}
              />
              <Text variant="bodySmall" style={styles.metricLabel}>
                NDVI
              </Text>
              <Text
                variant="titleMedium"
                style={[
                  styles.metricValue,
                  { color: getNDVIColor(field.ndvi_value) },
                ]}
              >
                {field.ndvi_value.toFixed(2)}
              </Text>
              <Text variant="bodySmall" style={styles.metricUnit}>
                قيمة
              </Text>
            </View>
          </View>

          <View style={styles.dates}>
            <View style={styles.dateItem}>
              <Icon name="calendar-start" size={20} color="#666" />
              <Text variant="bodySmall" style={styles.dateLabel}>
                تاريخ الزراعة:
              </Text>
              <Text variant="bodyMedium" style={styles.dateValue}>
                {new Date(field.planted_date).toLocaleDateString('ar-SA')}
              </Text>
            </View>

            <View style={styles.dateItem}>
              <Icon name="calendar-check" size={20} color="#666" />
              <Text variant="bodySmall" style={styles.dateLabel}>
                الحصاد المتوقع:
              </Text>
              <Text variant="bodyMedium" style={styles.dateValue}>
                {new Date(field.expected_harvest).toLocaleDateString('ar-SA')}
              </Text>
            </View>
          </View>
        </Card.Content>
      </Card>

      {/* Quick Actions */}
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

      {/* Health Recommendations */}
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            توصيات الصحة
          </Text>

          {field.health_score >= 80 ? (
            <View style={styles.recommendation}>
              <Icon name="check-circle" size={24} color="#4CAF50" />
              <Text style={styles.recommendationText}>
                الحقل في حالة صحية ممتازة. استمر في المراقبة المنتظمة.
              </Text>
            </View>
          ) : field.health_score >= 60 ? (
            <View style={styles.recommendation}>
              <Icon name="alert-circle" size={24} color="#FFC107" />
              <Text style={styles.recommendationText}>
                الحقل يحتاج إلى اهتمام. تحقق من الري والتسميد.
              </Text>
            </View>
          ) : (
            <View style={styles.recommendation}>
              <Icon name="close-circle" size={24} color="#F44336" />
              <Text style={styles.recommendationText}>
                تحذير: الحقل في حالة حرجة. يتطلب تدخل فوري.
              </Text>
            </View>
          )}
        </Card.Content>
      </Card>
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
  mapCard: {
    margin: 0,
    borderRadius: 0,
    overflow: 'hidden',
  },
  map: {
    width: Dimensions.get('window').width,
    height: 250,
  },
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
  recommendation: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    padding: 12,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
  },
  recommendationText: {
    flex: 1,
    color: '#666',
    lineHeight: 20,
  },
});
