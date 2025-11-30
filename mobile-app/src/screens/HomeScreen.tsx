import React, { useEffect, useState } from 'react';
import { View, ScrollView, StyleSheet, RefreshControl } from 'react-native';
import { Card, Title, Paragraph, Button, ActivityIndicator } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { apiService } from '../services/api';

interface DashboardData {
  totalFields: number;
  totalArea: number;
  avgNDVI: number;
  activeAlerts: number;
  weatherToday: {
    temp: number;
    condition: string;
  };
}

export default function HomeScreen({ navigation }: any) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [data, setData] = useState<DashboardData | null>(null);

  const fetchDashboardData = async () => {
    try {
      const response = await apiService.getDashboard();
      setData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchDashboardData();
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2E7D32" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <Title style={styles.title}>مرحباً بك في Sahool</Title>
        <Paragraph style={styles.subtitle}>منصتك الزراعية الذكية</Paragraph>
      </View>

      <View style={styles.statsContainer}>
        <Card style={styles.statCard}>
          <Card.Content style={styles.statContent}>
            <Icon name="map-marker" size={40} color="#2E7D32" />
            <Title style={styles.statNumber}>{data?.totalFields || 0}</Title>
            <Paragraph>الحقول</Paragraph>
          </Card.Content>
        </Card>

        <Card style={styles.statCard}>
          <Card.Content style={styles.statContent}>
            <Icon name="ruler-square" size={40} color="#1976D2" />
            <Title style={styles.statNumber}>{data?.totalArea || 0}</Title>
            <Paragraph>هكتار</Paragraph>
          </Card.Content>
        </Card>
      </View>

      <View style={styles.statsContainer}>
        <Card style={styles.statCard}>
          <Card.Content style={styles.statContent}>
            <Icon name="leaf" size={40} color="#388E3C" />
            <Title style={styles.statNumber}>{data?.avgNDVI?.toFixed(2) || '0.00'}</Title>
            <Paragraph>NDVI المتوسط</Paragraph>
          </Card.Content>
        </Card>

        <Card style={styles.statCard}>
          <Card.Content style={styles.statContent}>
            <Icon name="bell-alert" size={40} color="#D32F2F" />
            <Title style={styles.statNumber}>{data?.activeAlerts || 0}</Title>
            <Paragraph>تنبيهات</Paragraph>
          </Card.Content>
        </Card>
      </View>

      <Card style={styles.weatherCard}>
        <Card.Content>
          <View style={styles.weatherHeader}>
            <Icon name="weather-partly-cloudy" size={50} color="#FFA726" />
            <View style={styles.weatherInfo}>
              <Title>{data?.weatherToday?.temp || 25}°C</Title>
              <Paragraph>{data?.weatherToday?.condition || 'غائم جزئياً'}</Paragraph>
            </View>
          </View>
        </Card.Content>
      </Card>

      <Card style={styles.actionCard}>
        <Card.Content>
          <Title>الإجراءات السريعة</Title>
          <View style={styles.actionButtons}>
            <Button
              mode="contained"
              icon="map"
              onPress={() => navigation.navigate('Fields')}
              style={styles.actionButton}
            >
              عرض الحقول
            </Button>
            <Button
              mode="contained"
              icon="image-filter-hdr"
              onPress={() => navigation.navigate('NDVI')}
              style={styles.actionButton}
            >
              تحليل NDVI
            </Button>
          </View>
        </Card.Content>
      </Card>
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
  header: {
    padding: 20,
    backgroundColor: '#2E7D32',
  },
  title: {
    color: 'white',
    fontSize: 24,
    fontWeight: 'bold',
  },
  subtitle: {
    color: 'white',
    fontSize: 14,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 10,
  },
  statCard: {
    flex: 1,
    margin: 5,
    elevation: 3,
  },
  statContent: {
    alignItems: 'center',
    padding: 15,
  },
  statNumber: {
    fontSize: 28,
    fontWeight: 'bold',
    marginTop: 5,
  },
  weatherCard: {
    margin: 10,
    elevation: 3,
  },
  weatherHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  weatherInfo: {
    marginLeft: 20,
  },
  actionCard: {
    margin: 10,
    marginBottom: 20,
    elevation: 3,
  },
  actionButtons: {
    marginTop: 10,
  },
  actionButton: {
    marginVertical: 5,
  },
});
