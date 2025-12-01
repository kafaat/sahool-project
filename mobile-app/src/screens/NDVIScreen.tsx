import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Dimensions,
  Image
} from 'react-native';
import {
  Text,
  Card,
  SegmentedButtons,
  ActivityIndicator,
  useTheme,
  Chip
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { LineChart } from 'react-native-chart-kit';
import { getNDVIData, getNDVIHistory } from '../services/api';

export default function NDVIScreen() {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30d');
  const [ndviData, setNdviData] = useState({
    current: 0.65,
    average: 0.58,
    trend: 'increasing',
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
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Mock data
      const mockHistory = generateMockHistory(timeRange);
      setHistoryData(mockHistory);
      setNdviData({
        current: mockHistory.values[mockHistory.values.length - 1],
        average: mockHistory.values.reduce((a, b) => a + b, 0) / mockHistory.values.length,
        trend: mockHistory.values[mockHistory.values.length - 1] > mockHistory.values[0] ? 'increasing' : 'decreasing',
        lastUpdate: new Date().toISOString(),
      });
    } catch (error) {
      console.error('Error loading NDVI data:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateMockHistory = (range: string) => {
    const points = range === '7d' ? 7 : range === '30d' ? 15 : 30;
    const labels: string[] = [];
    const values: number[] = [];

    for (let i = points - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i * (range === '7d' ? 1 : range === '30d' ? 2 : 3));
      labels.push(
        `${date.getDate()}/${date.getMonth() + 1}`
      );
      values.push(0.3 + Math.random() * 0.4);
    }

    return { labels, values };
  };

  const getNDVICategory = (value: number) => {
    if (value >= 0.6) return { label: 'ممتاز', color: '#4CAF50', icon: 'check-circle' };
    if (value >= 0.4) return { label: 'جيد', color: '#8BC34A', icon: 'check' };
    if (value >= 0.2) return { label: 'متوسط', color: '#FFC107', icon: 'alert' };
    return { label: 'ضعيف', color: '#F44336', icon: 'close-circle' };
  };

  const currentCategory = getNDVICategory(ndviData.current);

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={styles.loadingText}>جاري تحميل بيانات NDVI...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {/* Current NDVI Card */}
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            القيمة الحالية
          </Text>

          <View style={styles.currentValue}>
            <View style={styles.ndviCircle}>
              <Icon name={currentCategory.icon} size={48} color={currentCategory.color} />
              <Text variant="displaySmall" style={[styles.ndviNumber, { color: currentCategory.color }]}>
                {ndviData.current.toFixed(2)}
              </Text>
              <Chip
                mode="flat"
                style={[styles.categoryChip, { backgroundColor: currentCategory.color }]}
                textStyle={{ color: 'white', fontSize: 12 }}
              >
                {currentCategory.label}
              </Chip>
            </View>
          </View>

          <View style={styles.stats}>
            <View style={styles.statItem}>
              <Icon name="chart-line" size={20} color="#666" />
              <Text variant="bodySmall" style={styles.statLabel}>
                المتوسط
              </Text>
              <Text variant="titleMedium" style={styles.statValue}>
                {ndviData.average.toFixed(2)}
              </Text>
            </View>

            <View style={styles.statItem}>
              <Icon
                name={ndviData.trend === 'increasing' ? 'trending-up' : 'trending-down'}
                size={20}
                color={ndviData.trend === 'increasing' ? '#4CAF50' : '#F44336'}
              />
              <Text variant="bodySmall" style={styles.statLabel}>
                الاتجاه
              </Text>
              <Text
                variant="titleMedium"
                style={[
                  styles.statValue,
                  { color: ndviData.trend === 'increasing' ? '#4CAF50' : '#F44336' }
                ]}
              >
                {ndviData.trend === 'increasing' ? 'تصاعدي' : 'تنازلي'}
              </Text>
            </View>

            <View style={styles.statItem}>
              <Icon name="clock-outline" size={20} color="#666" />
              <Text variant="bodySmall" style={styles.statLabel}>
                آخر تحديث
              </Text>
              <Text variant="bodySmall" style={styles.statValue}>
                {new Date(ndviData.lastUpdate).toLocaleDateString('ar-SA', {
                  month: 'short',
                  day: 'numeric',
                })}
              </Text>
            </View>
          </View>
        </Card.Content>
      </Card>

      {/* Time Range Selector */}
      <View style={styles.timeRangeContainer}>
        <SegmentedButtons
          value={timeRange}
          onValueChange={setTimeRange}
          buttons={[
            { value: '7d', label: '7 أيام' },
            { value: '30d', label: '30 يوم' },
            { value: '90d', label: '90 يوم' },
          ]}
        />
      </View>

      {/* History Chart */}
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            تاريخ NDVI
          </Text>

          <LineChart
            data={{
              labels: historyData.labels,
              datasets: [
                {
                  data: historyData.values,
                  color: (opacity = 1) => `rgba(76, 175, 80, ${opacity})`,
                  strokeWidth: 2,
                },
              ],
            }}
            width={Dimensions.get('window').width - 64}
            height={220}
            chartConfig={{
              backgroundColor: '#ffffff',
              backgroundGradientFrom: '#ffffff',
              backgroundGradientTo: '#ffffff',
              decimalPlaces: 2,
              color: (opacity = 1) => `rgba(46, 125, 50, ${opacity})`,
              labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
              style: {
                borderRadius: 16,
              },
              propsForDots: {
                r: '4',
                strokeWidth: '2',
                stroke: '#2E7D32',
              },
            }}
            bezier
            style={styles.chart}
          />
        </Card.Content>
      </Card>

      {/* NDVI Guide */}
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            دليل قراءة NDVI
          </Text>

          <View style={styles.guide}>
            <View style={styles.guideItem}>
              <View style={[styles.guideDot, { backgroundColor: '#4CAF50' }]} />
              <View style={styles.guideContent}>
                <Text variant="bodyMedium" style={styles.guideTitle}>
                  0.6 - 0.9 (ممتاز)
                </Text>
                <Text variant="bodySmall" style={styles.guideText}>
                  نباتات صحية وكثيفة مع غطاء نباتي قوي
                </Text>
              </View>
            </View>

            <View style={styles.guideItem}>
              <View style={[styles.guideDot, { backgroundColor: '#8BC34A' }]} />
              <View style={styles.guideContent}>
                <Text variant="bodyMedium" style={styles.guideTitle}>
                  0.4 - 0.6 (جيد)
                </Text>
                <Text variant="bodySmall" style={styles.guideText}>
                  نباتات في حالة جيدة مع نمو طبيعي
                </Text>
              </View>
            </View>

            <View style={styles.guideItem}>
              <View style={[styles.guideDot, { backgroundColor: '#FFC107' }]} />
              <View style={styles.guideContent}>
                <Text variant="bodyMedium" style={styles.guideTitle}>
                  0.2 - 0.4 (متوسط)
                </Text>
                <Text variant="bodySmall" style={styles.guideText}>
                  نباتات متوسطة قد تحتاج إلى عناية
                </Text>
              </View>
            </View>

            <View style={styles.guideItem}>
              <View style={[styles.guideDot, { backgroundColor: '#F44336' }]} />
              <View style={styles.guideContent}>
                <Text variant="bodyMedium" style={styles.guideTitle}>
                  أقل من 0.2 (ضعيف)
                </Text>
                <Text variant="bodySmall" style={styles.guideText}>
                  نباتات ضعيفة أو تربة عارية تحتاج تدخل
                </Text>
              </View>
            </View>
          </View>
        </Card.Content>
      </Card>

      {/* Satellite Images Preview */}
      <Card style={[styles.card, { marginBottom: 24 }]}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            صور الأقمار الصناعية
          </Text>

          <Text variant="bodySmall" style={styles.comingSoon}>
            سيتم إضافة معرض صور NDVI من الأقمار الصناعية قريباً
          </Text>

          <View style={styles.imagePlaceholder}>
            <Icon name="satellite-variant" size={48} color="#ccc" />
            <Text style={styles.placeholderText}>Sentinel-2 Images</Text>
          </View>
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
  card: {
    margin: 16,
    marginBottom: 0,
    elevation: 2,
    borderRadius: 12,
  },
  sectionTitle: {
    fontWeight: 'bold',
    marginBottom: 16,
  },
  currentValue: {
    alignItems: 'center',
    marginVertical: 20,
  },
  ndviCircle: {
    alignItems: 'center',
    gap: 8,
  },
  ndviNumber: {
    fontWeight: 'bold',
  },
  categoryChip: {
    marginTop: 8,
  },
  stats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 20,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  statItem: {
    alignItems: 'center',
    gap: 4,
  },
  statLabel: {
    color: '#666',
  },
  statValue: {
    fontWeight: '500',
  },
  timeRangeContainer: {
    padding: 16,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  guide: {
    gap: 12,
  },
  guideItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  guideDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginTop: 4,
  },
  guideContent: {
    flex: 1,
  },
  guideTitle: {
    fontWeight: '500',
    marginBottom: 2,
  },
  guideText: {
    color: '#666',
    lineHeight: 18,
  },
  comingSoon: {
    color: '#999',
    marginBottom: 12,
    fontStyle: 'italic',
  },
  imagePlaceholder: {
    height: 150,
    backgroundColor: '#f9f9f9',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#eee',
    borderStyle: 'dashed',
  },
  placeholderText: {
    marginTop: 8,
    color: '#999',
  },
});
