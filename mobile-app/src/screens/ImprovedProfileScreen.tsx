/**
 * Improved Profile Screen
 * شاشة الملف الشخصي المحسّنة
 *
 * Features:
 * - Professional farmer profile with stats
 * - Achievement badges
 * - Activity timeline
 * - Account management
 * - Settings quick access
 */

import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Pressable,
  Image,
  Alert,
} from 'react-native';
import { Text } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import Animated, { FadeInDown, FadeInRight } from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { Card, Button, Chip, StatCard, ProgressBar } from '../components/ui';
import { Theme } from '../theme/design-system';

type ImprovedProfileScreenProps = {
  navigation: NativeStackNavigationProp<any>;
};

export default function ImprovedProfileScreen({ navigation }: ImprovedProfileScreenProps) {
  const [refreshing, setRefreshing] = useState(false);

  // Mock farmer data
  const farmerData = {
    name: 'أحمد المزارع',
    email: 'ahmed@farm.com',
    phone: '+966 50 123 4567',
    joinDate: '2024-01-15',
    farmName: 'مزرعة الأمل الخضراء',
    location: 'الرياض، المملكة العربية السعودية',
    avatar: null,
    verified: true,
    premium: true,
    stats: {
      totalFields: 12,
      totalArea: 145.5, // hectares
      activeFields: 10,
      totalHarvests: 34,
      avgNDVI: 0.68,
      totalAlerts: 156,
      resolvedAlerts: 142,
    },
    achievements: [
      { id: 1, name: 'مزارع محترف', icon: 'trophy', color: Theme.colors.johnDeere.yellow },
      { id: 2, name: 'صديق البيئة', icon: 'leaf', color: Theme.colors.success.main },
      { id: 3, name: 'مراقب نشط', icon: 'eye-check', color: Theme.colors.info.main },
      { id: 4, name: 'محصول وفير', icon: 'fruit-watermelon', color: Theme.colors.warning.main },
    ],
    recentActivity: [
      { id: 1, type: 'field_added', message: 'تمت إضافة حقل الطماطم الجديد', time: '2 ساعات' },
      { id: 2, type: 'alert_resolved', message: 'تم حل تنبيه رطوبة التربة', time: '5 ساعات' },
      { id: 3, type: 'harvest', message: 'حصاد ناجح لحقل الخيار', time: 'أمس' },
      { id: 4, type: 'ndvi_improved', message: 'تحسن NDVI في حقل الفلفل', time: 'أمس' },
    ],
  };

  const handleLogout = () => {
    Alert.alert(
      'تسجيل الخروج',
      'هل أنت متأكد من تسجيل الخروج؟',
      [
        { text: 'إلغاء', style: 'cancel' },
        {
          text: 'تسجيل الخروج',
          style: 'destructive',
          onPress: () => navigation.replace('Login'),
        },
      ]
    );
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'field_added': return 'plus-circle';
      case 'alert_resolved': return 'check-circle';
      case 'harvest': return 'fruit-watermelon';
      case 'ndvi_improved': return 'trending-up';
      default: return 'information';
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'field_added': return Theme.colors.success.main;
      case 'alert_resolved': return Theme.colors.info.main;
      case 'harvest': return Theme.colors.warning.main;
      case 'ndvi_improved': return Theme.colors.johnDeere.green;
      default: return Theme.colors.gray[500];
    }
  };

  return (
    <ScrollView style={styles.container}>
      {/* Header with Gradient */}
      <Animated.View entering={FadeInDown.delay(100)}>
        <LinearGradient
          colors={[Theme.colors.johnDeere.green, Theme.colors.johnDeere.darkGreen]}
          style={styles.header}
        >
          {/* Settings Icon */}
          <Pressable
            style={styles.settingsButton}
            onPress={() => navigation.navigate('Settings')}
          >
            <Icon name="cog" size={24} color="#fff" />
          </Pressable>

          {/* Profile Picture */}
          <View style={styles.avatarContainer}>
            <View style={styles.avatarCircle}>
              {farmerData.avatar ? (
                <Image source={{ uri: farmerData.avatar }} style={styles.avatar} />
              ) : (
                <Icon name="account" size={60} color={Theme.colors.johnDeere.yellow} />
              )}
            </View>
            {farmerData.verified && (
              <View style={styles.verifiedBadge}>
                <Icon name="check-decagram" size={24} color={Theme.colors.johnDeere.yellow} />
              </View>
            )}
            {farmerData.premium && (
              <View style={styles.premiumBadge}>
                <Icon name="crown" size={16} color={Theme.colors.johnDeere.yellow} />
              </View>
            )}
          </View>

          {/* Farmer Info */}
          <Text style={styles.farmerName}>{farmerData.name}</Text>
          <Text style={styles.farmName}>{farmerData.farmName}</Text>
          <View style={styles.locationContainer}>
            <Icon name="map-marker" size={14} color="rgba(255,255,255,0.9)" />
            <Text style={styles.location}>{farmerData.location}</Text>
          </View>

          {/* Member Since */}
          <View style={styles.memberSinceContainer}>
            <Icon name="calendar" size={14} color="rgba(255,255,255,0.7)" />
            <Text style={styles.memberSince}>
              عضو منذ {new Date(farmerData.joinDate).toLocaleDateString('ar-SA')}
            </Text>
          </View>

          {/* Quick Actions */}
          <View style={styles.quickActions}>
            <Pressable style={styles.quickActionButton}>
              <Icon name="pencil" size={20} color="#fff" />
              <Text style={styles.quickActionText}>تعديل الملف</Text>
            </Pressable>
            <Pressable style={styles.quickActionButton}>
              <Icon name="share-variant" size={20} color="#fff" />
              <Text style={styles.quickActionText}>مشاركة</Text>
            </Pressable>
          </View>
        </LinearGradient>
      </Animated.View>

      {/* Stats Grid */}
      <View style={styles.statsContainer}>
        <Animated.View entering={FadeInRight.delay(200)} style={styles.statItem}>
          <StatCard
            title="إجمالي الحقول"
            value={farmerData.stats.totalFields.toString()}
            subtitle={`${farmerData.stats.activeFields} نشط`}
            icon={<Icon name="map-marker-multiple" size={32} color={Theme.colors.johnDeere.green} />}
            color="primary"
            variant="gradient"
          />
        </Animated.View>

        <Animated.View entering={FadeInRight.delay(300)} style={styles.statItem}>
          <StatCard
            title="المساحة الكلية"
            value={`${farmerData.stats.totalArea}`}
            subtitle="هكتار"
            icon={<Icon name="ruler-square" size={32} color={Theme.colors.professional.earth} />}
            color="warning"
            variant="gradient"
          />
        </Animated.View>

        <Animated.View entering={FadeInRight.delay(400)} style={styles.statItem}>
          <StatCard
            title="متوسط NDVI"
            value={farmerData.stats.avgNDVI.toFixed(2)}
            subtitle="ممتاز"
            icon={<Icon name="image-filter-hdr" size={32} color={Theme.colors.success.main} />}
            color="success"
            variant="gradient"
            trend={{ value: 12, isPositive: true }}
          />
        </Animated.View>

        <Animated.View entering={FadeInRight.delay(500)} style={styles.statItem}>
          <StatCard
            title="الحصادات"
            value={farmerData.stats.totalHarvests.toString()}
            subtitle="ناجحة"
            icon={<Icon name="fruit-watermelon" size={32} color={Theme.colors.johnDeere.yellow} />}
            color="warning"
            variant="gradient"
          />
        </Animated.View>
      </View>

      {/* Achievements */}
      <Animated.View entering={FadeInDown.delay(600)}>
        <Card elevation="md" rounded="lg" style={styles.section}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleContainer}>
              <Icon name="trophy" size={24} color={Theme.colors.johnDeere.yellow} />
              <Text style={styles.sectionTitle}>الإنجازات</Text>
            </View>
            <Chip label={`${farmerData.achievements.length}`} variant="filled" size="small" />
          </View>

          <View style={styles.achievementsGrid}>
            {farmerData.achievements.map((achievement, index) => (
              <Animated.View
                key={achievement.id}
                entering={FadeInDown.delay(700 + index * 100)}
                style={styles.achievementItem}
              >
                <View style={[styles.achievementIcon, { backgroundColor: achievement.color + '20' }]}>
                  <Icon name={achievement.icon} size={32} color={achievement.color} />
                </View>
                <Text style={styles.achievementName}>{achievement.name}</Text>
              </Animated.View>
            ))}
          </View>
        </Card>
      </Animated.View>

      {/* Alert Stats */}
      <Animated.View entering={FadeInDown.delay(800)}>
        <Card elevation="md" rounded="lg" style={styles.section}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleContainer}>
              <Icon name="bell-badge" size={24} color={Theme.colors.info.main} />
              <Text style={styles.sectionTitle}>إحصائيات التنبيهات</Text>
            </View>
          </View>

          <View style={styles.alertStatsContainer}>
            <View style={styles.alertStatRow}>
              <Text style={styles.alertStatLabel}>إجمالي التنبيهات</Text>
              <Text style={styles.alertStatValue}>{farmerData.stats.totalAlerts}</Text>
            </View>
            <View style={styles.alertStatRow}>
              <Text style={styles.alertStatLabel}>التنبيهات المحلولة</Text>
              <Text style={[styles.alertStatValue, { color: Theme.colors.success.main }]}>
                {farmerData.stats.resolvedAlerts}
              </Text>
            </View>
            <ProgressBar
              progress={(farmerData.stats.resolvedAlerts / farmerData.stats.totalAlerts) * 100}
              color={Theme.colors.success.main}
              height={8}
              variant="gradient"
              style={styles.alertProgress}
            />
            <Text style={styles.alertStatPercentage}>
              معدل الحل: {((farmerData.stats.resolvedAlerts / farmerData.stats.totalAlerts) * 100).toFixed(1)}%
            </Text>
          </View>
        </Card>
      </Animated.View>

      {/* Recent Activity */}
      <Animated.View entering={FadeInDown.delay(900)}>
        <Card elevation="md" rounded="lg" style={styles.section}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleContainer}>
              <Icon name="clock-outline" size={24} color={Theme.colors.primary.main} />
              <Text style={styles.sectionTitle}>النشاط الأخير</Text>
            </View>
            <Pressable>
              <Text style={styles.viewAllText}>عرض الكل</Text>
            </Pressable>
          </View>

          <View style={styles.activityList}>
            {farmerData.recentActivity.map((activity, index) => (
              <View key={activity.id} style={styles.activityItem}>
                <View
                  style={[
                    styles.activityIconContainer,
                    { backgroundColor: getActivityColor(activity.type) + '20' },
                  ]}
                >
                  <Icon
                    name={getActivityIcon(activity.type)}
                    size={20}
                    color={getActivityColor(activity.type)}
                  />
                </View>
                <View style={styles.activityContent}>
                  <Text style={styles.activityMessage}>{activity.message}</Text>
                  <Text style={styles.activityTime}>منذ {activity.time}</Text>
                </View>
              </View>
            ))}
          </View>
        </Card>
      </Animated.View>

      {/* Account Section */}
      <Animated.View entering={FadeInDown.delay(1000)}>
        <Card elevation="md" rounded="lg" style={styles.section}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleContainer}>
              <Icon name="account-cog" size={24} color={Theme.colors.gray[700]} />
              <Text style={styles.sectionTitle}>الحساب</Text>
            </View>
          </View>

          <View style={styles.accountList}>
            <Pressable style={styles.accountItem}>
              <View style={styles.accountItemLeft}>
                <Icon name="email" size={20} color={Theme.colors.gray[600]} />
                <Text style={styles.accountItemText}>{farmerData.email}</Text>
              </View>
              <Icon name="chevron-left" size={20} color={Theme.colors.gray[400]} />
            </Pressable>

            <Pressable style={styles.accountItem}>
              <View style={styles.accountItemLeft}>
                <Icon name="phone" size={20} color={Theme.colors.gray[600]} />
                <Text style={styles.accountItemText}>{farmerData.phone}</Text>
              </View>
              <Icon name="chevron-left" size={20} color={Theme.colors.gray[400]} />
            </Pressable>

            <Pressable style={styles.accountItem}>
              <View style={styles.accountItemLeft}>
                <Icon name="lock" size={20} color={Theme.colors.gray[600]} />
                <Text style={styles.accountItemText}>تغيير كلمة المرور</Text>
              </View>
              <Icon name="chevron-left" size={20} color={Theme.colors.gray[400]} />
            </Pressable>

            <Pressable style={styles.accountItem}>
              <View style={styles.accountItemLeft}>
                <Icon name="bell" size={20} color={Theme.colors.gray[600]} />
                <Text style={styles.accountItemText}>إعدادات الإشعارات</Text>
              </View>
              <Icon name="chevron-left" size={20} color={Theme.colors.gray[400]} />
            </Pressable>

            <Pressable style={styles.accountItem}>
              <View style={styles.accountItemLeft}>
                <Icon name="shield-check" size={20} color={Theme.colors.gray[600]} />
                <Text style={styles.accountItemText}>الخصوصية والأمان</Text>
              </View>
              <Icon name="chevron-left" size={20} color={Theme.colors.gray[400]} />
            </Pressable>
          </View>
        </Card>
      </Animated.View>

      {/* Logout Button */}
      <Animated.View entering={FadeInDown.delay(1100)} style={styles.logoutContainer}>
        <Button
          title="تسجيل الخروج"
          variant="outlined"
          color="error"
          icon={<Icon name="logout" size={20} color={Theme.colors.error.main} />}
          onPress={handleLogout}
          fullWidth
        />
      </Animated.View>

      {/* Version Info */}
      <View style={styles.versionContainer}>
        <Text style={styles.versionText}>Sahool v3.3.1</Text>
      </View>

      <View style={{ height: Theme.spacing.xl }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Theme.colors.background.default,
  },
  header: {
    paddingTop: Theme.spacing['4xl'],
    paddingBottom: Theme.spacing.xl,
    alignItems: 'center',
    borderBottomLeftRadius: Theme.borderRadius['3xl'],
    borderBottomRightRadius: Theme.borderRadius['3xl'],
    position: 'relative',
  },
  settingsButton: {
    position: 'absolute',
    top: Theme.spacing['2xl'],
    right: Theme.spacing.lg,
    padding: Theme.spacing.sm,
  },
  avatarContainer: {
    position: 'relative',
    marginBottom: Theme.spacing.md,
  },
  avatarCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: '#fff',
  },
  avatar: {
    width: '100%',
    height: '100%',
    borderRadius: 60,
  },
  verifiedBadge: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    backgroundColor: Theme.colors.johnDeere.green,
    borderRadius: 12,
    borderWidth: 3,
    borderColor: '#fff',
  },
  premiumBadge: {
    position: 'absolute',
    top: -5,
    right: -5,
    backgroundColor: Theme.colors.johnDeere.yellow,
    borderRadius: 12,
    padding: 4,
    borderWidth: 2,
    borderColor: '#fff',
  },
  farmerName: {
    ...Theme.typography.styles.h2,
    color: '#fff',
    marginBottom: Theme.spacing.xs,
  },
  farmName: {
    ...Theme.typography.styles.body1,
    color: 'rgba(255,255,255,0.9)',
    marginBottom: Theme.spacing.xs,
  },
  locationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.xs,
    marginBottom: Theme.spacing.sm,
  },
  location: {
    ...Theme.typography.styles.body2,
    color: 'rgba(255,255,255,0.9)',
  },
  memberSinceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.xs,
    marginBottom: Theme.spacing.lg,
  },
  memberSince: {
    ...Theme.typography.styles.caption,
    color: 'rgba(255,255,255,0.7)',
  },
  quickActions: {
    flexDirection: 'row',
    gap: Theme.spacing.md,
  },
  quickActionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.xs,
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: Theme.spacing.lg,
    paddingVertical: Theme.spacing.sm,
    borderRadius: Theme.borderRadius.full,
  },
  quickActionText: {
    ...Theme.typography.styles.body2,
    color: '#fff',
    fontWeight: '600',
  },
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: Theme.spacing.md,
    gap: Theme.spacing.sm,
    marginTop: -Theme.spacing.xl,
  },
  statItem: {
    width: '48.5%',
  },
  section: {
    marginHorizontal: Theme.spacing.md,
    marginBottom: Theme.spacing.md,
    padding: Theme.spacing.md,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Theme.spacing.md,
  },
  sectionTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.sm,
  },
  sectionTitle: {
    ...Theme.typography.styles.h4,
    color: Theme.colors.text.primary,
  },
  viewAllText: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.johnDeere.green,
    fontWeight: '600',
  },
  achievementsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Theme.spacing.md,
  },
  achievementItem: {
    width: '22%',
    alignItems: 'center',
    gap: Theme.spacing.xs,
  },
  achievementIcon: {
    width: 64,
    height: 64,
    borderRadius: Theme.borderRadius.lg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  achievementName: {
    ...Theme.typography.styles.caption,
    color: Theme.colors.text.secondary,
    textAlign: 'center',
  },
  alertStatsContainer: {
    gap: Theme.spacing.sm,
  },
  alertStatRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  alertStatLabel: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.text.secondary,
  },
  alertStatValue: {
    ...Theme.typography.styles.h4,
    color: Theme.colors.text.primary,
    fontWeight: '600',
  },
  alertProgress: {
    marginVertical: Theme.spacing.sm,
  },
  alertStatPercentage: {
    ...Theme.typography.styles.caption,
    color: Theme.colors.success.main,
    textAlign: 'center',
    fontWeight: '600',
  },
  activityList: {
    gap: Theme.spacing.md,
  },
  activityItem: {
    flexDirection: 'row',
    gap: Theme.spacing.md,
  },
  activityIconContainer: {
    width: 40,
    height: 40,
    borderRadius: Theme.borderRadius.lg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  activityContent: {
    flex: 1,
  },
  activityMessage: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.text.primary,
    marginBottom: Theme.spacing.xs,
  },
  activityTime: {
    ...Theme.typography.styles.caption,
    color: Theme.colors.text.disabled,
  },
  accountList: {
    gap: Theme.spacing.xs,
  },
  accountItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: Theme.spacing.md,
    paddingHorizontal: Theme.spacing.sm,
    borderRadius: Theme.borderRadius.md,
  },
  accountItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.md,
    flex: 1,
  },
  accountItemText: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.text.primary,
  },
  logoutContainer: {
    paddingHorizontal: Theme.spacing.md,
    marginBottom: Theme.spacing.md,
  },
  versionContainer: {
    alignItems: 'center',
    paddingVertical: Theme.spacing.md,
  },
  versionText: {
    ...Theme.typography.styles.caption,
    color: Theme.colors.text.disabled,
  },
});
