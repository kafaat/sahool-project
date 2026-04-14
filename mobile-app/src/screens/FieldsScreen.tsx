import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  FlatList,
  StyleSheet,
  RefreshControl,
  Dimensions,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Chip,
  ActivityIndicator,
  FAB,
  Searchbar,
  IconButton,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import MapView, { Polygon, PROVIDER_GOOGLE } from 'react-native-maps';
import { apiService } from '../services/api';

interface Field {
  id: number;
  name: string;
  area_hectares: number;
  crop_type: string;
  status: 'healthy' | 'warning' | 'critical';
  ndvi_current: number;
  geometry: {
    type: string;
    coordinates: number[][][];
  };
  region: string;
}

export default function FieldsScreen({ navigation }: any) {
  const [fields, setFields] = useState<Field[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list');

  const fetchFields = async () => {
    try {
      const response = await apiService.getFields();
      setFields(response.data);
    } catch (error) {
      console.error('Error fetching fields:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchFields();
  }, []);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchFields();
  }, []);

  const filteredFields = fields.filter(
    (field) =>
      field.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      field.crop_type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return '#4CAF50';
      case 'warning':
        return '#FF9800';
      case 'critical':
        return '#F44336';
      default:
        return '#9E9E9E';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'صحي';
      case 'warning':
        return 'تحذير';
      case 'critical':
        return 'حرج';
      default:
        return 'غير محدد';
    }
  };

  const renderFieldCard = ({ item }: { item: Field }) => (
    <Card
      style={styles.card}
      onPress={() => navigation.navigate('FieldDetail', { fieldId: item.id })}
    >
      <Card.Content>
        <View style={styles.cardHeader}>
          <View style={styles.cardTitleContainer}>
            <Icon name="map-marker" size={24} color="#2E7D32" />
            <Title style={styles.cardTitle}>{item.name}</Title>
          </View>
          <Chip
            mode="flat"
            style={[styles.statusChip, { backgroundColor: getStatusColor(item.status) }]}
            textStyle={styles.statusChipText}
          >
            {getStatusLabel(item.status)}
          </Chip>
        </View>

        <View style={styles.cardDetails}>
          <View style={styles.detailItem}>
            <Icon name="sprout" size={18} color="#666" />
            <Paragraph style={styles.detailText}>{item.crop_type}</Paragraph>
          </View>
          <View style={styles.detailItem}>
            <Icon name="ruler-square" size={18} color="#666" />
            <Paragraph style={styles.detailText}>{item.area_hectares} هكتار</Paragraph>
          </View>
          <View style={styles.detailItem}>
            <Icon name="leaf" size={18} color="#666" />
            <Paragraph style={styles.detailText}>
              NDVI: {item.ndvi_current?.toFixed(2) || 'N/A'}
            </Paragraph>
          </View>
        </View>

        <View style={styles.regionContainer}>
          <Icon name="map" size={16} color="#999" />
          <Paragraph style={styles.regionText}>{item.region}</Paragraph>
        </View>
      </Card.Content>
    </Card>
  );

  const renderMapView = () => (
    <MapView
      style={styles.map}
      provider={PROVIDER_GOOGLE}
      initialRegion={{
        latitude: 15.3694,
        longitude: 44.191,
        latitudeDelta: 5,
        longitudeDelta: 5,
      }}
    >
      {filteredFields.map((field) => {
        if (field.geometry?.coordinates?.[0]) {
          const coordinates = field.geometry.coordinates[0].map(
            (coord: number[]) => ({
              latitude: coord[1],
              longitude: coord[0],
            })
          );
          return (
            <Polygon
              key={field.id}
              coordinates={coordinates}
              fillColor={`${getStatusColor(field.status)}40`}
              strokeColor={getStatusColor(field.status)}
              strokeWidth={2}
              tappable
              onPress={() =>
                navigation.navigate('FieldDetail', { fieldId: field.id })
              }
            />
          );
        }
        return null;
      })}
    </MapView>
  );

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2E7D32" />
        <Paragraph style={styles.loadingText}>جاري تحميل الحقول...</Paragraph>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Searchbar
          placeholder="بحث عن حقل..."
          onChangeText={setSearchQuery}
          value={searchQuery}
          style={styles.searchbar}
        />
        <View style={styles.viewToggle}>
          <IconButton
            icon="view-list"
            size={24}
            iconColor={viewMode === 'list' ? '#2E7D32' : '#999'}
            onPress={() => setViewMode('list')}
          />
          <IconButton
            icon="map"
            size={24}
            iconColor={viewMode === 'map' ? '#2E7D32' : '#999'}
            onPress={() => setViewMode('map')}
          />
        </View>
      </View>

      {viewMode === 'list' ? (
        <FlatList
          data={filteredFields}
          renderItem={renderFieldCard}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Icon name="map-marker-off" size={60} color="#CCC" />
              <Paragraph style={styles.emptyText}>لا توجد حقول</Paragraph>
            </View>
          }
        />
      ) : (
        renderMapView()
      )}

      <FAB
        icon="plus"
        style={styles.fab}
        onPress={() => {/* Navigate to add field screen */}}
        color="white"
      />
    </View>
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
  loadingText: {
    marginTop: 10,
    color: '#666',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
    backgroundColor: 'white',
    elevation: 2,
  },
  searchbar: {
    flex: 1,
    marginRight: 10,
    elevation: 0,
    backgroundColor: '#F5F5F5',
  },
  viewToggle: {
    flexDirection: 'row',
  },
  listContent: {
    padding: 10,
  },
  card: {
    marginBottom: 10,
    elevation: 2,
    borderRadius: 10,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  cardTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  cardTitle: {
    marginLeft: 8,
    fontSize: 18,
  },
  statusChip: {
    height: 28,
  },
  statusChipText: {
    color: 'white',
    fontSize: 12,
  },
  cardDetails: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 10,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 15,
    marginBottom: 5,
  },
  detailText: {
    marginLeft: 5,
    fontSize: 14,
    color: '#666',
  },
  regionContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#EEE',
    paddingTop: 10,
  },
  regionText: {
    marginLeft: 5,
    fontSize: 12,
    color: '#999',
  },
  map: {
    flex: 1,
    width: Dimensions.get('window').width,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyText: {
    marginTop: 10,
    color: '#999',
    fontSize: 16,
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
    backgroundColor: '#2E7D32',
  },
});
