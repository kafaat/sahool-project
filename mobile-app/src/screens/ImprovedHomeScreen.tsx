/**
 * Improved Home Screen
 * الشاشة الرئيسية المحسّنة
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Theme } from '../theme/design-system';
import { Card, StatCard, Button, Chip } from '../components/ui';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, {
  FadeInDown,
  FadeInUp,
  Layout,
} from 'react-native-reanimated';

interface ImprovedHomeScreenProps {
  navigation: NativeStackNavigationProp<any>;
}

const { width } = Dimensions.get('window');

export default function ImprovedHomeScreen({ navigation }: ImprovedHomeScreenProps) {
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = async () => {
    setRefreshing(true);
    // Simulate data refresh
    setTimeout(() => {
      setRefreshing(false);
    }, 2000);
  };

  return (
    <View style={styles.container}>
      {/* Header with Gradient */}
      <LinearGradient
        colors={[Theme.colors.primary.main, Theme.colors.primary.dark]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <View>
            <Text style={styles.greeting}>مرحباً بك 👋</Text>
            <Text style={styles.userName}>أحمد المزارع</Text>
          </View>

          <Button
            title="🔔"
            variant="text"
            onPress={() => navigation.navigate('Alerts')}
            style={styles.notificationButton}
          />
        </View>

        {/* Weather Widget */}
        <Card elevation="md" style={styles.weatherCard}>
          <View style={styles.weatherContent}>
            <View>
              <Text style={styles.weatherTemp}>28°C</Text>
              <Text style={styles.weatherDesc}>مشمس جزئياً</Text>
            </View>
            <Text style={styles.weatherIcon}>☀️</Text>
          </View>

          <View style={styles.weatherDetails}>
            <View style={styles.weatherDetail}>
              <Text style={styles.weatherDetailLabel}>الرطوبة</Text>
              <Text style={styles.weatherDetailValue}>65%</Text>
            </View>
            <View style={styles.weatherDetail}>
              <Text style={styles.weatherDetailLabel}>الرياح</Text>
              <Text style={styles.weatherDetailValue}>12 كم/س</Text>
            </View>
            <View style={styles.weatherDetail}>
              <Text style={styles.weatherDetailLabel}>الأمطار</Text>
              <Text style={styles.weatherDetailValue}>0%</Text>
            </View>
          </View>
        </Card>
      </LinearGradient>

      <ScrollView
        style={styles.scrollView}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Quick Stats */}
        <Animated.View
          entering={FadeInDown.delay(100).springify()}
          style={styles.section}
        >
          <Text style={styles.sectionTitle}>نظرة سريعة</Text>

          <View style={styles.statsGrid}>
            <StatCard
              title="إجمالي الحقول"
              value="12"
              icon={<Text style={styles.statIcon}>🌾</Text>}
              trend={{ value: 8, isPositive: true }}
              color="primary"
              style={styles.statCard}
            />

            <StatCard
              title="النباتات النشطة"
              value="485"
              icon={<Text style={styles.statIcon}>🌱</Text>}
              trend={{ value: 12, isPositive: true }}
              color="success"
              style={styles.statCard}
            />

            <StatCard
              title="التنبيهات"
              value="3"
              icon={<Text style={styles.statIcon}>⚠️</Text>}
              color="warning"
              style={styles.statCard}
            />

            <StatCard
              title="الإنتاجية"
              value="94%"
              icon={<Text style={styles.statIcon}>📊</Text>}
              trend={{ value: 5, isPositive: true }}
              color="info"
              style={styles.statCard}
            />
          </View>
        </Animated.View>

        {/* Recent Fields */}
        <Animated.View
          entering={FadeInDown.delay(200).springify()}
          style={styles.section}
        >
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>الحقول الأخيرة</Text>
            <Button
              title="عرض الكل"
              variant="text"
              size="small"
              onPress={() => navigation.navigate('Fields')}
            />
          </View>

          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {[1, 2, 3].map((field) => (
              <Card
                key={field}
                elevation="md"
                rounded="lg"
                pressable
                onPress={() => navigation.navigate('FieldDetail', { id: field })}
                style={styles.fieldCard}
              >
                <LinearGradient
                  colors={[Theme.colors.primary.main, Theme.colors.primary.dark]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={styles.fieldGradient}
                >
                  <Text style={styles.fieldNumber}>#{field}</Text>
                </LinearGradient>

                <View style={styles.fieldInfo}>
                  <Text style={styles.fieldName}>حقل الطماطم {field}</Text>
                  <Text style={styles.fieldArea}>5.2 هكتار</Text>

                  <View style={styles.fieldTags}>
                    <Chip
                      label="طماطم"
                      size="small"
                      color="success"
                      variant="filled"
                    />
                    <Chip
                      label="صحي"
                      size="small"
                      color="success"
                      variant="outlined"
                    />
                  </View>

                  <View style={styles.fieldStats}>
                    <View style={styles.fieldStat}>
                      <Text style={styles.fieldStatLabel}>NDVI</Text>
                      <Text style={styles.fieldStatValue}>0.68</Text>
                    </View>
                    <View style={styles.fieldStat}>
                      <Text style={styles.fieldStatLabel}>الصحة</Text>
                      <Text style={styles.fieldStatValue}>85%</Text>
                    </View>
                  </View>
                </View>
              </Card>
            ))}
          </ScrollView>
        </Animated.View>

        {/* Quick Actions */}
        <Animated.View
          entering={FadeInDown.delay(300).springify()}
          style={styles.section}
        >
          <Text style={styles.sectionTitle}>إجراءات سريعة</Text>

          <View style={styles.actionsGrid}>
            <Card
              pressable
              onPress={() => navigation.navigate('Fields')}
              style={styles.actionCard}
            >
              <Text style={styles.actionIcon}>➕</Text>
              <Text style={styles.actionTitle}>إضافة حقل</Text>
            </Card>

            <Card
              pressable
              onPress={() => navigation.navigate('NDVI')}
              style={styles.actionCard}
            >
              <Text style={styles.actionIcon}>📊</Text>
              <Text style={styles.actionTitle}>تحليل NDVI</Text>
            </Card>

            <Card
              pressable
              onPress={() => navigation.navigate('Alerts')}
              style={styles.actionCard}
            >
              <Text style={styles.actionIcon}>🔔</Text>
              <Text style={styles.actionTitle}>التنبيهات</Text>
            </Card>

            <Card
              pressable
              onPress={() => navigation.navigate('Profile')}
              style={styles.actionCard}
            >
              <Text style={styles.actionIcon}>⚙️</Text>
              <Text style={styles.actionTitle}>الإعدادات</Text>
            </Card>
          </View>
        </Animated.View>

        {/* Recent Alerts */}
        <Animated.View
          entering={FadeInDown.delay(400).springify()}
          style={styles.section}
        >
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>آخر التنبيهات</Text>
            <Button
              title="عرض الكل"
              variant="text"
              size="small"
              onPress={() => navigation.navigate('Alerts')}
            />
          </View>

          <Card elevation="sm" style={styles.alertCard}>
            <View style={styles.alertHeader}>
              <View style={[styles.alertDot, { backgroundColor: Theme.colors.warning.main }]} />
              <Text style={styles.alertTitle}>انخفاض مستوى الرطوبة</Text>
            </View>
            <Text style={styles.alertDescription}>
              الحقل #3 يحتاج إلى الري - مستوى الرطوبة 35%
            </Text>
            <Text style={styles.alertTime}>منذ ساعتين</Text>
          </Card>

          <Card elevation="sm" style={styles.alertCard}>
            <View style={styles.alertHeader}>
              <View style={[styles.alertDot, { backgroundColor: Theme.colors.success.main }]} />
              <Text style={styles.alertTitle}>تحديث NDVI متاح</Text>
            </View>
            <Text style={styles.alertDescription}>
              صور جديدة من الأقمار الصناعية متاحة للتحليل
            </Text>
            <Text style={styles.alertTime}>منذ 4 ساعات</Text>
          </Card>
        </Animated.View>

        <View style={{ height: Theme.spacing['2xl'] }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Theme.colors.background.default,
  },
  header: {
    paddingTop: 60,
    paddingHorizontal: Theme.spacing.md,
    paddingBottom: Theme.spacing.lg,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Theme.spacing.lg,
  },
  greeting: {
    fontSize: Theme.typography.fontSize.base,
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: Theme.spacing.xs,
  },
  userName: {
    fontSize: Theme.typography.fontSize['2xl'],
    fontWeight: Theme.typography.fontWeight.bold,
    color: '#FFFFFF',
  },
  notificationButton: {
    width: 44,
    height: 44,
    borderRadius: Theme.borderRadius.full,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
  weatherCard: {
    marginHorizontal: 0,
  },
  weatherContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Theme.spacing.md,
  },
  weatherTemp: {
    fontSize: Theme.typography.fontSize['3xl'],
    fontWeight: Theme.typography.fontWeight.bold,
    color: Theme.colors.text.primary,
  },
  weatherDesc: {
    fontSize: Theme.typography.fontSize.base,
    color: Theme.colors.text.secondary,
  },
  weatherIcon: {
    fontSize: 48,
  },
  weatherDetails: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    borderTopWidth: 1,
    borderTopColor: Theme.colors.gray[200],
    paddingTop: Theme.spacing.md,
  },
  weatherDetail: {
    alignItems: 'center',
  },
  weatherDetailLabel: {
    fontSize: Theme.typography.fontSize.xs,
    color: Theme.colors.text.secondary,
    marginBottom: Theme.spacing.xs,
  },
  weatherDetailValue: {
    fontSize: Theme.typography.fontSize.base,
    fontWeight: Theme.typography.fontWeight.semibold,
    color: Theme.colors.text.primary,
  },
  scrollView: {
    flex: 1,
  },
  section: {
    paddingHorizontal: Theme.spacing.md,
    marginTop: Theme.spacing.lg,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Theme.spacing.md,
  },
  sectionTitle: {
    fontSize: Theme.typography.fontSize.lg,
    fontWeight: Theme.typography.fontWeight.bold,
    color: Theme.colors.text.primary,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -Theme.spacing.xs,
  },
  statCard: {
    width: (width - Theme.spacing.md * 2 - Theme.spacing.xs * 2) / 2,
    marginHorizontal: Theme.spacing.xs,
    marginBottom: Theme.spacing.md,
  },
  statIcon: {
    fontSize: 24,
  },
  fieldCard: {
    width: 200,
    marginRight: Theme.spacing.md,
  },
  fieldGradient: {
    height: 80,
    borderTopLeftRadius: Theme.borderRadius.lg,
    borderTopRightRadius: Theme.borderRadius.lg,
    padding: Theme.spacing.md,
    justifyContent: 'center',
  },
  fieldNumber: {
    fontSize: Theme.typography.fontSize['2xl'],
    fontWeight: Theme.typography.fontWeight.bold,
    color: '#FFFFFF',
  },
  fieldInfo: {
    padding: Theme.spacing.md,
  },
  fieldName: {
    fontSize: Theme.typography.fontSize.base,
    fontWeight: Theme.typography.fontWeight.semibold,
    color: Theme.colors.text.primary,
    marginBottom: Theme.spacing.xs,
  },
  fieldArea: {
    fontSize: Theme.typography.fontSize.sm,
    color: Theme.colors.text.secondary,
    marginBottom: Theme.spacing.md,
  },
  fieldTags: {
    flexDirection: 'row',
    gap: Theme.spacing.xs,
    marginBottom: Theme.spacing.md,
  },
  fieldStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  fieldStat: {
    alignItems: 'center',
  },
  fieldStatLabel: {
    fontSize: Theme.typography.fontSize.xs,
    color: Theme.colors.text.secondary,
    marginBottom: Theme.spacing.xs,
  },
  fieldStatValue: {
    fontSize: Theme.typography.fontSize.md,
    fontWeight: Theme.typography.fontWeight.bold,
    color: Theme.colors.primary.main,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -Theme.spacing.xs,
  },
  actionCard: {
    width: (width - Theme.spacing.md * 2 - Theme.spacing.xs * 2) / 2,
    marginHorizontal: Theme.spacing.xs,
    marginBottom: Theme.spacing.md,
    alignItems: 'center',
    padding: Theme.spacing.lg,
  },
  actionIcon: {
    fontSize: 36,
    marginBottom: Theme.spacing.sm,
  },
  actionTitle: {
    fontSize: Theme.typography.fontSize.sm,
    fontWeight: Theme.typography.fontWeight.medium,
    color: Theme.colors.text.primary,
    textAlign: 'center',
  },
  alertCard: {
    marginBottom: Theme.spacing.md,
  },
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Theme.spacing.sm,
  },
  alertDot: {
    width: 8,
    height: 8,
    borderRadius: Theme.borderRadius.full,
    marginRight: Theme.spacing.sm,
  },
  alertTitle: {
    fontSize: Theme.typography.fontSize.base,
    fontWeight: Theme.typography.fontWeight.semibold,
    color: Theme.colors.text.primary,
  },
  alertDescription: {
    fontSize: Theme.typography.fontSize.sm,
    color: Theme.colors.text.secondary,
    marginBottom: Theme.spacing.xs,
  },
  alertTime: {
    fontSize: Theme.typography.fontSize.xs,
    color: Theme.colors.text.hint,
  },
});
