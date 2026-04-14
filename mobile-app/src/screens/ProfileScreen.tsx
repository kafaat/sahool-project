import React, { useEffect, useState } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  Alert,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Button,
  Avatar,
  List,
  Divider,
  Switch,
  ActivityIndicator,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface UserProfile {
  id: number;
  name: string;
  email: string;
  phone?: string;
  role: string;
  region?: string;
  total_fields?: number;
  total_area?: number;
  created_at?: string;
}

interface Settings {
  notifications_enabled: boolean;
  alert_critical: boolean;
  alert_warning: boolean;
  alert_info: boolean;
  language: string;
  dark_mode: boolean;
}

export default function ProfileScreen({ navigation }: any) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [settings, setSettings] = useState<Settings>({
    notifications_enabled: true,
    alert_critical: true,
    alert_warning: true,
    alert_info: false,
    language: 'ar',
    dark_mode: false,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const userData = await AsyncStorage.getItem('user');
      if (userData) {
        setUser(JSON.parse(userData));
      }
      const savedSettings = await AsyncStorage.getItem('settings');
      if (savedSettings) {
        setSettings(JSON.parse(savedSettings));
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateSetting = async (key: keyof Settings, value: boolean | string) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    await AsyncStorage.setItem('settings', JSON.stringify(newSettings));
  };

  const handleLogout = () => {
    Alert.alert(
      'تسجيل الخروج',
      'هل أنت متأكد من رغبتك في تسجيل الخروج؟',
      [
        { text: 'إلغاء', style: 'cancel' },
        {
          text: 'تسجيل الخروج',
          style: 'destructive',
          onPress: async () => {
            await AsyncStorage.removeItem('authToken');
            await AsyncStorage.removeItem('user');
            navigation.replace('Login');
          },
        },
      ]
    );
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'admin':
        return 'مدير النظام';
      case 'farmer':
        return 'مزارع';
      case 'agronomist':
        return 'مهندس زراعي';
      case 'viewer':
        return 'مشاهد';
      default:
        return role;
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2E7D32" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {/* Profile Header */}
      <Card style={styles.profileCard}>
        <Card.Content style={styles.profileContent}>
          <Avatar.Text
            size={80}
            label={user?.name?.charAt(0) || 'م'}
            style={styles.avatar}
          />
          <Title style={styles.userName}>{user?.name || 'مستخدم'}</Title>
          <Paragraph style={styles.userEmail}>{user?.email}</Paragraph>
          <View style={styles.roleContainer}>
            <Icon name="account-badge" size={16} color="#2E7D32" />
            <Paragraph style={styles.roleText}>
              {getRoleLabel(user?.role || 'farmer')}
            </Paragraph>
          </View>
        </Card.Content>
      </Card>

      {/* Stats Card */}
      <Card style={styles.statsCard}>
        <Card.Content>
          <View style={styles.statsContainer}>
            <View style={styles.statItem}>
              <Icon name="map-marker-multiple" size={30} color="#2E7D32" />
              <Title style={styles.statNumber}>{user?.total_fields || 0}</Title>
              <Paragraph style={styles.statLabel}>حقل</Paragraph>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Icon name="ruler-square" size={30} color="#1976D2" />
              <Title style={styles.statNumber}>{user?.total_area || 0}</Title>
              <Paragraph style={styles.statLabel}>هكتار</Paragraph>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Icon name="map" size={30} color="#FF5722" />
              <Title style={styles.statNumber}>1</Title>
              <Paragraph style={styles.statLabel}>منطقة</Paragraph>
            </View>
          </View>
        </Card.Content>
      </Card>

      {/* Account Settings */}
      <Card style={styles.settingsCard}>
        <Card.Content>
          <Title style={styles.sectionTitle}>إعدادات الحساب</Title>

          <List.Item
            title="تعديل الملف الشخصي"
            description="الاسم، البريد، رقم الهاتف"
            left={(props) => <List.Icon {...props} icon="account-edit" />}
            right={(props) => <List.Icon {...props} icon="chevron-left" />}
            onPress={() => {/* Navigate to edit profile */}}
          />
          <Divider />
          <List.Item
            title="تغيير كلمة المرور"
            description="تحديث كلمة المرور الخاصة بك"
            left={(props) => <List.Icon {...props} icon="lock-reset" />}
            right={(props) => <List.Icon {...props} icon="chevron-left" />}
            onPress={() => {/* Navigate to change password */}}
          />
          <Divider />
          <List.Item
            title="المنطقة"
            description={user?.region || 'اليمن'}
            left={(props) => <List.Icon {...props} icon="map-marker" />}
            right={(props) => <List.Icon {...props} icon="chevron-left" />}
            onPress={() => {/* Navigate to region settings */}}
          />
        </Card.Content>
      </Card>

      {/* Notification Settings */}
      <Card style={styles.settingsCard}>
        <Card.Content>
          <Title style={styles.sectionTitle}>إعدادات التنبيهات</Title>

          <List.Item
            title="تفعيل التنبيهات"
            description="استقبال إشعارات فورية"
            left={(props) => <List.Icon {...props} icon="bell" />}
            right={() => (
              <Switch
                value={settings.notifications_enabled}
                onValueChange={(value) =>
                  updateSetting('notifications_enabled', value)
                }
                color="#2E7D32"
              />
            )}
          />
          <Divider />
          <List.Item
            title="تنبيهات حرجة"
            description="تنبيهات الطوارئ والمشاكل الخطيرة"
            left={(props) => (
              <List.Icon {...props} icon="alert-circle" color="#F44336" />
            )}
            right={() => (
              <Switch
                value={settings.alert_critical}
                onValueChange={(value) => updateSetting('alert_critical', value)}
                color="#F44336"
                disabled={!settings.notifications_enabled}
              />
            )}
          />
          <Divider />
          <List.Item
            title="تنبيهات تحذيرية"
            description="تحذيرات الطقس والنباتات"
            left={(props) => (
              <List.Icon {...props} icon="alert" color="#FF9800" />
            )}
            right={() => (
              <Switch
                value={settings.alert_warning}
                onValueChange={(value) => updateSetting('alert_warning', value)}
                color="#FF9800"
                disabled={!settings.notifications_enabled}
              />
            )}
          />
          <Divider />
          <List.Item
            title="تنبيهات معلوماتية"
            description="نصائح وتحديثات عامة"
            left={(props) => (
              <List.Icon {...props} icon="information" color="#2196F3" />
            )}
            right={() => (
              <Switch
                value={settings.alert_info}
                onValueChange={(value) => updateSetting('alert_info', value)}
                color="#2196F3"
                disabled={!settings.notifications_enabled}
              />
            )}
          />
        </Card.Content>
      </Card>

      {/* App Settings */}
      <Card style={styles.settingsCard}>
        <Card.Content>
          <Title style={styles.sectionTitle}>إعدادات التطبيق</Title>

          <List.Item
            title="اللغة"
            description="العربية"
            left={(props) => <List.Icon {...props} icon="translate" />}
            right={(props) => <List.Icon {...props} icon="chevron-left" />}
            onPress={() => {/* Show language picker */}}
          />
          <Divider />
          <List.Item
            title="الوضع الداكن"
            description="تغيير مظهر التطبيق"
            left={(props) => <List.Icon {...props} icon="theme-light-dark" />}
            right={() => (
              <Switch
                value={settings.dark_mode}
                onValueChange={(value) => updateSetting('dark_mode', value)}
                color="#2E7D32"
              />
            )}
          />
        </Card.Content>
      </Card>

      {/* Help & Support */}
      <Card style={styles.settingsCard}>
        <Card.Content>
          <Title style={styles.sectionTitle}>المساعدة والدعم</Title>

          <List.Item
            title="دليل الاستخدام"
            description="تعرف على كيفية استخدام التطبيق"
            left={(props) => <List.Icon {...props} icon="book-open-variant" />}
            right={(props) => <List.Icon {...props} icon="chevron-left" />}
            onPress={() => {/* Navigate to help */}}
          />
          <Divider />
          <List.Item
            title="تواصل معنا"
            description="support@sahool.ye"
            left={(props) => <List.Icon {...props} icon="email" />}
            right={(props) => <List.Icon {...props} icon="chevron-left" />}
            onPress={() => {/* Open email */}}
          />
          <Divider />
          <List.Item
            title="عن التطبيق"
            description="الإصدار 1.0.0"
            left={(props) => <List.Icon {...props} icon="information" />}
            right={(props) => <List.Icon {...props} icon="chevron-left" />}
            onPress={() => {/* Show about dialog */}}
          />
        </Card.Content>
      </Card>

      {/* Logout Button */}
      <View style={styles.logoutContainer}>
        <Button
          mode="outlined"
          icon="logout"
          onPress={handleLogout}
          style={styles.logoutButton}
          textColor="#F44336"
        >
          تسجيل الخروج
        </Button>
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        <Paragraph style={styles.footerText}>
          منصة سهول الزراعية © 2024
        </Paragraph>
        <Paragraph style={styles.footerText}>
          صنع في اليمن 🇾🇪
        </Paragraph>
      </View>
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
  profileCard: {
    margin: 10,
    borderRadius: 15,
    backgroundColor: '#2E7D32',
  },
  profileContent: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  avatar: {
    backgroundColor: 'white',
  },
  userName: {
    color: 'white',
    fontSize: 22,
    fontWeight: 'bold',
    marginTop: 10,
  },
  userEmail: {
    color: 'rgba(255,255,255,0.8)',
    fontSize: 14,
  },
  roleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 15,
    paddingVertical: 5,
    borderRadius: 20,
    marginTop: 10,
  },
  roleText: {
    color: 'white',
    marginLeft: 5,
    fontSize: 12,
  },
  statsCard: {
    margin: 10,
    marginTop: -20,
    borderRadius: 15,
    elevation: 4,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 10,
  },
  statItem: {
    alignItems: 'center',
    flex: 1,
  },
  statDivider: {
    width: 1,
    backgroundColor: '#E0E0E0',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 5,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
  },
  settingsCard: {
    margin: 10,
    borderRadius: 15,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  logoutContainer: {
    padding: 10,
    paddingTop: 20,
  },
  logoutButton: {
    borderColor: '#F44336',
  },
  footer: {
    alignItems: 'center',
    padding: 20,
    paddingBottom: 40,
  },
  footerText: {
    color: '#999',
    fontSize: 12,
  },
});
