/**
 * Improved NDVI Screen
 * شاشة NDVI المحسّنة
 *
 * Features:
 * - Enhanced visual design with gradients
 * - Better NDVI visualization
 * - Improved charts and statistics
 * - Agricultural color coding
 * - Smooth animations
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Dimensions,
  Pressable,
} from 'react-native';
import { Text } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import Animated, { FadeInDown, FadeInUp } from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import { LineChart } from 'react-native-chart-kit';

import { Card, Chip, ProgressBar, StatCard } from '../components/ui';
import { Theme } from '../theme/design-system';
import { getNDVIData, getNDVIHistory } from '../services/api';

const SCREEN_WIDTH = Dimensions.get('window').width;

export default function ImprovedNDVIScreen() {
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');
  const [ndviData, setNdviData] = useState({
    current: 0.65,
    average: 0.58,
    min: 0.42,
    max: 0.78,
    trend: 'increasing' as 'increasing' | 'decreasing',
    lastUpdate: new Date().toISOString(),
  });
  const [historyData, setHistoryData] = useState({
    labels: [] as string[],
    values: [] as number[],
  });

  useEffect(() => {
    loadNDVIData();
  }, [timeRange]);

  const loadNDVIData = async () => {
    setLoading(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const mockHistory = generateMockHistory(timeRange);
      setHistoryData(mockHistory);

      const values = mockHistory.values;
      setNdviData({
        current: values[values.length - 1],
        average: values.reduce((a, b) => a + b, 0) / values.length,
        min: Math.min(...values),
        max: Math.max(...values),
        trend: values[values.length - 1] > values[0] ? 'increasing' : 'decreasing',
        lastUpdate: new Date().toISOString(),
      });
    } catch (error) {
      console.error('Error loading NDVI data:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateMockHistory = (range: '7d' | '30d' | '90d') => {
    const points = range === '7d' ? 7 : range === '30d' ? 15 : 30;
    const labels: string[] = [];
    const values: number[] = [];

    for (let i = points - 1; i >= 0; i--) {
      const date = new Date();
      const daysAgo = i * (range === '7d' ? 1 : range === '30d' ? 2 : 3);
      date.setDate(date.getDate() - daysAgo);
      labels.push(`${date.getDate()}/${date.getMonth() + 1}`);
      values.push(0.3 + Math.random() * 0.4 + (points - i) * 0.01);
    }

    return { labels, values };
  };

  const getNDVICategory = (value: number) => {
    if (value >= 0.6) {
      return {
        label: 'ممتاز',
        color: Theme.colors.agricultural.ndvi.excellent,
        icon: 'check-circle',
        description: 'نباتات صحية وكثيفة مع غطاء نباتي قوي',
      };
    }
    if (value >= 0.4) {
      return {
        label: 'جيد',
        color: Theme.colors.agricultural.ndvi.good,
        icon: 'checkbox-marked-circle-outline',
        description: 'نباتات في حالة جيدة مع نمو طبيعي',
      };
    }
    if (value >= 0.2) {
      return {
        label: 'متوسط',
        color: Theme.colors.agricultural.ndvi.moderate,
        icon: 'alert-circle-outline',
        description: 'نباتات متوسطة قد تحتاج إلى عناية',
      };
    }
    return {
      label: 'ضعيف',
      color: Theme.colors.agricultural.ndvi.poor,
      icon: 'close-circle',
      description: 'نباتات ضعيفة أو تربة عارية تحتاج تدخل',
    };
  };

  const currentCategory = getNDVICategory(ndviData.current);

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <Icon name="image-filter-hdr" size={64} color={Theme.colors.primary.main} />
        <Text style={styles.loadingText}>جاري تحميل بيانات NDVI...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {/* Hero Section with Current NDVI */}
      <Animated.View entering={FadeInDown.delay(100)}>
        <LinearGradient
          colors={[currentCategory.color, currentCategory.color + '80']}
          style={styles.heroSection}
        >
          <Icon name="satellite-variant" size={40} color="rgba(255,255,255,0.5)" />

          <Text style={styles.heroTitle}>قيمة NDVI الحالية</Text>

          <View style={styles.ndviValueContainer}>
            <Icon name={currentCategory.icon} size={56} color="#fff" />
            <Text style={styles.ndviValue}>{ndviData.current.toFixed(2)}</Text>
          </View>

          <View style={styles.ndviCategoryBadge}>
            <Text style={styles.ndviCategoryText}>{currentCategory.label}</Text>
          </View>

          <Text style={styles.ndviDescription}>{currentCategory.description}</Text>

          <View style={styles.lastUpdateContainer}>
            <Icon name="clock-outline" size={14} color="rgba(255,255,255,0.8)" />
            <Text style={styles.lastUpdateText}>
              آخر تحديث: {new Date(ndviData.lastUpdate).toLocaleDateString('ar-SA')}
            </Text>
          </View>
        </LinearGradient>
      </Animated.View>

      {/* Quick Stats */}
      <View style={styles.quickStatsContainer}>
        <Animated.View entering={FadeInDown.delay(200)} style={styles.quickStatItem}>
          <StatCard
            title="المتوسط"
            value={ndviData.average.toFixed(2)}
            icon={<Icon name="chart-line" size={28} color={Theme.colors.info.main} />}
            color="info"
            variant="minimal"
          />
        </Animated.View>

        <Animated.View entering={FadeInDown.delay(300)} style={styles.quickStatItem}>
          <StatCard
            title="الحد الأقصى"
            value={ndviData.max.toFixed(2)}
            icon={<Icon name="arrow-up-bold" size={28} color={Theme.colors.success.main} />}
            color="success"
            variant="minimal"
            trend={{ value: 15, isPositive: true }}
          />
        </Animated.View>

        <Animated.View entering={FadeInDown.delay(400)} style={styles.quickStatItem}>
          <StatCard
            title="الحد الأدنى"
            value={ndviData.min.toFixed(2)}
            icon={<Icon name="arrow-down-bold" size={28} color={Theme.colors.error.main} />}
            color="error"
            variant="minimal"
          />
        </Animated.View>
      </View>

      {/* Trend Indicator */}
      <Animated.View entering={FadeInDown.delay(500)}>
        <Card elevation="sm" rounded="lg" style={styles.trendCard}>
          <View style={styles.trendContainer}>
            <Icon
              name={ndviData.trend === 'increasing' ? 'trending-up' : 'trending-down'}
              size={32}
              color={
                ndviData.trend === 'increasing'
                  ? Theme.colors.success.main
                  : Theme.colors.error.main
              }
            />
            <View style={styles.trendTextContainer}>
              <Text style={styles.trendLabel}>الاتجاه</Text>
              <Text
                style={[
                  styles.trendValue,
                  {
                    color:
                      ndviData.trend === 'increasing'
                        ? Theme.colors.success.main
                        : Theme.colors.error.main,
                  },
                ]}
              >
                {ndviData.trend === 'increasing' ? 'تصاعدي ↑' : 'تنازلي ↓'}
              </Text>
            </View>
            <Chip
              label={ndviData.trend === 'increasing' ? 'إيجابي' : 'سلبي'}
              variant="filled"
              color={ndviData.trend === 'increasing' ? 'success' : 'error'}
              size="small"
            />
          </View>
        </Card>
      </Animated.View>

      {/* Time Range Selector */}
      <Animated.View entering={FadeInDown.delay(600)}>
        <View style={styles.timeRangeContainer}>
          <Text style={styles.sectionTitle}>الفترة الزمنية</Text>
          <View style={styles.timeRangeButtons}>
            {(['7d', '30d', '90d'] as const).map((range) => (
              <Pressable
                key={range}
                onPress={() => setTimeRange(range)}
                style={styles.timeRangeButton}
              >
                <LinearGradient
                  colors={
                    timeRange === range
                      ? [Theme.colors.primary.main, Theme.colors.primary.dark]
                      : ['#fff', '#fff']
                  }
                  style={[
                    styles.timeRangeButtonGradient,
                    timeRange !== range && styles.timeRangeButtonOutline,
                  ]}
                >
                  <Text
                    style={[
                      styles.timeRangeButtonText,
                      { color: timeRange === range ? '#fff' : Theme.colors.text.primary },
                    ]}
                  >
                    {range === '7d' ? '7 أيام' : range === '30d' ? '30 يوم' : '90 يوم'}
                  </Text>
                </LinearGradient>
              </Pressable>
            ))}
          </View>
        </View>
      </Animated.View>

      {/* History Chart */}
      <Animated.View entering={FadeInDown.delay(700)}>
        <Card elevation="md" rounded="lg" style={styles.chartCard}>
          <Text style={styles.chartTitle}>تاريخ NDVI</Text>

          <LineChart
            data={{
              labels: historyData.labels,
              datasets: [
                {
                  data: historyData.values,
                  color: (opacity = 1) => Theme.colors.agricultural.crop,
                  strokeWidth: 3,
                },
              ],
            }}
            width={SCREEN_WIDTH - 64}
            height={240}
            chartConfig={{
              backgroundColor: '#fff',
              backgroundGradientFrom: '#fff',
              backgroundGradientTo: '#fff',
              decimalPlaces: 2,
              color: (opacity = 1) => `rgba(102, 187, 106, ${opacity})`,
              labelColor: (opacity = 1) => Theme.colors.text.secondary,
              style: {
                borderRadius: Theme.borderRadius.lg,
              },
              propsForDots: {
                r: '5',
                strokeWidth: '2',
                stroke: Theme.colors.agricultural.crop,
                fill: '#fff',
              },
              propsForBackgroundLines: {
                strokeDasharray: '',
                stroke: Theme.colors.gray[200],
              },
            }}
            bezier
            style={styles.chart}
          />
        </Card>
      </Animated.View>

      {/* NDVI Guide */}
      <Animated.View entering={FadeInDown.delay(800)}>
        <Card elevation="md" rounded="lg" style={styles.guideCard}>
          <Text style={styles.guideTitle}>دليل قراءة NDVI</Text>
          <Text style={styles.guideSubtitle}>
            فهم قيم مؤشر الغطاء النباتي NDVI
          </Text>

          <View style={styles.guideItems}>
            {[
              {
                range: '0.6 - 0.9',
                label: 'ممتاز',
                color: Theme.colors.agricultural.ndvi.excellent,
                description: 'نباتات صحية وكثيفة مع غطاء نباتي قوي',
                percentage: 85,
              },
              {
                range: '0.4 - 0.6',
                label: 'جيد',
                color: Theme.colors.agricultural.ndvi.good,
                description: 'نباتات في حالة جيدة مع نمو طبيعي',
                percentage: 65,
              },
              {
                range: '0.2 - 0.4',
                label: 'متوسط',
                color: Theme.colors.agricultural.ndvi.moderate,
                description: 'نباتات متوسطة قد تحتاج إلى عناية',
                percentage: 45,
              },
              {
                range: '< 0.2',
                label: 'ضعيف',
                color: Theme.colors.agricultural.ndvi.poor,
                description: 'نباتات ضعيفة أو تربة عارية تحتاج تدخل',
                percentage: 25,
              },
            ].map((item, index) => (
              <View key={index} style={styles.guideItem}>
                <View style={styles.guideItemHeader}>
                  <View style={[styles.guideDot, { backgroundColor: item.color }]} />
                  <View style={styles.guideItemContent}>
                    <View style={styles.guideItemTitleRow}>
                      <Text style={styles.guideItemRange}>{item.range}</Text>
                      <Chip
                        label={item.label}
                        variant="filled"
                        size="small"
                        style={{ backgroundColor: item.color }}
                      />
                    </View>
                    <Text style={styles.guideItemDescription}>{item.description}</Text>
                  </View>
                </View>
                <ProgressBar
                  progress={item.percentage}
                  color={item.color}
                  height={6}
                  style={styles.guideProgress}
                />
              </View>
            ))}
          </View>
        </Card>
      </Animated.View>

      {/* Satellite Images Placeholder */}
      <Animated.View entering={FadeInUp.delay(900)}>
        <Card elevation="sm" rounded="lg" style={styles.satelliteCard}>
          <Text style={styles.satelliteTitle}>صور الأقمار الصناعية</Text>
          <Text style={styles.satelliteSubtitle}>
            صور NDVI من Sentinel-2
          </Text>

          <View style={styles.satellitePlaceholder}>
            <Icon name="satellite-variant" size={56} color={Theme.colors.gray[300]} />
            <Text style={styles.satellitePlaceholderText}>قريباً</Text>
            <Text style={styles.satellitePlaceholderSubtext}>
              سيتم إضافة معرض صور NDVI التفاعلية
            </Text>
          </View>
        </Card>
      </Animated.View>

      <View style={{ height: Theme.spacing.xl }} />
    </ScrollView>
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
  heroSection: {
    padding: Theme.spacing.xl,
    paddingTop: Theme.spacing['2xl'],
    paddingBottom: Theme.spacing['3xl'],
    alignItems: 'center',
    borderBottomLeftRadius: Theme.borderRadius['3xl'],
    borderBottomRightRadius: Theme.borderRadius['3xl'],
  },
  heroTitle: {
    ...Theme.typography.styles.body1,
    color: 'rgba(255,255,255,0.9)',
    marginTop: Theme.spacing.md,
    marginBottom: Theme.spacing.lg,
  },
  ndviValueContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.md,
    marginBottom: Theme.spacing.md,
  },
  ndviValue: {
    fontSize: 56,
    fontWeight: '700',
    color: '#fff',
  },
  ndviCategoryBadge: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: Theme.spacing.lg,
    paddingVertical: Theme.spacing.sm,
    borderRadius: Theme.borderRadius.full,
    marginBottom: Theme.spacing.md,
  },
  ndviCategoryText: {
    ...Theme.typography.styles.h3,
    color: '#fff',
  },
  ndviDescription: {
    ...Theme.typography.styles.body2,
    color: 'rgba(255,255,255,0.9)',
    textAlign: 'center',
    maxWidth: '80%',
  },
  lastUpdateContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.xs,
    marginTop: Theme.spacing.md,
  },
  lastUpdateText: {
    ...Theme.typography.styles.caption,
    color: 'rgba(255,255,255,0.8)',
  },
  quickStatsContainer: {
    flexDirection: 'row',
    padding: Theme.spacing.md,
    gap: Theme.spacing.sm,
    marginTop: -Theme.spacing.xl,
  },
  quickStatItem: {
    flex: 1,
  },
  trendCard: {
    marginHorizontal: Theme.spacing.md,
    marginBottom: Theme.spacing.md,
    padding: Theme.spacing.md,
  },
  trendContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.md,
  },
  trendTextContainer: {
    flex: 1,
  },
  trendLabel: {
    ...Theme.typography.styles.caption,
    color: Theme.colors.text.secondary,
  },
  trendValue: {
    ...Theme.typography.styles.h3,
    fontWeight: '600',
  },
  timeRangeContainer: {
    padding: Theme.spacing.md,
  },
  sectionTitle: {
    ...Theme.typography.styles.h3,
    color: Theme.colors.text.primary,
    marginBottom: Theme.spacing.md,
  },
  timeRangeButtons: {
    flexDirection: 'row',
    gap: Theme.spacing.sm,
  },
  timeRangeButton: {
    flex: 1,
  },
  timeRangeButtonGradient: {
    paddingVertical: Theme.spacing.md,
    borderRadius: Theme.borderRadius.lg,
    alignItems: 'center',
  },
  timeRangeButtonOutline: {
    borderWidth: 1,
    borderColor: Theme.colors.gray[300],
  },
  timeRangeButtonText: {
    ...Theme.typography.styles.body1,
    fontWeight: '600',
  },
  chartCard: {
    marginHorizontal: Theme.spacing.md,
    marginBottom: Theme.spacing.md,
    padding: Theme.spacing.md,
  },
  chartTitle: {
    ...Theme.typography.styles.h3,
    color: Theme.colors.text.primary,
    marginBottom: Theme.spacing.md,
  },
  chart: {
    marginVertical: Theme.spacing.sm,
    borderRadius: Theme.borderRadius.lg,
  },
  guideCard: {
    marginHorizontal: Theme.spacing.md,
    marginBottom: Theme.spacing.md,
    padding: Theme.spacing.md,
  },
  guideTitle: {
    ...Theme.typography.styles.h3,
    color: Theme.colors.text.primary,
    marginBottom: Theme.spacing.xs,
  },
  guideSubtitle: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.text.secondary,
    marginBottom: Theme.spacing.lg,
  },
  guideItems: {
    gap: Theme.spacing.md,
  },
  guideItem: {
    gap: Theme.spacing.sm,
  },
  guideItemHeader: {
    flexDirection: 'row',
    gap: Theme.spacing.md,
  },
  guideDot: {
    width: 16,
    height: 16,
    borderRadius: 8,
    marginTop: 4,
  },
  guideItemContent: {
    flex: 1,
  },
  guideItemTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Theme.spacing.xs,
  },
  guideItemRange: {
    ...Theme.typography.styles.body1,
    fontWeight: '600',
    color: Theme.colors.text.primary,
  },
  guideItemDescription: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.text.secondary,
    lineHeight: 20,
  },
  guideProgress: {
    marginLeft: 30,
  },
  satelliteCard: {
    marginHorizontal: Theme.spacing.md,
    marginBottom: Theme.spacing.md,
    padding: Theme.spacing.md,
  },
  satelliteTitle: {
    ...Theme.typography.styles.h3,
    color: Theme.colors.text.primary,
    marginBottom: Theme.spacing.xs,
  },
  satelliteSubtitle: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.text.secondary,
    marginBottom: Theme.spacing.lg,
  },
  satellitePlaceholder: {
    height: 200,
    backgroundColor: Theme.colors.gray[50],
    borderRadius: Theme.borderRadius.lg,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: Theme.colors.gray[200],
    borderStyle: 'dashed',
  },
  satellitePlaceholderText: {
    ...Theme.typography.styles.h3,
    color: Theme.colors.text.disabled,
    marginTop: Theme.spacing.sm,
  },
  satellitePlaceholderSubtext: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.text.disabled,
    marginTop: Theme.spacing.xs,
  },
});
