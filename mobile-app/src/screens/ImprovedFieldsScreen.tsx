/**
 * Improved Fields Screen
 * شاشة الحقول المحسّنة
 *
 * Features:
 * - Enhanced UI with new design system
 * - Animated field cards
 * - Better visual hierarchy
 * - Agricultural color scheme
 * - Improved search and filtering
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  RefreshControl,
  TextInput,
  Pressable,
  ScrollView,
} from 'react-native';
import { Text } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import Animated, { FadeInDown, FadeInRight } from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';

import { Card, Button, Chip, StatCard } from '../components/ui';
import { Theme } from '../theme/design-system';
import { getFields } from '../services/api';

type ImprovedFieldsScreenProps = {
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

export default function ImprovedFieldsScreen({ navigation }: ImprovedFieldsScreenProps) {
  const [fields, setFields] = useState<Field[]>([]);
  const [filteredFields, setFilteredFields] = useState<Field[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'active' | 'healthy'>('all');

  useEffect(() => {
    loadFields();
  }, []);

  useEffect(() => {
    filterFields();
  }, [searchQuery, fields, selectedFilter]);

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
    let filtered = fields;

    // Apply status filter
    if (selectedFilter === 'active') {
      filtered = filtered.filter((field) => field.status === 'active');
    } else if (selectedFilter === 'healthy') {
      filtered = filtered.filter((field) => field.health_score >= 80);
    }

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (field) =>
          field.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          field.crop_type.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    setFilteredFields(filtered);
  };

  const getHealthColor = (score: number): keyof typeof Theme.colors.agricultural.ndvi => {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'moderate';
    return 'poor';
  };

  const getHealthIcon = (score: number) => {
    if (score >= 80) return 'check-circle';
    if (score >= 60) return 'checkbox-marked-circle-outline';
    if (score >= 40) return 'alert-circle-outline';
    return 'close-circle';
  };

  const getNDVIColor = (value: number) => {
    if (value >= 0.6) return Theme.colors.agricultural.ndvi.excellent;
    if (value >= 0.4) return Theme.colors.agricultural.ndvi.good;
    if (value >= 0.2) return Theme.colors.agricultural.ndvi.moderate;
    return Theme.colors.agricultural.ndvi.poor;
  };

  // Calculate stats
  const stats = {
    total: fields.length,
    active: fields.filter((f) => f.status === 'active').length,
    healthy: fields.filter((f) => f.health_score >= 80).length,
    avgHealth: fields.length > 0
      ? fields.reduce((sum, f) => sum + f.health_score, 0) / fields.length
      : 0,
  };

  const renderFieldCard = ({ item, index }: { item: Field; index: number }) => {
    const healthCategory = getHealthColor(item.health_score);
    const healthColorValue = Theme.colors.agricultural.ndvi[healthCategory];

    return (
      <Animated.View entering={FadeInDown.delay(index * 100).springify()}>
        <Card
          pressable
          onPress={() => navigation.navigate('FieldDetail', { fieldId: item.id })}
          elevation="md"
          rounded="lg"
          style={styles.fieldCard}
        >
          {/* Gradient Header */}
          <LinearGradient
            colors={[healthColorValue, healthColorValue + '80']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.fieldCardHeader}
          >
            <View style={styles.fieldHeaderContent}>
              <View style={styles.fieldTitleContainer}>
                <Text style={styles.fieldName}>{item.name}</Text>
                <View style={styles.cropTypeContainer}>
                  <Icon name="sprout" size={14} color="rgba(255,255,255,0.9)" />
                  <Text style={styles.cropType}>{item.crop_type}</Text>
                </View>
              </View>

              <View style={styles.healthIconContainer}>
                <Icon
                  name={getHealthIcon(item.health_score)}
                  size={36}
                  color="#fff"
                />
              </View>
            </View>
          </LinearGradient>

          {/* Card Body */}
          <View style={styles.fieldCardBody}>
            {/* Metrics Grid */}
            <View style={styles.metricsGrid}>
              <View style={styles.metricItem}>
                <Icon name="ruler-square" size={20} color={Theme.colors.primary.main} />
                <Text style={styles.metricLabel}>المساحة</Text>
                <Text style={styles.metricValue}>{item.area.toFixed(1)} هكتار</Text>
              </View>

              <View style={styles.metricItem}>
                <Icon name="heart-pulse" size={20} color={healthColorValue} />
                <Text style={styles.metricLabel}>الصحة</Text>
                <Text style={[styles.metricValue, { color: healthColorValue }]}>
                  {item.health_score}%
                </Text>
              </View>

              <View style={styles.metricItem}>
                <Icon name="image-filter-hdr" size={20} color={getNDVIColor(item.ndvi_value)} />
                <Text style={styles.metricLabel}>NDVI</Text>
                <Text style={[styles.metricValue, { color: getNDVIColor(item.ndvi_value) }]}>
                  {item.ndvi_value.toFixed(2)}
                </Text>
              </View>
            </View>

            {/* Status Chips */}
            <View style={styles.chipsContainer}>
              <Chip
                label={item.status === 'active' ? 'نشط' : 'غير نشط'}
                variant="filled"
                color={item.status === 'active' ? 'success' : 'default'}
                size="small"
              />

              {item.health_score >= 80 && (
                <Chip
                  label="صحة ممتازة"
                  variant="outlined"
                  color="success"
                  size="small"
                />
              )}
            </View>
          </View>
        </Card>
      </Animated.View>
    );
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <Icon name="sprout" size={64} color={Theme.colors.primary.main} />
        <Text style={styles.loadingText}>جاري تحميل الحقول...</Text>
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
        <Text style={styles.headerTitle}>حقولي 🌾</Text>
        <Text style={styles.headerSubtitle}>إدارة ومراقبة جميع الحقول الزراعية</Text>

        {/* Search Bar */}
        <View style={styles.searchContainer}>
          <Icon name="magnify" size={20} color={Theme.colors.gray[500]} />
          <TextInput
            style={styles.searchInput}
            placeholder="ابحث عن حقل أو محصول..."
            placeholderTextColor={Theme.colors.gray[500]}
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          {searchQuery.length > 0 && (
            <Pressable onPress={() => setSearchQuery('')}>
              <Icon name="close" size={20} color={Theme.colors.gray[500]} />
            </Pressable>
          )}
        </View>
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
            title="إجمالي الحقول"
            value={stats.total.toString()}
            icon={<Icon name="map-marker-multiple" size={32} color={Theme.colors.primary.main} />}
            color="primary"
            variant="minimal"
            style={styles.statCardSmall}
          />
        </Animated.View>

        <Animated.View entering={FadeInRight.delay(200)}>
          <StatCard
            title="الحقول النشطة"
            value={stats.active.toString()}
            icon={<Icon name="check-circle" size={32} color={Theme.colors.success.main} />}
            color="success"
            variant="minimal"
            style={styles.statCardSmall}
          />
        </Animated.View>

        <Animated.View entering={FadeInRight.delay(300)}>
          <StatCard
            title="صحة ممتازة"
            value={stats.healthy.toString()}
            icon={<Icon name="heart-pulse" size={32} color={Theme.colors.agricultural.crop} />}
            color="success"
            variant="minimal"
            style={styles.statCardSmall}
          />
        </Animated.View>

        <Animated.View entering={FadeInRight.delay(400)}>
          <StatCard
            title="متوسط الصحة"
            value={`${stats.avgHealth.toFixed(0)}%`}
            icon={<Icon name="chart-line" size={32} color={Theme.colors.info.main} />}
            color="info"
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
          label="الكل"
          variant={selectedFilter === 'all' ? 'filled' : 'outlined'}
          color="primary"
          onPress={() => setSelectedFilter('all')}
          selected={selectedFilter === 'all'}
        />
        <Chip
          label="النشطة فقط"
          variant={selectedFilter === 'active' ? 'filled' : 'outlined'}
          color="success"
          onPress={() => setSelectedFilter('active')}
          selected={selectedFilter === 'active'}
        />
        <Chip
          label="الصحية فقط"
          variant={selectedFilter === 'healthy' ? 'filled' : 'outlined'}
          color="success"
          onPress={() => setSelectedFilter('healthy')}
          selected={selectedFilter === 'healthy'}
        />
      </ScrollView>

      {/* Results Count */}
      <View style={styles.resultsHeader}>
        <Text style={styles.resultsText}>
          عرض {filteredFields.length} من {fields.length} حقل
        </Text>
      </View>

      {/* Fields List */}
      {filteredFields.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Icon name="map-marker-off" size={64} color={Theme.colors.gray[400]} />
          <Text style={styles.emptyText}>لا توجد حقول</Text>
          <Text style={styles.emptySubtext}>
            {searchQuery
              ? 'لم يتم العثور على نتائج للبحث'
              : 'أضف حقلك الأول للبدء'}
          </Text>
          {!searchQuery && (
            <Button
              title="إضافة حقل جديد"
              variant="contained"
              color="primary"
              icon={<Icon name="plus" size={20} color="#fff" />}
              onPress={() => alert('سيتم إضافة ميزة إضافة حقل جديد قريباً')}
              style={styles.addButton}
            />
          )}
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
              colors={[Theme.colors.primary.main]}
              tintColor={Theme.colors.primary.main}
            />
          }
        />
      )}

      {/* Floating Action Button */}
      {filteredFields.length > 0 && (
        <Animated.View entering={FadeInDown.delay(500)} style={styles.fabContainer}>
          <Pressable
            style={styles.fab}
            onPress={() => alert('سيتم إضافة ميزة إضافة حقل جديد قريباً')}
          >
            <LinearGradient
              colors={[Theme.colors.primary.main, Theme.colors.primary.dark]}
              style={styles.fabGradient}
            >
              <Icon name="plus" size={28} color="#fff" />
            </LinearGradient>
          </Pressable>
        </Animated.View>
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
    marginBottom: Theme.spacing.lg,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: Theme.borderRadius.xl,
    paddingHorizontal: Theme.spacing.md,
    paddingVertical: Theme.spacing.sm,
    ...Theme.shadows.md,
  },
  searchInput: {
    flex: 1,
    marginLeft: Theme.spacing.sm,
    ...Theme.typography.styles.body1,
    color: Theme.colors.text.primary,
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
    minWidth: 140,
  },
  filterChipsContainer: {
    paddingHorizontal: Theme.spacing.md,
    gap: Theme.spacing.sm,
    paddingVertical: Theme.spacing.sm,
  },
  resultsHeader: {
    paddingHorizontal: Theme.spacing.md,
    paddingVertical: Theme.spacing.sm,
  },
  resultsText: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.text.secondary,
  },
  list: {
    padding: Theme.spacing.md,
    paddingBottom: 100,
  },
  fieldCard: {
    marginBottom: Theme.spacing.md,
    overflow: 'hidden',
  },
  fieldCardHeader: {
    padding: Theme.spacing.md,
  },
  fieldHeaderContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  fieldTitleContainer: {
    flex: 1,
  },
  fieldName: {
    ...Theme.typography.styles.h3,
    color: '#fff',
    marginBottom: Theme.spacing.xs,
  },
  cropTypeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.xs,
  },
  cropType: {
    ...Theme.typography.styles.body2,
    color: 'rgba(255,255,255,0.9)',
  },
  healthIconContainer: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: Theme.borderRadius.full,
    padding: Theme.spacing.sm,
  },
  fieldCardBody: {
    padding: Theme.spacing.md,
    backgroundColor: '#fff',
  },
  metricsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: Theme.spacing.md,
  },
  metricItem: {
    alignItems: 'center',
    gap: Theme.spacing.xs,
    flex: 1,
  },
  metricLabel: {
    ...Theme.typography.styles.caption,
    color: Theme.colors.text.secondary,
  },
  metricValue: {
    ...Theme.typography.styles.body1,
    fontWeight: '600',
    color: Theme.colors.text.primary,
  },
  chipsContainer: {
    flexDirection: 'row',
    gap: Theme.spacing.sm,
    flexWrap: 'wrap',
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
    marginBottom: Theme.spacing.lg,
  },
  addButton: {
    marginTop: Theme.spacing.md,
  },
  fabContainer: {
    position: 'absolute',
    right: Theme.spacing.lg,
    bottom: Theme.spacing.lg,
  },
  fab: {
    ...Theme.shadows.xl,
  },
  fabGradient: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
