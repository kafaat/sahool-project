import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Alert
} from 'react-native';
import {
  Text,
  Card,
  List,
  Avatar,
  Button,
  Switch,
  useTheme,
  Divider
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import AsyncStorage from '@react-native-async-storage/async-storage';

type ProfileScreenProps = {
  navigation: NativeStackNavigationProp<any>;
};

export default function ProfileScreen({ navigation }: ProfileScreenProps) {
  const theme = useTheme();
  const [user, setUser] = useState({
    name: 'محمد أحمد',
    email: 'mohamed@example.com',
    phone: '+966 50 123 4567',
    role: 'مزارع',
    joinDate: '2024-01-15',
    avatar: null,
  });

  const [settings, setSettings] = useState({
    notifications: true,
    emailAlerts: false,
    smsAlerts: true,
    darkMode: false,
    language: 'ar',
  });

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        const parsedData = JSON.parse(userData);
        setUser({
          ...user,
          ...parsedData,
        });
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'تسجيل الخروج',
      'هل أنت متأكد أنك تريد تسجيل الخروج؟',
      [
        {
          text: 'إلغاء',
          style: 'cancel',
        },
        {
          text: 'تسجيل الخروج',
          style: 'destructive',
          onPress: async () => {
            await AsyncStorage.removeItem('userToken');
            await AsyncStorage.removeItem('userData');
            navigation.replace('Login');
          },
        },
      ]
    );
  };

  const handleSettingChange = async (key: string, value: boolean) => {
    setSettings({
      ...settings,
      [key]: value,
    });

    // Save to storage
    try {
      await AsyncStorage.setItem('settings', JSON.stringify({ ...settings, [key]: value }));
    } catch (error) {
      console.error('Error saving settings:', error);
    }
  };

  return (
    <ScrollView style={styles.container}>
      {/* Profile Header */}
      <Card style={styles.headerCard}>
        <Card.Content style={styles.headerContent}>
          <Avatar.Icon
            size={80}
            icon="account"
            style={styles.avatar}
          />
          <Text variant="titleLarge" style={styles.name}>
            {user.name}
          </Text>
          <Text variant="bodyMedium" style={styles.role}>
            {user.role}
          </Text>
          <Text variant="bodySmall" style={styles.joinDate}>
            عضو منذ {new Date(user.joinDate).toLocaleDateString('ar-SA', {
              year: 'numeric',
              month: 'long',
            })}
          </Text>

          <Button
            mode="outlined"
            icon="pencil"
            style={styles.editButton}
            onPress={() => Alert.alert('تعديل الملف الشخصي', 'سيتم إضافة هذه الميزة قريباً')}
          >
            تعديل الملف الشخصي
          </Button>
        </Card.Content>
      </Card>

      {/* Account Info */}
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            معلومات الحساب
          </Text>

          <List.Item
            title="البريد الإلكتروني"
            description={user.email}
            left={(props) => <List.Icon {...props} icon="email" />}
          />
          <Divider />

          <List.Item
            title="رقم الهاتف"
            description={user.phone}
            left={(props) => <List.Icon {...props} icon="phone" />}
          />
          <Divider />

          <List.Item
            title="كلمة المرور"
            description="••••••••"
            left={(props) => <List.Icon {...props} icon="lock" />}
            right={(props) => (
              <List.Icon
                {...props}
                icon="chevron-left"
                onPress={() => Alert.alert('تغيير كلمة المرور', 'سيتم إضافة هذه الميزة قريباً')}
              />
            )}
          />
        </Card.Content>
      </Card>

      {/* Notifications Settings */}
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            الإشعارات
          </Text>

          <List.Item
            title="إشعارات التطبيق"
            description="تلقي إشعارات داخل التطبيق"
            left={(props) => <List.Icon {...props} icon="bell" />}
            right={() => (
              <Switch
                value={settings.notifications}
                onValueChange={(value) => handleSettingChange('notifications', value)}
              />
            )}
          />
          <Divider />

          <List.Item
            title="إشعارات البريد الإلكتروني"
            description="تلقي تنبيهات عبر البريد"
            left={(props) => <List.Icon {...props} icon="email-alert" />}
            right={() => (
              <Switch
                value={settings.emailAlerts}
                onValueChange={(value) => handleSettingChange('emailAlerts', value)}
              />
            )}
          />
          <Divider />

          <List.Item
            title="إشعارات SMS"
            description="تلقي رسائل نصية للتنبيهات المهمة"
            left={(props) => <List.Icon {...props} icon="message-alert" />}
            right={() => (
              <Switch
                value={settings.smsAlerts}
                onValueChange={(value) => handleSettingChange('smsAlerts', value)}
              />
            )}
          />
        </Card.Content>
      </Card>

      {/* App Settings */}
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            إعدادات التطبيق
          </Text>

          <List.Item
            title="الوضع الليلي"
            description="تفعيل المظهر الداكن"
            left={(props) => <List.Icon {...props} icon="theme-light-dark" />}
            right={() => (
              <Switch
                value={settings.darkMode}
                onValueChange={(value) => {
                  handleSettingChange('darkMode', value);
                  Alert.alert('الوضع الليلي', 'سيتم إضافة هذه الميزة في التحديث القادم');
                }}
              />
            )}
          />
          <Divider />

          <List.Item
            title="اللغة"
            description="العربية"
            left={(props) => <List.Icon {...props} icon="translate" />}
            right={(props) => (
              <List.Icon
                {...props}
                icon="chevron-left"
                onPress={() => Alert.alert('تغيير اللغة', 'سيتم إضافة دعم لغات إضافية قريباً')}
              />
            )}
          />
        </Card.Content>
      </Card>

      {/* Help & Support */}
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            المساعدة والدعم
          </Text>

          <List.Item
            title="مركز المساعدة"
            left={(props) => <List.Icon {...props} icon="help-circle" />}
            right={(props) => <List.Icon {...props} icon="chevron-left" />}
            onPress={() => Alert.alert('مركز المساعدة', 'سيتم إضافة دليل المساعدة قريباً')}
          />
          <Divider />

          <List.Item
            title="تواصل معنا"
            left={(props) => <List.Icon {...props} icon="email-outline" />}
            right={(props) => <List.Icon {...props} icon="chevron-left" />}
            onPress={() => Alert.alert('تواصل معنا', 'support@sahool.com\n+966 11 123 4567')}
          />
          <Divider />

          <List.Item
            title="تقييم التطبيق"
            left={(props) => <List.Icon {...props} icon="star" />}
            right={(props) => <List.Icon {...props} icon="chevron-left" />}
            onPress={() => Alert.alert('تقييم التطبيق', 'شكراً لاهتمامك! سننقلك لمتجر التطبيقات')}
          />
          <Divider />

          <List.Item
            title="شارك التطبيق"
            left={(props) => <List.Icon {...props} icon="share-variant" />}
            right={(props) => <List.Icon {...props} icon="chevron-left" />}
            onPress={() => Alert.alert('مشاركة التطبيق', 'سيتم إضافة ميزة المشاركة قريباً')}
          />
        </Card.Content>
      </Card>

      {/* About */}
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            عن التطبيق
          </Text>

          <List.Item
            title="الإصدار"
            description="3.0.0"
            left={(props) => <List.Icon {...props} icon="information" />}
          />
          <Divider />

          <List.Item
            title="الشروط والأحكام"
            left={(props) => <List.Icon {...props} icon="file-document" />}
            right={(props) => <List.Icon {...props} icon="chevron-left" />}
            onPress={() => Alert.alert('الشروط والأحكام', 'سيتم عرض الشروط والأحكام')}
          />
          <Divider />

          <List.Item
            title="سياسة الخصوصية"
            left={(props) => <List.Icon {...props} icon="shield-check" />}
            right={(props) => <List.Icon {...props} icon="chevron-left" />}
            onPress={() => Alert.alert('سياسة الخصوصية', 'سيتم عرض سياسة الخصوصية')}
          />
        </Card.Content>
      </Card>

      {/* Logout Button */}
      <Button
        mode="contained"
        icon="logout"
        style={styles.logoutButton}
        buttonColor="#F44336"
        onPress={handleLogout}
      >
        تسجيل الخروج
      </Button>

      <View style={styles.footer}>
        <Text variant="bodySmall" style={styles.footerText}>
          © 2024 Sahool Platform
        </Text>
        <Text variant="bodySmall" style={styles.footerText}>
          جميع الحقوق محفوظة
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  headerCard: {
    margin: 0,
    borderRadius: 0,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
    elevation: 4,
  },
  headerContent: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  avatar: {
    backgroundColor: '#2E7D32',
    marginBottom: 16,
  },
  name: {
    fontWeight: 'bold',
    marginBottom: 4,
  },
  role: {
    color: '#666',
    marginBottom: 4,
  },
  joinDate: {
    color: '#999',
    marginBottom: 16,
  },
  editButton: {
    marginTop: 8,
  },
  card: {
    margin: 16,
    marginBottom: 0,
    elevation: 2,
    borderRadius: 12,
  },
  sectionTitle: {
    fontWeight: 'bold',
    marginBottom: 8,
  },
  logoutButton: {
    margin: 16,
    paddingVertical: 6,
  },
  footer: {
    alignItems: 'center',
    padding: 24,
    paddingBottom: 32,
  },
  footerText: {
    color: '#999',
    marginBottom: 4,
  },
});
