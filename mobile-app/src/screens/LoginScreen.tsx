import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Image,
} from 'react-native';
import {
  TextInput,
  Button,
  Title,
  Paragraph,
  Snackbar,
  ActivityIndicator,
} from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiService } from '../services/api';

export default function LoginScreen({ navigation }: any) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) {
      setError('الرجاء إدخال البريد الإلكتروني وكلمة المرور');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await apiService.login(email, password);
      const { access_token, user } = response.data;

      await AsyncStorage.setItem('authToken', access_token);
      await AsyncStorage.setItem('user', JSON.stringify(user));

      navigation.replace('Main');
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('البريد الإلكتروني أو كلمة المرور غير صحيحة');
      } else if (err.response?.status === 422) {
        setError('الرجاء التحقق من صحة البيانات المدخلة');
      } else {
        setError('حدث خطأ في الاتصال. الرجاء المحاولة مرة أخرى');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setLoading(true);
    // Demo mode - bypass authentication
    await AsyncStorage.setItem('authToken', 'demo_token');
    await AsyncStorage.setItem('user', JSON.stringify({
      id: 1,
      name: 'مستخدم تجريبي',
      email: 'demo@sahool.ye',
      role: 'farmer',
    }));
    navigation.replace('Main');
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <View style={styles.logoContainer}>
          <View style={styles.logoPlaceholder}>
            <Title style={styles.logoText}>سهول</Title>
          </View>
          <Title style={styles.title}>منصة سهول الزراعية</Title>
          <Paragraph style={styles.subtitle}>
            الحلول الذكية للزراعة اليمنية
          </Paragraph>
        </View>

        <View style={styles.formContainer}>
          <TextInput
            label="البريد الإلكتروني"
            value={email}
            onChangeText={setEmail}
            mode="outlined"
            keyboardType="email-address"
            autoCapitalize="none"
            style={styles.input}
            left={<TextInput.Icon icon="email" />}
            disabled={loading}
          />

          <TextInput
            label="كلمة المرور"
            value={password}
            onChangeText={setPassword}
            mode="outlined"
            secureTextEntry={!showPassword}
            style={styles.input}
            left={<TextInput.Icon icon="lock" />}
            right={
              <TextInput.Icon
                icon={showPassword ? 'eye-off' : 'eye'}
                onPress={() => setShowPassword(!showPassword)}
              />
            }
            disabled={loading}
          />

          <Button
            mode="contained"
            onPress={handleLogin}
            style={styles.loginButton}
            loading={loading}
            disabled={loading}
          >
            {loading ? 'جاري تسجيل الدخول...' : 'تسجيل الدخول'}
          </Button>

          <Button
            mode="outlined"
            onPress={handleDemoLogin}
            style={styles.demoButton}
            disabled={loading}
          >
            الدخول بالوضع التجريبي
          </Button>

          <View style={styles.linksContainer}>
            <Button
              mode="text"
              onPress={() => {/* Navigate to forgot password */}}
              style={styles.linkButton}
            >
              نسيت كلمة المرور؟
            </Button>
            <Button
              mode="text"
              onPress={() => {/* Navigate to register */}}
              style={styles.linkButton}
            >
              إنشاء حساب جديد
            </Button>
          </View>
        </View>

        <View style={styles.footer}>
          <Paragraph style={styles.footerText}>
            © 2024 Sahool Yemen - جميع الحقوق محفوظة
          </Paragraph>
        </View>
      </ScrollView>

      <Snackbar
        visible={!!error}
        onDismiss={() => setError('')}
        duration={4000}
        action={{
          label: 'إغلاق',
          onPress: () => setError(''),
        }}
      >
        {error}
      </Snackbar>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logoPlaceholder: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#2E7D32',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
  },
  logoText: {
    color: 'white',
    fontSize: 28,
    fontWeight: 'bold',
  },
  title: {
    fontSize: 26,
    fontWeight: 'bold',
    color: '#2E7D32',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  formContainer: {
    backgroundColor: 'white',
    borderRadius: 15,
    padding: 20,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  input: {
    marginBottom: 15,
  },
  loginButton: {
    marginTop: 10,
    paddingVertical: 5,
    backgroundColor: '#2E7D32',
  },
  demoButton: {
    marginTop: 10,
    paddingVertical: 5,
    borderColor: '#2E7D32',
  },
  linksContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 15,
  },
  linkButton: {
    marginHorizontal: 0,
  },
  footer: {
    marginTop: 30,
    alignItems: 'center',
  },
  footerText: {
    color: '#999',
    fontSize: 12,
  },
});
