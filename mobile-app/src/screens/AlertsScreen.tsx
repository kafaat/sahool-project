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
  SegmentedButtons,
  ActivityIndicator,
  useTheme,
  Badge
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { getAlerts } from '../services/api';

interface Alert {
  id: number;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  field_name: string;
  field_id: number;
  timestamp: string;
  read: boolean;
  resolved: boolean;
}

export default function AlertsScreen() {
  const theme = useTheme();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [filteredAlerts, setFilteredAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadAlerts();
  }, []);

  useEffect(() => {
    filterAlerts();
  }, [filter, alerts]);

  const loadAlerts = async () => {
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Mock data
      const mockAlerts: Alert[] = [
        {
          id: 1,
          type: 'low_ndvi',
          severity: 'high',
          title: 'انخفاض NDVI حرج',
          message: 'قيمة NDVI انخفضت إلى 0.15 في حقل الطماطم. يتطلب تدخل فوري.',
          field_name: 'حقل الطماطم الرئيسي',
          field_id: 1,
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          read: false,
          resolved: false,
        },
        {
          id: 2,
          type: 'low_moisture',
          severity: 'medium',
          title: 'رطوبة التربة منخفضة',
          message: 'رطوبة التربة وصلت إلى 25%. يُنصح بالري قريباً.',
          field_name: 'حقل الخيار',
          field_id: 2,
          timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
          read: true,
          resolved: false,
        },
        {
          id: 3,
          type: 'high_temperature',
          severity: 'low',
          title: 'درجة حرارة مرتفعة',
          message: 'درجة الحرارة المتوقعة غداً 42°م. راقب النباتات عن كثب.',
          field_name: 'جميع الحقول',
          field_id: 0,
          timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          read: true,
          resolved: true,
        },
        {
          id: 4,
          type: 'low_battery',
          severity: 'medium',
          title: 'بطارية الحساس منخفضة',
          message: 'حساس رطوبة التربة #SM-001 بطاريته 15%. استبدلها قريباً.',
          field_name: 'حقل الفلفل',
          field_id: 3,
          timestamp: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
          read: true,
          resolved: false,
        },
      ];

      setAlerts(mockAlerts);
    } catch (error) {
      console.error('Error loading alerts:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const filterAlerts = () => {
    let filtered = alerts;

    switch (filter) {
      case 'unread':
        filtered = alerts.filter((alert) => !alert.read);
        break;
      case 'high':
        filtered = alerts.filter((alert) =>
          ['high', 'critical'].includes(alert.severity)
        );
        break;
      case 'resolved':
        filtered = alerts.filter((alert) => alert.resolved);
        break;
      default:
        filtered = alerts;
    }

    setFilteredAlerts(filtered);
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadAlerts();
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return '#D32F2F';
      case 'high':
        return '#F44336';
      case 'medium':
        return '#FFC107';
      case 'low':
        return '#2196F3';
      default:
        return '#999';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'alert-octagon';
      case 'high':
        return 'alert';
      case 'medium':
        return 'alert-circle';
      case 'low':
        return 'information';
      default:
        return 'bell';
    }
  };

  const getSeverityLabel = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'حرج';
      case 'high':
        return 'عالي';
      case 'medium':
        return 'متوسط';
      case 'low':
        return 'منخفض';
      default:
        return severity;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'low_ndvi':
        return 'image-filter-hdr';
      case 'low_moisture':
        return 'water';
      case 'high_temperature':
        return 'thermometer';
      case 'low_battery':
        return 'battery-low';
      default:
        return 'bell';
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (hours < 1) return 'منذ دقائق';
    if (hours < 24) return `منذ ${hours} ساعة`;
    if (days === 1) return 'منذ يوم';
    return `منذ ${days} أيام`;
  };

  const renderAlert = ({ item }: { item: Alert }) => (
    <TouchableOpacity>
      <Card style={[
        styles.card,
        !item.read && styles.unreadCard,
        item.resolved && styles.resolvedCard
      ]}>
        <Card.Content>
          <View style={styles.alertHeader}>
            <View style={styles.alertIcon}>
              <Icon
                name={getTypeIcon(item.type)}
                size={24}
                color={getSeverityColor(item.severity)}
              />
            </View>

            <View style={styles.alertContent}>
              <View style={styles.alertTitle}>
                <Text variant="titleSmall" style={styles.alertTitleText}>
                  {item.title}
                </Text>
                {!item.read && <Badge size={8} style={styles.unreadBadge} />}
              </View>

              <Text variant="bodyMedium" style={styles.alertMessage}>
                {item.message}
              </Text>

              <View style={styles.alertMeta}>
                <Chip
                  mode="outlined"
                  compact
                  style={[
                    styles.severityChip,
                    { borderColor: getSeverityColor(item.severity) }
                  ]}
                  textStyle={{ fontSize: 11, color: getSeverityColor(item.severity) }}
                >
                  {getSeverityLabel(item.severity)}
                </Chip>

                <Text variant="bodySmall" style={styles.fieldName}>
                  <Icon name="map-marker" size={12} /> {item.field_name}
                </Text>

                <Text variant="bodySmall" style={styles.timestamp}>
                  <Icon name="clock-outline" size={12} /> {formatTime(item.timestamp)}
                </Text>
              </View>

              {item.resolved && (
                <Chip
                  mode="flat"
                  compact
                  style={styles.resolvedChip}
                  icon="check-circle"
                  textStyle={{ fontSize: 11 }}
                >
                  تم الحل
                </Chip>
              )}
            </View>
          </View>
        </Card.Content>
      </Card>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={styles.loadingText}>جاري تحميل التنبيهات...</Text>
      </View>
    );
  }

  const unreadCount = alerts.filter((a) => !a.read).length;
  const highPriorityCount = alerts.filter((a) =>
    ['high', 'critical'].includes(a.severity) && !a.resolved
  ).length;

  return (
    <View style={styles.container}>
      {/* Stats */}
      <View style={styles.stats}>
        <View style={styles.statItem}>
          <Text variant="titleLarge" style={styles.statValue}>
            {alerts.length}
          </Text>
          <Text variant="bodySmall" style={styles.statLabel}>
            إجمالي التنبيهات
          </Text>
        </View>

        <View style={styles.statItem}>
          <Text variant="titleLarge" style={[styles.statValue, { color: '#F44336' }]}>
            {unreadCount}
          </Text>
          <Text variant="bodySmall" style={styles.statLabel}>
            غير مقروءة
          </Text>
        </View>

        <View style={styles.statItem}>
          <Text variant="titleLarge" style={[styles.statValue, { color: '#FFC107' }]}>
            {highPriorityCount}
          </Text>
          <Text variant="bodySmall" style={styles.statLabel}>
            أولوية عالية
          </Text>
        </View>
      </View>

      {/* Filters */}
      <View style={styles.filterContainer}>
        <SegmentedButtons
          value={filter}
          onValueChange={setFilter}
          buttons={[
            { value: 'all', label: 'الكل' },
            { value: 'unread', label: 'غير مقروءة' },
            { value: 'high', label: 'مهمة' },
            { value: 'resolved', label: 'محلولة' },
          ]}
        />
      </View>

      {/* Alerts List */}
      {filteredAlerts.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Icon name="bell-off" size={64} color="#ccc" />
          <Text variant="titleMedium" style={styles.emptyText}>
            لا توجد تنبيهات
          </Text>
          <Text variant="bodySmall" style={styles.emptySubtext}>
            {filter !== 'all'
              ? 'لا توجد تنبيهات في هذا التصنيف'
              : 'جميع الأمور على ما يرام'}
          </Text>
        </View>
      ) : (
        <FlatList
          data={filteredAlerts}
          renderItem={renderAlert}
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
  stats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 16,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontWeight: 'bold',
  },
  statLabel: {
    color: '#666',
    marginTop: 4,
  },
  filterContainer: {
    padding: 16,
  },
  list: {
    padding: 16,
  },
  card: {
    marginBottom: 12,
    elevation: 2,
    borderRadius: 12,
  },
  unreadCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#2E7D32',
  },
  resolvedCard: {
    opacity: 0.7,
  },
  alertHeader: {
    flexDirection: 'row',
    gap: 12,
  },
  alertIcon: {
    paddingTop: 2,
  },
  alertContent: {
    flex: 1,
    gap: 8,
  },
  alertTitle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  alertTitleText: {
    fontWeight: 'bold',
  },
  unreadBadge: {
    backgroundColor: '#2E7D32',
  },
  alertMessage: {
    color: '#666',
    lineHeight: 20,
  },
  alertMeta: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: 8,
  },
  severityChip: {
    height: 24,
  },
  fieldName: {
    color: '#666',
  },
  timestamp: {
    color: '#999',
  },
  resolvedChip: {
    alignSelf: 'flex-start',
    backgroundColor: '#E8F5E9',
    height: 24,
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
});
