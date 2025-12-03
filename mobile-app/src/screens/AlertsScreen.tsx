import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  FlatList,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Chip,
  ActivityIndicator,
  Badge,
  IconButton,
  Divider,
  Menu,
  Button,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { apiService } from '../services/api';

interface Alert {
  id: number;
  type: 'warning' | 'critical' | 'info' | 'success';
  title: string;
  message: string;
  field_name: string;
  field_id: number;
  created_at: string;
  is_read: boolean;
  category: string;
}

export default function AlertsScreen({ navigation }: any) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<string>('all');
  const [menuVisible, setMenuVisible] = useState(false);

  const fetchAlerts = async () => {
    try {
      const response = await apiService.getAlerts();
      setAlerts(response.data || []);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchAlerts();
  }, []);

  const markAsRead = async (alertId: number) => {
    try {
      await apiService.markAlertAsRead(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, is_read: true } : a))
      );
    } catch (error) {
      console.error('Error marking alert as read:', error);
    }
  };

  const getAlertIcon = (type: string, category: string) => {
    switch (category) {
      case 'weather':
        return 'weather-lightning-rainy';
      case 'ndvi':
        return 'leaf';
      case 'irrigation':
        return 'water';
      case 'pest':
        return 'bug';
      case 'soil':
        return 'terrain';
      default:
        switch (type) {
          case 'critical':
            return 'alert-circle';
          case 'warning':
            return 'alert';
          case 'success':
            return 'check-circle';
          default:
            return 'information';
        }
    }
  };

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'critical':
        return '#F44336';
      case 'warning':
        return '#FF9800';
      case 'success':
        return '#4CAF50';
      default:
        return '#2196F3';
    }
  };

  const getAlertBgColor = (type: string) => {
    switch (type) {
      case 'critical':
        return '#FFEBEE';
      case 'warning':
        return '#FFF3E0';
      case 'success':
        return '#E8F5E9';
      default:
        return '#E3F2FD';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (hours < 1) return 'منذ دقائق';
    if (hours < 24) return `منذ ${hours} ساعة`;
    if (days < 7) return `منذ ${days} يوم`;
    return date.toLocaleDateString('ar-YE');
  };

  const filteredAlerts = alerts.filter((alert) => {
    if (filter === 'all') return true;
    if (filter === 'unread') return !alert.is_read;
    return alert.type === filter;
  });

  const unreadCount = alerts.filter((a) => !a.is_read).length;

  const renderAlertCard = ({ item }: { item: Alert }) => (
    <TouchableOpacity
      onPress={() => {
        markAsRead(item.id);
        navigation.navigate('FieldDetail', { fieldId: item.field_id });
      }}
      activeOpacity={0.8}
    >
      <Card
        style={[
          styles.alertCard,
          { backgroundColor: getAlertBgColor(item.type) },
          !item.is_read && styles.unreadCard,
        ]}
      >
        <Card.Content>
          <View style={styles.alertHeader}>
            <View style={styles.alertIconContainer}>
              <Icon
                name={getAlertIcon(item.type, item.category)}
                size={28}
                color={getAlertColor(item.type)}
              />
              {!item.is_read && <Badge style={styles.unreadBadge} size={8} />}
            </View>
            <View style={styles.alertContent}>
              <View style={styles.alertTitleRow}>
                <Title style={styles.alertTitle}>{item.title}</Title>
                <Chip
                  mode="flat"
                  style={[
                    styles.typeChip,
                    { backgroundColor: getAlertColor(item.type) },
                  ]}
                  textStyle={styles.typeChipText}
                  compact
                >
                  {item.type === 'critical'
                    ? 'حرج'
                    : item.type === 'warning'
                    ? 'تحذير'
                    : item.type === 'success'
                    ? 'نجاح'
                    : 'معلومة'}
                </Chip>
              </View>
              <Paragraph style={styles.alertMessage}>{item.message}</Paragraph>
              <View style={styles.alertFooter}>
                <View style={styles.fieldInfo}>
                  <Icon name="map-marker" size={14} color="#666" />
                  <Paragraph style={styles.fieldName}>{item.field_name}</Paragraph>
                </View>
                <Paragraph style={styles.alertTime}>
                  {formatDate(item.created_at)}
                </Paragraph>
              </View>
            </View>
          </View>
        </Card.Content>
      </Card>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2E7D32" />
        <Paragraph style={styles.loadingText}>جاري تحميل التنبيهات...</Paragraph>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header with filter */}
      <View style={styles.header}>
        <View style={styles.headerTitle}>
          <Title style={styles.title}>التنبيهات</Title>
          {unreadCount > 0 && (
            <Badge style={styles.headerBadge}>{unreadCount}</Badge>
          )}
        </View>
        <Menu
          visible={menuVisible}
          onDismiss={() => setMenuVisible(false)}
          anchor={
            <IconButton
              icon="filter-variant"
              size={24}
              onPress={() => setMenuVisible(true)}
            />
          }
        >
          <Menu.Item
            onPress={() => {
              setFilter('all');
              setMenuVisible(false);
            }}
            title="الكل"
            leadingIcon={filter === 'all' ? 'check' : undefined}
          />
          <Menu.Item
            onPress={() => {
              setFilter('unread');
              setMenuVisible(false);
            }}
            title="غير مقروءة"
            leadingIcon={filter === 'unread' ? 'check' : undefined}
          />
          <Divider />
          <Menu.Item
            onPress={() => {
              setFilter('critical');
              setMenuVisible(false);
            }}
            title="حرج"
            leadingIcon="alert-circle"
          />
          <Menu.Item
            onPress={() => {
              setFilter('warning');
              setMenuVisible(false);
            }}
            title="تحذير"
            leadingIcon="alert"
          />
          <Menu.Item
            onPress={() => {
              setFilter('info');
              setMenuVisible(false);
            }}
            title="معلومة"
            leadingIcon="information"
          />
        </Menu>
      </View>

      {/* Filter Chips */}
      <View style={styles.filterContainer}>
        <Chip
          selected={filter === 'all'}
          onPress={() => setFilter('all')}
          style={styles.filterChip}
        >
          الكل ({alerts.length})
        </Chip>
        <Chip
          selected={filter === 'critical'}
          onPress={() => setFilter('critical')}
          style={[styles.filterChip, filter === 'critical' && { backgroundColor: '#FFCDD2' }]}
        >
          حرج ({alerts.filter((a) => a.type === 'critical').length})
        </Chip>
        <Chip
          selected={filter === 'warning'}
          onPress={() => setFilter('warning')}
          style={[styles.filterChip, filter === 'warning' && { backgroundColor: '#FFE0B2' }]}
        >
          تحذير ({alerts.filter((a) => a.type === 'warning').length})
        </Chip>
      </View>

      {/* Alerts List */}
      <FlatList
        data={filteredAlerts}
        renderItem={renderAlertCard}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Icon name="bell-off" size={60} color="#CCC" />
            <Paragraph style={styles.emptyText}>لا توجد تنبيهات</Paragraph>
            <Paragraph style={styles.emptySubtext}>
              ستظهر التنبيهات هنا عندما تحتاج حقولك إلى اهتمام
            </Paragraph>
          </View>
        }
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
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 15,
    backgroundColor: 'white',
    elevation: 2,
  },
  headerTitle: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  headerBadge: {
    marginLeft: 10,
    backgroundColor: '#F44336',
  },
  filterContainer: {
    flexDirection: 'row',
    padding: 10,
    gap: 8,
  },
  filterChip: {
    marginRight: 5,
  },
  listContent: {
    padding: 10,
    paddingBottom: 30,
  },
  alertCard: {
    marginBottom: 10,
    borderRadius: 12,
    borderLeftWidth: 4,
  },
  unreadCard: {
    borderLeftColor: '#2E7D32',
  },
  alertHeader: {
    flexDirection: 'row',
  },
  alertIconContainer: {
    position: 'relative',
    marginRight: 12,
  },
  unreadBadge: {
    position: 'absolute',
    top: -2,
    right: -2,
    backgroundColor: '#4CAF50',
  },
  alertContent: {
    flex: 1,
  },
  alertTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 5,
  },
  alertTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    flex: 1,
  },
  typeChip: {
    height: 24,
  },
  typeChipText: {
    color: 'white',
    fontSize: 10,
  },
  alertMessage: {
    fontSize: 14,
    color: '#333',
    marginBottom: 10,
  },
  alertFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  fieldInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  fieldName: {
    marginLeft: 5,
    fontSize: 12,
    color: '#666',
  },
  alertTime: {
    fontSize: 11,
    color: '#999',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyText: {
    marginTop: 15,
    fontSize: 18,
    color: '#666',
  },
  emptySubtext: {
    marginTop: 5,
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    paddingHorizontal: 40,
  },
});
