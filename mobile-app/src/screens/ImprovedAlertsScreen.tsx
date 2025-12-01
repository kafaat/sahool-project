/**
 * Improved Alerts Screen
 * شاشة التنبيهات المحسّنة
 *
 * Features:
 * - Enhanced alert cards with priority colors
 * - Better filtering and categorization
 * - Animated alert cards
 * - Severity-based visual design
 * - Quick action buttons
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  RefreshControl,
  Pressable,
  ScrollView,
} from 'react-native';
import { Text } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import Animated, { FadeInDown, FadeInRight } from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';

import { Card, Chip, StatCard, Button } from '../components/ui';
import { Theme } from '../theme/design-system';
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

export default function ImprovedAlertsScreen() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [filteredAlerts, setFilteredAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<'all' | 'unread' | 'high' | 'resolved'>('all');

  useEffect(() => {
    loadAlerts();
  }, []);

  useEffect(() => {
    filterAlerts();
  }, [filter, alerts]);

  const loadAlerts = async () => {
    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const mockAlerts: Alert[] = [
        {
          id: 1,
          type: 'low_ndvi',
          severity: 'critical',
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
          severity: 'high',
          title: 'رطوبة التربة منخفضة',
          message: 'رطوبة التربة وصلت إلى 25%. يُنصح بالري قريباً.',
          field_name: 'حقل الخيار',
          field_id: 2,
          timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
          read: false,
          resolved: false,
        },
        {
          id: 3,
          type: 'high_temperature',
          severity: 'medium',
          title: 'درجة حرارة مرتفعة',
          message: 'درجة الحرارة المتوقعة غداً 42°م. راقب النباتات عن كثب.',
          field_name: 'جميع الحقول',
          field_id: 0,
          timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          read: true,
          resolved: false,
        },
        {
          id: 4,
          type: 'low_battery',
          severity: 'low',
          title: 'بطارية الحساس منخفضة',
          message: 'حساس رطوبة التربة #SM-001 بطاريته 15%. استبدلها قريباً.',
          field_name: 'حقل الفلفل',
          field_id: 3,
          timestamp: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
          read: true,
          resolved: true,
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
          ['high', 'critical'].includes(alert.severity) && !alert.resolved
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

  const getSeverityConfig = (severity: string) => {
    switch (severity) {
      case 'critical':
        return {
          color: '#D32F2F',
          bgColor: '#FFEBEE',
          icon: 'alert-octagon',
          label: 'حرج',
          gradient: ['#D32F2F', '#F44336'],
        };
      case 'high':
        return {
          color: '#F44336',
          bgColor: '#FFF3E0',
          icon: 'alert',
          label: 'عالي',
          gradient: ['#F44336', '#FF6B6B'],
        };
      case 'medium':
        return {
          color: Theme.colors.warning.main,
          bgColor: '#FFF9E6',
          icon: 'alert-circle',
          label: 'متوسط',
          gradient: [Theme.colors.warning.main, Theme.colors.warning.light],
        };
      case 'low':
        return {
          color: Theme.colors.info.main,
          bgColor: '#E3F2FD',
          icon: 'information',
          label: 'منخفض',
          gradient: [Theme.colors.info.main, Theme.colors.info.light],
        };
      default:
        return {
          color: Theme.colors.gray[500],
          bgColor: Theme.colors.gray[100],
          icon: 'bell',
          label: severity,
          gradient: [Theme.colors.gray[500], Theme.colors.gray[400]],
        };
    }
  };

  const getTypeConfig = (type: string) => {
    switch (type) {
      case 'low_ndvi':
        return { icon: 'image-filter-hdr', label: 'NDVI منخفض' };
      case 'low_moisture':
        return { icon: 'water-alert', label: 'رطوبة منخفضة' };
      case 'high_temperature':
        return { icon: 'thermometer-alert', label: 'حرارة مرتفعة' };
      case 'low_battery':
        return { icon: 'battery-low', label: 'بطارية منخفضة' };
      default:
        return { icon: 'bell', label: 'تنبيه' };
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

  const stats = {
    total: alerts.length,
    unread: alerts.filter((a) => !a.read).length,
    highPriority: alerts.filter((a) => ['high', 'critical'].includes(a.severity) && !a.resolved).length,
    resolved: alerts.filter((a) => a.resolved).length,
  };

  const renderAlert = ({ item, index }: { item: Alert; index: number }) => {
    const severityConfig = getSeverityConfig(item.severity);
    const typeConfig = getTypeConfig(item.type);

    return (
      <Animated.View entering={FadeInDown.delay(index * 100).springify()}>
        <Card
          pressable
          onPress={() => console.log('Alert pressed:', item.id)}
          elevation="md"
          rounded="lg"
          style={[
            styles.alertCard,
            !item.read && styles.unreadCard,
            item.resolved && styles.resolvedCard,
          ]}
        >
          {/* Severity Indicator Bar */}
          <View style={[styles.severityBar, { backgroundColor: severityConfig.color }]} />

          <View style={styles.alertContent}>
            {/* Header */}
            <View style={styles.alertHeader}>
              <LinearGradient
                colors={severityConfig.gradient}
                style={styles.alertIconContainer}
              >
                <Icon name={typeConfig.icon} size={24} color="#fff" />
              </LinearGradient>

              <View style={styles.alertHeaderText}>
                <View style={styles.alertTitleRow}>
                  <Text style={styles.alertTitle}>{item.title}</Text>
                  {!item.read && <View style={styles.unreadDot} />}
                </View>

                <View style={styles.alertMetaRow}>
                  <Chip
                    label={severityConfig.label}
                    variant="filled"
                    size="small"
                    style={{ backgroundColor: severityConfig.color }}
                  />
                  <Chip
                    label={typeConfig.label}
                    variant="outlined"
                    size="small"
                    color="default"
                  />
                </View>
              </View>
            </View>

            {/* Message */}
            <Text style={styles.alertMessage}>{item.message}</Text>

            {/* Footer */}
            <View style={styles.alertFooter}>
              <View style={styles.alertFooterLeft}>
                <Icon name="map-marker" size={14} color={Theme.colors.text.secondary} />
                <Text style={styles.fieldName}>{item.field_name}</Text>
              </View>

              <View style={styles.alertFooterRight}>
                <Icon name="clock-outline" size={14} color={Theme.colors.text.disabled} />
                <Text style={styles.timestamp}>{formatTime(item.timestamp)}</Text>
              </View>
            </View>

            {/* Actions */}
            {!item.resolved && (
              <View style={styles.alertActions}>
                <Button
                  title="عرض التفاصيل"
                  variant="outlined"
                  color="primary"
                  size="small"
                  onPress={() => console.log('View details')}
                />
                <Button
                  title="وضع علامة كمحلول"
                  variant="text"
                  color="success"
                  size="small"
                  onPress={() => console.log('Mark as resolved')}
                  icon={<Icon name="check" size={16} color={Theme.colors.success.main} />}
                />
              </View>
            )}

            {item.resolved && (
              <View style={styles.resolvedBadge}>
                <Icon name="check-circle" size={16} color={Theme.colors.success.main} />
                <Text style={styles.resolvedText}>تم الحل</Text>
              </View>
            )}
          </View>
        </Card>
      </Animated.View>
    );
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <Icon name="bell-ring" size={64} color={Theme.colors.primary.main} />
        <Text style={styles.loadingText}>جاري تحميل التنبيهات...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header with Gradient */}
      <LinearGradient
        colors={[Theme.colors.primary.main, Theme.colors.primary.dark]}
        style={styles.header}
      >
        <Text style={styles.headerTitle}>التنبيهات 🔔</Text>
        <Text style={styles.headerSubtitle}>مراقبة جميع التنبيهات والإشعارات</Text>
      </LinearGradient>

      {/* Quick Stats */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.statsScrollContainer}
        style={styles.statsContainer}
      >
        <Animated.View entering={FadeInRight.delay(100)}>
          <StatCard
            title="إجمالي"
            value={stats.total.toString()}
            icon={<Icon name="bell-ring" size={28} color={Theme.colors.primary.main} />}
            color="primary"
            variant="minimal"
            style={styles.statCardSmall}
          />
        </Animated.View>

        <Animated.View entering={FadeInRight.delay(200)}>
          <StatCard
            title="غير مقروءة"
            value={stats.unread.toString()}
            icon={<Icon name="bell-badge" size={28} color={Theme.colors.error.main} />}
            color="error"
            variant="minimal"
            style={styles.statCardSmall}
          />
        </Animated.View>

        <Animated.View entering={FadeInRight.delay(300)}>
          <StatCard
            title="أولوية عالية"
            value={stats.highPriority.toString()}
            icon={<Icon name="alert" size={28} color={Theme.colors.warning.main} />}
            color="warning"
            variant="minimal"
            style={styles.statCardSmall}
          />
        </Animated.View>

        <Animated.View entering={FadeInRight.delay(400)}>
          <StatCard
            title="محلولة"
            value={stats.resolved.toString()}
            icon={<Icon name="check-circle" size={28} color={Theme.colors.success.main} />}
            color="success"
            variant="minimal"
            style={styles.statCardSmall}
          />
        </Animated.View>
      </ScrollView>

      {/* Filter Chips */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.filterChipsContainer}
      >
        <Chip
          label={`الكل (${alerts.length})`}
          variant={filter === 'all' ? 'filled' : 'outlined'}
          color="primary"
          onPress={() => setFilter('all')}
          selected={filter === 'all'}
        />
        <Chip
          label={`غير مقروءة (${stats.unread})`}
          variant={filter === 'unread' ? 'filled' : 'outlined'}
          color="error"
          onPress={() => setFilter('unread')}
          selected={filter === 'unread'}
        />
        <Chip
          label={`مهمة (${stats.highPriority})`}
          variant={filter === 'high' ? 'filled' : 'outlined'}
          color="warning"
          onPress={() => setFilter('high')}
          selected={filter === 'high'}
        />
        <Chip
          label={`محلولة (${stats.resolved})`}
          variant={filter === 'resolved' ? 'filled' : 'outlined'}
          color="success"
          onPress={() => setFilter('resolved')}
          selected={filter === 'resolved'}
        />
      </ScrollView>

      {/* Alerts List */}
      {filteredAlerts.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Icon name="bell-check" size={64} color={Theme.colors.gray[400]} />
          <Text style={styles.emptyText}>لا توجد تنبيهات</Text>
          <Text style={styles.emptySubtext}>
            {filter !== 'all'
              ? 'لا توجد تنبيهات في هذا التصنيف'
              : 'جميع الأمور على ما يرام 🎉'}
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
              colors={[Theme.colors.primary.main]}
              tintColor={Theme.colors.primary.main}
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
    backgroundColor: Theme.colors.background.default,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Theme.colors.background.default,
  },
  loadingText: {
    marginTop: Theme.spacing.md,
    ...Theme.typography.styles.body1,
    color: Theme.colors.text.secondary,
  },
  header: {
    padding: Theme.spacing.xl,
    paddingTop: Theme.spacing['2xl'],
    paddingBottom: Theme.spacing.lg,
    borderBottomLeftRadius: Theme.borderRadius['2xl'],
    borderBottomRightRadius: Theme.borderRadius['2xl'],
  },
  headerTitle: {
    ...Theme.typography.styles.h2,
    color: '#fff',
    marginBottom: Theme.spacing.xs,
  },
  headerSubtitle: {
    ...Theme.typography.styles.body2,
    color: 'rgba(255,255,255,0.9)',
  },
  statsContainer: {
    marginTop: -Theme.spacing.lg,
    marginBottom: Theme.spacing.sm,
  },
  statsScrollContainer: {
    paddingHorizontal: Theme.spacing.md,
    gap: Theme.spacing.sm,
  },
  statCardSmall: {
    minWidth: 130,
  },
  filterChipsContainer: {
    paddingHorizontal: Theme.spacing.md,
    gap: Theme.spacing.sm,
    paddingVertical: Theme.spacing.md,
  },
  list: {
    padding: Theme.spacing.md,
    paddingBottom: Theme.spacing.xl,
  },
  alertCard: {
    marginBottom: Theme.spacing.md,
    overflow: 'hidden',
  },
  unreadCard: {
    borderLeftWidth: 4,
    borderLeftColor: Theme.colors.primary.main,
  },
  resolvedCard: {
    opacity: 0.75,
  },
  severityBar: {
    height: 4,
    width: '100%',
  },
  alertContent: {
    padding: Theme.spacing.md,
  },
  alertHeader: {
    flexDirection: 'row',
    gap: Theme.spacing.md,
    marginBottom: Theme.spacing.md,
  },
  alertIconContainer: {
    width: 48,
    height: 48,
    borderRadius: Theme.borderRadius.lg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  alertHeaderText: {
    flex: 1,
    gap: Theme.spacing.sm,
  },
  alertTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.sm,
  },
  alertTitle: {
    ...Theme.typography.styles.body1,
    fontWeight: '600',
    color: Theme.colors.text.primary,
    flex: 1,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Theme.colors.primary.main,
  },
  alertMetaRow: {
    flexDirection: 'row',
    gap: Theme.spacing.xs,
    flexWrap: 'wrap',
  },
  alertMessage: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.text.secondary,
    lineHeight: 22,
    marginBottom: Theme.spacing.md,
  },
  alertFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: Theme.spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Theme.colors.gray[200],
    marginBottom: Theme.spacing.md,
  },
  alertFooterLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.xs,
  },
  fieldName: {
    ...Theme.typography.styles.caption,
    color: Theme.colors.text.secondary,
  },
  alertFooterRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.xs,
  },
  timestamp: {
    ...Theme.typography.styles.caption,
    color: Theme.colors.text.disabled,
  },
  alertActions: {
    flexDirection: 'row',
    gap: Theme.spacing.sm,
    flexWrap: 'wrap',
  },
  resolvedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.xs,
    paddingVertical: Theme.spacing.xs,
    paddingHorizontal: Theme.spacing.md,
    backgroundColor: Theme.colors.success.light + '20',
    borderRadius: Theme.borderRadius.lg,
    alignSelf: 'flex-start',
  },
  resolvedText: {
    ...Theme.typography.styles.caption,
    color: Theme.colors.success.main,
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: Theme.spacing['2xl'],
  },
  emptyText: {
    ...Theme.typography.styles.h3,
    color: Theme.colors.text.secondary,
    marginTop: Theme.spacing.md,
    marginBottom: Theme.spacing.xs,
  },
  emptySubtext: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.text.disabled,
    textAlign: 'center',
  },
});
