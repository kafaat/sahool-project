import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  RefreshControl,
  TouchableOpacity
} from 'react-native';
import {
  Text,
  Card,
  Chip,
  Searchbar,
  FAB,
  ActivityIndicator,
  useTheme
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { getFields } from '../services/api';

type FieldsScreenProps = {
  navigation: NativeStackNavigationProp<any>;
};

interface Field {
  id: number;
  name: string;
  area: number;
  crop_type: string;
  health_score: number;
  ndvi_value: number;
  status: string;
  location: {
    lat: number;
    lon: number;
  };
}

export default function FieldsScreen({ navigation }: FieldsScreenProps) {
  const theme = useTheme();
  const [fields, setFields] = useState<Field[]>([]);
  const [filteredFields, setFilteredFields] = useState<Field[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadFields();
  }, []);

  useEffect(() => {
    filterFields();
  }, [searchQuery, fields]);

  const loadFields = async () => {
    try {
      const data = await getFields();
      setFields(data);
      setFilteredFields(data);
    } catch (error) {
      console.error('Error loading fields:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadFields();
  };

  const filterFields = () => {
    if (!searchQuery) {
      setFilteredFields(fields);
      return;
    }

    const filtered = fields.filter(
      (field) =>
        field.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        field.crop_type.toLowerCase().includes(searchQuery.toLowerCase())
    );
    setFilteredFields(filtered);
  };

  const getHealthColor = (score: number) => {
    if (score >= 80) return '#4CAF50';
    if (score >= 60) return '#FFC107';
    return '#F44336';
  };

  const getHealthIcon = (score: number) => {
    if (score >= 80) return 'check-circle';
    if (score >= 60) return 'alert-circle';
    return 'close-circle';
  };

  const renderFieldCard = ({ item }: { item: Field }) => (
    <TouchableOpacity
      onPress={() => navigation.navigate('FieldDetail', { fieldId: item.id })}
    >
      <Card style={styles.card}>
        <Card.Content>
          <View style={styles.cardHeader}>
            <View style={styles.fieldInfo}>
              <Text variant="titleMedium" style={styles.fieldName}>
                {item.name}
              </Text>
              <Text variant="bodySmall" style={styles.cropType}>
                <Icon name="sprout" size={14} /> {item.crop_type}
              </Text>
            </View>
            <Icon
              name={getHealthIcon(item.health_score)}
              size={32}
              color={getHealthColor(item.health_score)}
            />
          </View>

          <View style={styles.metrics}>
            <View style={styles.metricItem}>
              <Icon name="ruler-square" size={20} color="#666" />
              <Text variant="bodySmall" style={styles.metricText}>
                {item.area.toFixed(1)} هكتار
              </Text>
            </View>

            <View style={styles.metricItem}>
              <Icon name="image-filter-hdr" size={20} color="#666" />
              <Text variant="bodySmall" style={styles.metricText}>
                NDVI: {item.ndvi_value.toFixed(2)}
              </Text>
            </View>

            <View style={styles.metricItem}>
              <Icon name="heart-pulse" size={20} color="#666" />
              <Text variant="bodySmall" style={styles.metricText}>
                {item.health_score}%
              </Text>
            </View>
          </View>

          <View style={styles.chips}>
            <Chip
              mode="outlined"
              style={[
                styles.statusChip,
                { borderColor: item.status === 'active' ? '#4CAF50' : '#999' },
              ]}
              textStyle={{ fontSize: 12 }}
            >
              {item.status === 'active' ? 'نشط' : 'غير نشط'}
            </Chip>
          </View>
        </Card.Content>
      </Card>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={styles.loadingText}>جاري تحميل الحقول...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Searchbar
        placeholder="ابحث عن حقل أو محصول..."
        onChangeText={setSearchQuery}
        value={searchQuery}
        style={styles.searchbar}
        icon="magnify"
        clearIcon="close"
      />

      <View style={styles.summary}>
        <Text variant="titleSmall" style={styles.summaryText}>
          إجمالي الحقول: {filteredFields.length}
        </Text>
      </View>

      {filteredFields.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Icon name="map-marker-off" size={64} color="#ccc" />
          <Text variant="titleMedium" style={styles.emptyText}>
            لا توجد حقول
          </Text>
          <Text variant="bodySmall" style={styles.emptySubtext}>
            {searchQuery
              ? 'لم يتم العثور على نتائج للبحث'
              : 'أضف حقلك الأول للبدء'}
          </Text>
        </View>
      ) : (
        <FlatList
          data={filteredFields}
          renderItem={renderFieldCard}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              colors={[theme.colors.primary]}
            />
          }
        />
      )}

      <FAB
        icon="plus"
        style={styles.fab}
        onPress={() => alert('سيتم إضافة ميزة إضافة حقل جديد قريباً')}
        label="إضافة حقل"
      />
    </View>
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
  searchbar: {
    margin: 16,
    marginBottom: 8,
    elevation: 2,
  },
  summary: {
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  summaryText: {
    color: '#666',
  },
  list: {
    padding: 16,
    paddingBottom: 80,
  },
  card: {
    marginBottom: 12,
    elevation: 2,
    borderRadius: 12,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  fieldInfo: {
    flex: 1,
  },
  fieldName: {
    fontWeight: 'bold',
    marginBottom: 4,
  },
  cropType: {
    color: '#666',
  },
  metrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  metricItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metricText: {
    color: '#666',
    marginLeft: 4,
  },
  chips: {
    flexDirection: 'row',
    gap: 8,
  },
  statusChip: {
    height: 28,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyText: {
    marginTop: 16,
    color: '#666',
  },
  emptySubtext: {
    marginTop: 8,
    color: '#999',
    textAlign: 'center',
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
    backgroundColor: '#2E7D32',
  },
});
