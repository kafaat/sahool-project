import React, { useEffect, useState } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  Dimensions,
  RefreshControl,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Button,
  Chip,
  ActivityIndicator,
  Divider,
  List,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import MapView, { Polygon, PROVIDER_GOOGLE } from 'react-native-maps';
import { LineChart } from 'react-native-chart-kit';
import { apiService } from '../services/api';

interface FieldDetail {
  id: number;
  name: string;
  area_hectares: number;
  crop_type: string;
  status: string;
  ndvi_current: number;
  ndvi_history: Array<{ date: string; value: number }>;
  geometry: {
    type: string;
    coordinates: number[][][];
  };
  region: string;
  soil_type: string;
  irrigation_type: string;
  planting_date: string;
  weather: {
    temp: number;
    humidity: number;
    condition: string;
  };
  recommendations: string[];
}

export default function FieldDetailScreen({ route, navigation }: any) {
  const { fieldId } = route.params;
  const [field, setField] = useState<FieldDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'ndvi' | 'weather'>('overview');

  const fetchFieldDetail = async () => {
    try {
      const [fieldResponse, ndviResponse, weatherResponse] = await Promise.all([
        apiService.getFieldDetail(fieldId),
        apiService.getNDVIHistory(fieldId),
        apiService.getWeather(fieldId),
      ]);

      setField({
        ...fieldResponse.data,
        ndvi_history: ndviResponse.data || [],
        weather: weatherResponse.data || {},
      });
    } catch (error) {
      console.error('Error fetching field detail:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchFieldDetail();
  }, [fieldId]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchFieldDetail();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#4CAF50';
      case 'warning': return '#FF9800';
      case 'critical': return '#F44336';
      default: return '#9E9E9E';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'healthy': return 'صحي';
      case 'warning': return 'تحذير';
      case 'critical': return 'حرج';
      default: return 'غير محدد';
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2E7D32" />
      </View>
    );
  }

  if (!field) {
    return (
      <View style={styles.centered}>
        <Icon name="alert-circle" size={60} color="#CCC" />
        <Paragraph>لم يتم العثور على الحقل</Paragraph>
      </View>
    );
  }

  const mapRegion = field.geometry?.coordinates?.[0]?.[0]
    ? {
        latitude: field.geometry.coordinates[0][0][1],
        longitude: field.geometry.coordinates[0][0][0],
        latitudeDelta: 0.01,
        longitudeDelta: 0.01,
      }
    : { latitude: 15.3694, longitude: 44.191, latitudeDelta: 0.1, longitudeDelta: 0.1 };

  const polygonCoordinates = field.geometry?.coordinates?.[0]?.map(
    (coord: number[]) => ({
      latitude: coord[1],
      longitude: coord[0],
    })
  ) || [];

  const ndviChartData = {
    labels: field.ndvi_history?.slice(-7).map((h) => h.date.slice(5, 10)) || [],
    datasets: [
      {
        data: field.ndvi_history?.slice(-7).map((h) => h.value) || [0],
        color: () => '#4CAF50',
        strokeWidth: 2,
      },
    ],
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Map Preview */}
      <View style={styles.mapContainer}>
        <MapView
          style={styles.map}
          provider={PROVIDER_GOOGLE}
          region={mapRegion}
          scrollEnabled={false}
          zoomEnabled={false}
        >
          {polygonCoordinates.length > 0 && (
            <Polygon
              coordinates={polygonCoordinates}
              fillColor={`${getStatusColor(field.status)}40`}
              strokeColor={getStatusColor(field.status)}
              strokeWidth={2}
            />
          )}
        </MapView>
        <View style={styles.mapOverlay}>
          <Chip
            style={[styles.statusChip, { backgroundColor: getStatusColor(field.status) }]}
            textStyle={styles.statusChipText}
          >
            {getStatusLabel(field.status)}
          </Chip>
        </View>
      </View>

      {/* Field Info Header */}
      <Card style={styles.infoCard}>
        <Card.Content>
          <Title style={styles.fieldName}>{field.name}</Title>
          <View style={styles.infoRow}>
            <View style={styles.infoItem}>
              <Icon name="sprout" size={20} color="#2E7D32" />
              <Paragraph style={styles.infoText}>{field.crop_type}</Paragraph>
            </View>
            <View style={styles.infoItem}>
              <Icon name="ruler-square" size={20} color="#1976D2" />
              <Paragraph style={styles.infoText}>{field.area_hectares} هكتار</Paragraph>
            </View>
            <View style={styles.infoItem}>
              <Icon name="map-marker" size={20} color="#FF5722" />
              <Paragraph style={styles.infoText}>{field.region}</Paragraph>
            </View>
          </View>
        </Card.Content>
      </Card>

      {/* Tab Buttons */}
      <View style={styles.tabContainer}>
        <Button
          mode={activeTab === 'overview' ? 'contained' : 'outlined'}
          onPress={() => setActiveTab('overview')}
          style={styles.tabButton}
          compact
        >
          نظرة عامة
        </Button>
        <Button
          mode={activeTab === 'ndvi' ? 'contained' : 'outlined'}
          onPress={() => setActiveTab('ndvi')}
          style={styles.tabButton}
          compact
        >
          NDVI
        </Button>
        <Button
          mode={activeTab === 'weather' ? 'contained' : 'outlined'}
          onPress={() => setActiveTab('weather')}
          style={styles.tabButton}
          compact
        >
          الطقس
        </Button>
      </View>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <Card style={styles.contentCard}>
          <Card.Content>
            <Title style={styles.sectionTitle}>معلومات الحقل</Title>
            <List.Item
              title="نوع التربة"
              description={field.soil_type || 'غير محدد'}
              left={(props) => <List.Icon {...props} icon="terrain" />}
            />
            <Divider />
            <List.Item
              title="نظام الري"
              description={field.irrigation_type || 'غير محدد'}
              left={(props) => <List.Icon {...props} icon="water" />}
            />
            <Divider />
            <List.Item
              title="تاريخ الزراعة"
              description={field.planting_date || 'غير محدد'}
              left={(props) => <List.Icon {...props} icon="calendar" />}
            />
            <Divider />
            <List.Item
              title="مؤشر NDVI الحالي"
              description={field.ndvi_current?.toFixed(3) || 'N/A'}
              left={(props) => <List.Icon {...props} icon="leaf" color="#4CAF50" />}
            />
          </Card.Content>
        </Card>
      )}

      {activeTab === 'ndvi' && (
        <Card style={styles.contentCard}>
          <Card.Content>
            <Title style={styles.sectionTitle}>تحليل NDVI</Title>
            <View style={styles.ndviCurrentContainer}>
              <View style={styles.ndviValue}>
                <Title style={styles.ndviNumber}>
                  {field.ndvi_current?.toFixed(2) || '0.00'}
                </Title>
                <Paragraph>القيمة الحالية</Paragraph>
              </View>
              <Icon name="leaf" size={60} color="#4CAF50" />
            </View>

            {field.ndvi_history && field.ndvi_history.length > 0 && (
              <>
                <Paragraph style={styles.chartTitle}>السجل التاريخي (آخر 7 أيام)</Paragraph>
                <LineChart
                  data={ndviChartData}
                  width={Dimensions.get('window').width - 60}
                  height={180}
                  chartConfig={{
                    backgroundColor: '#FFF',
                    backgroundGradientFrom: '#FFF',
                    backgroundGradientTo: '#FFF',
                    decimalPlaces: 2,
                    color: (opacity = 1) => `rgba(76, 175, 80, ${opacity})`,
                    labelColor: () => '#666',
                    style: { borderRadius: 16 },
                    propsForDots: {
                      r: '4',
                      strokeWidth: '2',
                      stroke: '#4CAF50',
                    },
                  }}
                  bezier
                  style={styles.chart}
                />
              </>
            )}

            <Button
              mode="contained"
              icon="image-filter-hdr"
              onPress={() => navigation.navigate('NDVI', { fieldId: field.id })}
              style={styles.actionButton}
            >
              تحليل متقدم
            </Button>
          </Card.Content>
        </Card>
      )}

      {activeTab === 'weather' && (
        <Card style={styles.contentCard}>
          <Card.Content>
            <Title style={styles.sectionTitle}>حالة الطقس</Title>
            <View style={styles.weatherContainer}>
              <View style={styles.weatherMain}>
                <Icon name="weather-partly-cloudy" size={70} color="#FFA726" />
                <Title style={styles.weatherTemp}>
                  {field.weather?.temp || 25}°C
                </Title>
              </View>
              <Paragraph style={styles.weatherCondition}>
                {field.weather?.condition || 'غائم جزئياً'}
              </Paragraph>
            </View>

            <Divider style={styles.divider} />

            <View style={styles.weatherDetails}>
              <View style={styles.weatherDetailItem}>
                <Icon name="water-percent" size={30} color="#1976D2" />
                <Paragraph style={styles.weatherDetailLabel}>الرطوبة</Paragraph>
                <Title style={styles.weatherDetailValue}>
                  {field.weather?.humidity || 45}%
                </Title>
              </View>
            </View>
          </Card.Content>
        </Card>
      )}

      {/* Recommendations */}
      {field.recommendations && field.recommendations.length > 0 && (
        <Card style={styles.contentCard}>
          <Card.Content>
            <Title style={styles.sectionTitle}>التوصيات</Title>
            {field.recommendations.map((rec, index) => (
              <View key={index} style={styles.recommendationItem}>
                <Icon name="lightbulb-on" size={20} color="#FFA726" />
                <Paragraph style={styles.recommendationText}>{rec}</Paragraph>
              </View>
            ))}
          </Card.Content>
        </Card>
      )}

      {/* Action Buttons */}
      <View style={styles.actionsContainer}>
        <Button
          mode="contained"
          icon="robot"
          onPress={() => {/* Get AI advice */}}
          style={[styles.actionButton, { backgroundColor: '#9C27B0' }]}
        >
          استشارة الذكاء الاصطناعي
        </Button>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  mapContainer: {
    height: 200,
    position: 'relative',
  },
  map: {
    ...StyleSheet.absoluteFillObject,
  },
  mapOverlay: {
    position: 'absolute',
    top: 10,
    right: 10,
  },
  statusChip: {
    elevation: 3,
  },
  statusChipText: {
    color: 'white',
    fontWeight: 'bold',
  },
  infoCard: {
    margin: 10,
    marginTop: -30,
    elevation: 4,
    borderRadius: 15,
  },
  fieldName: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  infoItem: {
    alignItems: 'center',
  },
  infoText: {
    marginTop: 5,
    fontSize: 12,
    color: '#666',
  },
  tabContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    padding: 10,
    gap: 10,
  },
  tabButton: {
    flex: 1,
  },
  contentCard: {
    margin: 10,
    borderRadius: 15,
  },
  sectionTitle: {
    fontSize: 18,
    marginBottom: 15,
    color: '#333',
  },
  ndviCurrentContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    padding: 15,
    backgroundColor: '#E8F5E9',
    borderRadius: 10,
  },
  ndviValue: {
    alignItems: 'flex-start',
  },
  ndviNumber: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#2E7D32',
  },
  chartTitle: {
    textAlign: 'center',
    marginBottom: 10,
    color: '#666',
  },
  chart: {
    borderRadius: 16,
    marginVertical: 10,
  },
  weatherContainer: {
    alignItems: 'center',
    padding: 20,
  },
  weatherMain: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 20,
  },
  weatherTemp: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#333',
  },
  weatherCondition: {
    fontSize: 18,
    color: '#666',
    marginTop: 10,
  },
  divider: {
    marginVertical: 15,
  },
  weatherDetails: {
    flexDirection: 'row',
    justifyContent: 'center',
  },
  weatherDetailItem: {
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  weatherDetailLabel: {
    fontSize: 12,
    color: '#999',
    marginTop: 5,
  },
  weatherDetailValue: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  recommendationItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 10,
    padding: 10,
    backgroundColor: '#FFF8E1',
    borderRadius: 8,
  },
  recommendationText: {
    flex: 1,
    marginLeft: 10,
    color: '#333',
  },
  actionsContainer: {
    padding: 10,
    paddingBottom: 30,
  },
  actionButton: {
    marginVertical: 5,
    paddingVertical: 5,
  },
});
