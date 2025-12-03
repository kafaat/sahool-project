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
  SegmentedButtons,
  List,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { LineChart, BarChart } from 'react-native-chart-kit';
import { apiService } from '../services/api';

interface NDVIData {
  fieldId: number;
  fieldName: string;
  currentValue: number;
  trend: 'up' | 'down' | 'stable';
  classification: string;
  history: Array<{ date: string; value: number }>;
  analysis?: {
    health_status: string;
    vegetation_density: string;
    recommendations: string[];
  };
}

interface FieldSummary {
  id: number;
  name: string;
  ndvi: number;
  status: string;
}

export default function NDVIScreen({ navigation, route }: any) {
  const preselectedFieldId = route?.params?.fieldId;
  const [fields, setFields] = useState<FieldSummary[]>([]);
  const [selectedField, setSelectedField] = useState<number | null>(preselectedFieldId || null);
  const [ndviData, setNdviData] = useState<NDVIData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [timeRange, setTimeRange] = useState('7d');

  const fetchFields = async () => {
    try {
      const response = await apiService.getFields();
      const fieldSummaries = response.data.map((f: any) => ({
        id: f.id,
        name: f.name,
        ndvi: f.ndvi_current,
        status: f.status,
      }));
      setFields(fieldSummaries);
      if (!selectedField && fieldSummaries.length > 0) {
        setSelectedField(fieldSummaries[0].id);
      }
    } catch (error) {
      console.error('Error fetching fields:', error);
    }
  };

  const fetchNDVIData = async () => {
    if (!selectedField) return;

    try {
      const [ndviResponse, analysisResponse] = await Promise.all([
        apiService.getNDVIHistory(selectedField),
        apiService.getNDVIAnalysis(selectedField).catch(() => null),
      ]);

      const field = fields.find((f) => f.id === selectedField);
      const history = ndviResponse.data || [];

      setNdviData({
        fieldId: selectedField,
        fieldName: field?.name || 'حقل',
        currentValue: history[history.length - 1]?.value || field?.ndvi || 0,
        trend: calculateTrend(history),
        classification: classifyNDVI(history[history.length - 1]?.value || 0),
        history,
        analysis: analysisResponse?.data,
      });
    } catch (error) {
      console.error('Error fetching NDVI data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchFields();
  }, []);

  useEffect(() => {
    if (selectedField) {
      setLoading(true);
      fetchNDVIData();
    }
  }, [selectedField]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchNDVIData();
  };

  const calculateTrend = (history: Array<{ value: number }>): 'up' | 'down' | 'stable' => {
    if (history.length < 2) return 'stable';
    const recent = history.slice(-3);
    const avg = recent.reduce((a, b) => a + b.value, 0) / recent.length;
    const older = history.slice(-6, -3);
    if (older.length === 0) return 'stable';
    const oldAvg = older.reduce((a, b) => a + b.value, 0) / older.length;
    if (avg > oldAvg + 0.05) return 'up';
    if (avg < oldAvg - 0.05) return 'down';
    return 'stable';
  };

  const classifyNDVI = (value: number): string => {
    if (value >= 0.7) return 'نباتات كثيفة';
    if (value >= 0.5) return 'نباتات صحية';
    if (value >= 0.3) return 'نباتات معتدلة';
    if (value >= 0.1) return 'نباتات ضعيفة';
    return 'تربة عارية';
  };

  const getNDVIColor = (value: number): string => {
    if (value >= 0.7) return '#1B5E20';
    if (value >= 0.5) return '#4CAF50';
    if (value >= 0.3) return '#8BC34A';
    if (value >= 0.1) return '#CDDC39';
    return '#FFC107';
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return 'trending-up';
      case 'down': return 'trending-down';
      default: return 'trending-neutral';
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'up': return '#4CAF50';
      case 'down': return '#F44336';
      default: return '#9E9E9E';
    }
  };

  if (loading && fields.length === 0) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2E7D32" />
        <Paragraph style={styles.loadingText}>جاري تحميل بيانات NDVI...</Paragraph>
      </View>
    );
  }

  const chartData = ndviData?.history?.slice(-7) || [];
  const lineChartData = {
    labels: chartData.map((h) => h.date.slice(5, 10)),
    datasets: [
      {
        data: chartData.length > 0 ? chartData.map((h) => h.value) : [0],
        color: () => '#4CAF50',
        strokeWidth: 3,
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
      {/* Field Selector */}
      <Card style={styles.selectorCard}>
        <Card.Content>
          <Title style={styles.sectionTitle}>اختر الحقل</Title>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.fieldChips}>
              {fields.map((field) => (
                <Chip
                  key={field.id}
                  selected={selectedField === field.id}
                  onPress={() => setSelectedField(field.id)}
                  style={[
                    styles.fieldChip,
                    selectedField === field.id && styles.selectedFieldChip,
                  ]}
                  textStyle={selectedField === field.id ? styles.selectedChipText : undefined}
                >
                  {field.name}
                </Chip>
              ))}
            </View>
          </ScrollView>
        </Card.Content>
      </Card>

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#2E7D32" />
        </View>
      ) : ndviData ? (
        <>
          {/* Current NDVI Value */}
          <Card style={styles.currentValueCard}>
            <Card.Content>
              <View style={styles.currentValueContainer}>
                <View style={styles.valueSection}>
                  <Paragraph style={styles.valueLabel}>قيمة NDVI الحالية</Paragraph>
                  <Title
                    style={[
                      styles.currentValue,
                      { color: getNDVIColor(ndviData.currentValue) },
                    ]}
                  >
                    {ndviData.currentValue.toFixed(3)}
                  </Title>
                  <Chip
                    style={[
                      styles.classificationChip,
                      { backgroundColor: getNDVIColor(ndviData.currentValue) },
                    ]}
                    textStyle={styles.classificationText}
                  >
                    {ndviData.classification}
                  </Chip>
                </View>
                <View style={styles.trendSection}>
                  <Icon
                    name={getTrendIcon(ndviData.trend)}
                    size={50}
                    color={getTrendColor(ndviData.trend)}
                  />
                  <Paragraph style={{ color: getTrendColor(ndviData.trend) }}>
                    {ndviData.trend === 'up'
                      ? 'تحسن'
                      : ndviData.trend === 'down'
                      ? 'تراجع'
                      : 'مستقر'}
                  </Paragraph>
                </View>
              </View>
            </Card.Content>
          </Card>

          {/* NDVI Scale */}
          <Card style={styles.scaleCard}>
            <Card.Content>
              <Title style={styles.sectionTitle}>مقياس NDVI</Title>
              <View style={styles.scaleContainer}>
                {[
                  { range: '0.7-1.0', label: 'كثيف', color: '#1B5E20' },
                  { range: '0.5-0.7', label: 'صحي', color: '#4CAF50' },
                  { range: '0.3-0.5', label: 'معتدل', color: '#8BC34A' },
                  { range: '0.1-0.3', label: 'ضعيف', color: '#CDDC39' },
                  { range: '0.0-0.1', label: 'عاري', color: '#FFC107' },
                ].map((item, index) => (
                  <View key={index} style={styles.scaleItem}>
                    <View style={[styles.scaleColor, { backgroundColor: item.color }]} />
                    <Paragraph style={styles.scaleLabel}>{item.label}</Paragraph>
                    <Paragraph style={styles.scaleRange}>{item.range}</Paragraph>
                  </View>
                ))}
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
                { value: '90d', label: '3 أشهر' },
              ]}
            />
          </View>

          {/* History Chart */}
          {chartData.length > 0 && (
            <Card style={styles.chartCard}>
              <Card.Content>
                <Title style={styles.sectionTitle}>السجل التاريخي</Title>
                <LineChart
                  data={lineChartData}
                  width={Dimensions.get('window').width - 50}
                  height={220}
                  chartConfig={{
                    backgroundColor: '#FFF',
                    backgroundGradientFrom: '#FFF',
                    backgroundGradientTo: '#FFF',
                    decimalPlaces: 2,
                    color: (opacity = 1) => `rgba(76, 175, 80, ${opacity})`,
                    labelColor: () => '#666',
                    style: { borderRadius: 16 },
                    propsForDots: {
                      r: '5',
                      strokeWidth: '2',
                      stroke: '#2E7D32',
                    },
                  }}
                  bezier
                  style={styles.chart}
                />
              </Card.Content>
            </Card>
          )}

          {/* AI Analysis */}
          {ndviData.analysis && (
            <Card style={styles.analysisCard}>
              <Card.Content>
                <View style={styles.analysisHeader}>
                  <Icon name="robot" size={24} color="#9C27B0" />
                  <Title style={styles.analysisTitle}>تحليل الذكاء الاصطناعي</Title>
                </View>

                <List.Item
                  title="حالة الصحة"
                  description={ndviData.analysis.health_status}
                  left={(props) => <List.Icon {...props} icon="heart-pulse" color="#F44336" />}
                />
                <List.Item
                  title="كثافة الغطاء النباتي"
                  description={ndviData.analysis.vegetation_density}
                  left={(props) => <List.Icon {...props} icon="tree" color="#4CAF50" />}
                />

                {ndviData.analysis.recommendations?.length > 0 && (
                  <>
                    <Paragraph style={styles.recommendationsTitle}>التوصيات:</Paragraph>
                    {ndviData.analysis.recommendations.map((rec, index) => (
                      <View key={index} style={styles.recommendationItem}>
                        <Icon name="lightbulb-on" size={18} color="#FFA726" />
                        <Paragraph style={styles.recommendationText}>{rec}</Paragraph>
                      </View>
                    ))}
                  </>
                )}
              </Card.Content>
            </Card>
          )}

          {/* Action Buttons */}
          <View style={styles.actionsContainer}>
            <Button
              mode="contained"
              icon="download"
              onPress={() => {/* Download report */}}
              style={styles.actionButton}
            >
              تحميل التقرير
            </Button>
            <Button
              mode="outlined"
              icon="share"
              onPress={() => {/* Share */}}
              style={styles.actionButton}
            >
              مشاركة
            </Button>
          </View>
        </>
      ) : (
        <View style={styles.emptyContainer}>
          <Icon name="image-filter-hdr-outline" size={60} color="#CCC" />
          <Paragraph style={styles.emptyText}>لا توجد بيانات NDVI</Paragraph>
        </View>
      )}
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
  loadingText: {
    marginTop: 10,
    color: '#666',
  },
  loadingContainer: {
    padding: 50,
    alignItems: 'center',
  },
  selectorCard: {
    margin: 10,
    borderRadius: 15,
  },
  sectionTitle: {
    fontSize: 16,
    marginBottom: 10,
    color: '#333',
  },
  fieldChips: {
    flexDirection: 'row',
    gap: 8,
  },
  fieldChip: {
    marginRight: 8,
  },
  selectedFieldChip: {
    backgroundColor: '#2E7D32',
  },
  selectedChipText: {
    color: 'white',
  },
  currentValueCard: {
    margin: 10,
    borderRadius: 15,
    backgroundColor: '#E8F5E9',
  },
  currentValueContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  valueSection: {
    flex: 1,
  },
  valueLabel: {
    fontSize: 14,
    color: '#666',
  },
  currentValue: {
    fontSize: 48,
    fontWeight: 'bold',
    marginVertical: 5,
  },
  classificationChip: {
    alignSelf: 'flex-start',
  },
  classificationText: {
    color: 'white',
    fontWeight: 'bold',
  },
  trendSection: {
    alignItems: 'center',
    paddingLeft: 20,
  },
  scaleCard: {
    margin: 10,
    borderRadius: 15,
  },
  scaleContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  scaleItem: {
    alignItems: 'center',
  },
  scaleColor: {
    width: 30,
    height: 30,
    borderRadius: 15,
    marginBottom: 5,
  },
  scaleLabel: {
    fontSize: 10,
    color: '#666',
  },
  scaleRange: {
    fontSize: 8,
    color: '#999',
  },
  timeRangeContainer: {
    padding: 10,
  },
  chartCard: {
    margin: 10,
    borderRadius: 15,
  },
  chart: {
    borderRadius: 16,
    marginTop: 10,
  },
  analysisCard: {
    margin: 10,
    borderRadius: 15,
    borderLeftWidth: 4,
    borderLeftColor: '#9C27B0',
  },
  analysisHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  analysisTitle: {
    marginLeft: 10,
    fontSize: 16,
    color: '#9C27B0',
  },
  recommendationsTitle: {
    fontWeight: 'bold',
    marginTop: 10,
    marginBottom: 5,
  },
  recommendationItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
    padding: 8,
    backgroundColor: '#FFF8E1',
    borderRadius: 8,
  },
  recommendationText: {
    flex: 1,
    marginLeft: 8,
    fontSize: 13,
  },
  actionsContainer: {
    flexDirection: 'row',
    padding: 10,
    paddingBottom: 30,
    gap: 10,
  },
  actionButton: {
    flex: 1,
  },
  emptyContainer: {
    padding: 50,
    alignItems: 'center',
  },
  emptyText: {
    marginTop: 10,
    color: '#999',
  },
});
