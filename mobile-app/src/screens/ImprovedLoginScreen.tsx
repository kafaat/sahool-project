/**
 * Improved Login Screen
 * شاشة تسجيل الدخول المحسّنة
 *
 * Features:
 * - Professional agricultural branding (John Deere inspired)
 * - Clean, modern interface
 * - Brute force protection integrated
 * - Smooth animations
 * - Accessibility features
 */

import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  TextInput,
  Pressable,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Image,
} from 'react-native';
import { Text } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import Animated, { FadeInDown, FadeInUp } from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { Button, Card } from '../components/ui';
import { Theme } from '../theme/design-system';
import { BruteForceProtection } from '../utils/BruteForceProtection';

type ImprovedLoginScreenProps = {
  navigation: NativeStackNavigationProp<any>;
};

export default function ImprovedLoginScreen({ navigation }: ImprovedLoginScreenProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [focusedField, setFocusedField] = useState<'email' | 'password' | null>(null);

  const handleLogin = async () => {
    setError('');

    // Validation
    if (!email || !password) {
      setError('الرجاء إدخال البريد الإلكتروني وكلمة المرور');
      return;
    }

    // Check brute force protection
    const rateLimitCheck = await BruteForceProtection.checkRateLimit(email);
    if (!rateLimitCheck.allowed) {
      setError(rateLimitCheck.message || 'تم تجاوز عدد المحاولات');
      return;
    }

    setLoading(true);

    try {
      // Simulate API call
      await new Promise((resolve, reject) => {
        setTimeout(() => {
          // Simulate success for demo@example.com
          if (email === 'demo@example.com' && password === 'demo123') {
            resolve(true);
          } else {
            reject(new Error('بيانات الدخول غير صحيحة'));
          }
        }, 1500);
      });

      // Clear attempts on success
      await BruteForceProtection.clearAttempts(email);

      // Navigate to main app
      navigation.replace('Main');
    } catch (err: any) {
      // Record failed attempt
      await BruteForceProtection.recordFailedAttempt(email);

      const remaining = await BruteForceProtection.getRemainingAttempts(email);
      setError(`${err.message}. المحاولات المتبقية: ${remaining}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header with Gradient */}
        <Animated.View entering={FadeInDown.delay(100)} style={styles.headerContainer}>
          <LinearGradient
            colors={[Theme.colors.johnDeere.green, Theme.colors.johnDeere.darkGreen]}
            style={styles.headerGradient}
          >
            {/* Logo */}
            <View style={styles.logoContainer}>
              <View style={styles.logoCircle}>
                <Icon name="sprout" size={48} color={Theme.colors.johnDeere.yellow} />
              </View>
            </View>

            <Text style={styles.appName}>Sahool</Text>
            <Text style={styles.tagline}>المنصة الزراعية الذكية</Text>
          </LinearGradient>
        </Animated.View>

        {/* Login Card */}
        <Animated.View entering={FadeInUp.delay(200)} style={styles.cardContainer}>
          <Card elevation="lg" rounded="xl" style={styles.loginCard}>
            <Text style={styles.welcomeText}>مرحباً بعودتك! 👋</Text>
            <Text style={styles.subtitleText}>
              سجّل الدخول للوصول إلى حقولك ومزارعك
            </Text>

            {/* Error Message */}
            {error ? (
              <Animated.View entering={FadeInDown} style={styles.errorContainer}>
                <Icon name="alert-circle" size={20} color={Theme.colors.error.main} />
                <Text style={styles.errorText}>{error}</Text>
              </Animated.View>
            ) : null}

            {/* Email Input */}
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>البريد الإلكتروني</Text>
              <View
                style={[
                  styles.inputWrapper,
                  focusedField === 'email' && styles.inputWrapperFocused,
                  error && styles.inputWrapperError,
                ]}
              >
                <Icon
                  name="email-outline"
                  size={20}
                  color={
                    focusedField === 'email'
                      ? Theme.colors.johnDeere.green
                      : Theme.colors.gray[500]
                  }
                />
                <TextInput
                  style={styles.input}
                  placeholder="example@email.com"
                  placeholderTextColor={Theme.colors.gray[400]}
                  value={email}
                  onChangeText={setEmail}
                  onFocus={() => setFocusedField('email')}
                  onBlur={() => setFocusedField(null)}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </View>
            </View>

            {/* Password Input */}
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>كلمة المرور</Text>
              <View
                style={[
                  styles.inputWrapper,
                  focusedField === 'password' && styles.inputWrapperFocused,
                  error && styles.inputWrapperError,
                ]}
              >
                <Icon
                  name="lock-outline"
                  size={20}
                  color={
                    focusedField === 'password'
                      ? Theme.colors.johnDeere.green
                      : Theme.colors.gray[500]
                  }
                />
                <TextInput
                  style={[styles.input, { flex: 1 }]}
                  placeholder="••••••••"
                  placeholderTextColor={Theme.colors.gray[400]}
                  value={password}
                  onChangeText={setPassword}
                  onFocus={() => setFocusedField('password')}
                  onBlur={() => setFocusedField(null)}
                  secureTextEntry={!showPassword}
                  autoCapitalize="none"
                />
                <Pressable onPress={() => setShowPassword(!showPassword)}>
                  <Icon
                    name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                    size={20}
                    color={Theme.colors.gray[500]}
                  />
                </Pressable>
              </View>
            </View>

            {/* Forgot Password */}
            <Pressable onPress={() => alert('سيتم إضافة ميزة استعادة كلمة المرور قريباً')}>
              <Text style={styles.forgotPassword}>نسيت كلمة المرور؟</Text>
            </Pressable>

            {/* Login Button */}
            <View style={styles.buttonContainer}>
              <Pressable onPress={handleLogin} disabled={loading} style={styles.loginButton}>
                <LinearGradient
                  colors={[Theme.colors.johnDeere.green, Theme.colors.johnDeere.darkGreen]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.loginButtonGradient}
                >
                  {loading ? (
                    <Icon name="loading" size={24} color="#fff" />
                  ) : (
                    <>
                      <Text style={styles.loginButtonText}>تسجيل الدخول</Text>
                      <Icon name="arrow-left" size={20} color="#fff" />
                    </>
                  )}
                </LinearGradient>
              </Pressable>
            </View>

            {/* Divider */}
            <View style={styles.divider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>أو</Text>
              <View style={styles.dividerLine} />
            </View>

            {/* Social Login */}
            <View style={styles.socialContainer}>
              <Pressable style={styles.socialButton}>
                <Icon name="google" size={24} color="#DB4437" />
              </Pressable>
              <Pressable style={styles.socialButton}>
                <Icon name="facebook" size={24} color="#4267B2" />
              </Pressable>
              <Pressable style={styles.socialButton}>
                <Icon name="apple" size={24} color="#000" />
              </Pressable>
            </View>

            {/* Sign Up */}
            <View style={styles.signupContainer}>
              <Text style={styles.signupText}>ليس لديك حساب؟ </Text>
              <Pressable onPress={() => alert('سيتم إضافة ميزة التسجيل قريباً')}>
                <Text style={styles.signupLink}>إنشاء حساب جديد</Text>
              </Pressable>
            </View>
          </Card>
        </Animated.View>

        {/* Features */}
        <Animated.View entering={FadeInUp.delay(300)} style={styles.featuresContainer}>
          <View style={styles.featureItem}>
            <Icon name="shield-check" size={20} color={Theme.colors.johnDeere.green} />
            <Text style={styles.featureText}>آمن ومشفّر</Text>
          </View>
          <View style={styles.featureItem}>
            <Icon name="cloud-sync" size={20} color={Theme.colors.johnDeere.green} />
            <Text style={styles.featureText}>مزامنة سحابية</Text>
          </View>
          <View style={styles.featureItem}>
            <Icon name="cellphone-link" size={20} color={Theme.colors.johnDeere.green} />
            <Text style={styles.featureText}>وصول من أي مكان</Text>
          </View>
        </Animated.View>

        {/* Demo Credentials */}
        <Animated.View entering={FadeInUp.delay(400)} style={styles.demoContainer}>
          <View style={styles.demoCard}>
            <Icon name="information-outline" size={20} color={Theme.colors.info.main} />
            <View style={styles.demoTextContainer}>
              <Text style={styles.demoTitle}>حساب تجريبي:</Text>
              <Text style={styles.demoCredentials}>demo@example.com / demo123</Text>
            </View>
          </View>
        </Animated.View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>© 2025 Sahool. جميع الحقوق محفوظة</Text>
          <View style={styles.footerLinks}>
            <Pressable>
              <Text style={styles.footerLink}>الشروط والأحكام</Text>
            </Pressable>
            <Text style={styles.footerSeparator}>•</Text>
            <Pressable>
              <Text style={styles.footerLink}>سياسة الخصوصية</Text>
            </Pressable>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Theme.colors.background.default,
  },
  scrollContent: {
    flexGrow: 1,
  },
  headerContainer: {
    marginBottom: -40,
  },
  headerGradient: {
    paddingTop: Theme.spacing['4xl'],
    paddingBottom: Theme.spacing['5xl'],
    alignItems: 'center',
    borderBottomLeftRadius: Theme.borderRadius['3xl'],
    borderBottomRightRadius: Theme.borderRadius['3xl'],
  },
  logoContainer: {
    marginBottom: Theme.spacing.lg,
  },
  logoCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: Theme.colors.johnDeere.yellow,
  },
  appName: {
    ...Theme.typography.styles.h1,
    color: '#fff',
    marginBottom: Theme.spacing.xs,
    fontWeight: '800',
  },
  tagline: {
    ...Theme.typography.styles.body1,
    color: 'rgba(255, 255, 255, 0.9)',
  },
  cardContainer: {
    padding: Theme.spacing.lg,
  },
  loginCard: {
    padding: Theme.spacing.xl,
  },
  welcomeText: {
    ...Theme.typography.styles.h2,
    color: Theme.colors.text.primary,
    marginBottom: Theme.spacing.xs,
  },
  subtitleText: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.text.secondary,
    marginBottom: Theme.spacing.xl,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.sm,
    backgroundColor: Theme.colors.error.light + '20',
    padding: Theme.spacing.md,
    borderRadius: Theme.borderRadius.lg,
    marginBottom: Theme.spacing.md,
    borderLeftWidth: 4,
    borderLeftColor: Theme.colors.error.main,
  },
  errorText: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.error.dark,
    flex: 1,
  },
  inputContainer: {
    marginBottom: Theme.spacing.lg,
  },
  inputLabel: {
    ...Theme.typography.styles.body2,
    fontWeight: '600',
    color: Theme.colors.text.primary,
    marginBottom: Theme.spacing.sm,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Theme.colors.gray[50],
    borderRadius: Theme.borderRadius.lg,
    paddingHorizontal: Theme.spacing.md,
    gap: Theme.spacing.sm,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  inputWrapperFocused: {
    borderColor: Theme.colors.johnDeere.green,
    backgroundColor: '#fff',
    ...Theme.shadows.sm,
  },
  inputWrapperError: {
    borderColor: Theme.colors.error.main,
  },
  input: {
    flex: 1,
    paddingVertical: Theme.spacing.md,
    ...Theme.typography.styles.body1,
    color: Theme.colors.text.primary,
  },
  forgotPassword: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.johnDeere.green,
    textAlign: 'left',
    marginBottom: Theme.spacing.xl,
    fontWeight: '600',
  },
  buttonContainer: {
    marginBottom: Theme.spacing.lg,
  },
  loginButton: {
    borderRadius: Theme.borderRadius.lg,
    overflow: 'hidden',
    ...Theme.shadows.md,
  },
  loginButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: Theme.spacing.sm,
    paddingVertical: Theme.spacing.lg,
  },
  loginButtonText: {
    ...Theme.typography.styles.h4,
    color: '#fff',
    fontWeight: '600',
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: Theme.spacing.lg,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: Theme.colors.gray[300],
  },
  dividerText: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.text.secondary,
    marginHorizontal: Theme.spacing.md,
  },
  socialContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: Theme.spacing.md,
    marginBottom: Theme.spacing.lg,
  },
  socialButton: {
    width: 56,
    height: 56,
    borderRadius: Theme.borderRadius.lg,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Theme.colors.gray[300],
    ...Theme.shadows.sm,
  },
  signupContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  signupText: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.text.secondary,
  },
  signupLink: {
    ...Theme.typography.styles.body2,
    color: Theme.colors.johnDeere.green,
    fontWeight: '600',
  },
  featuresContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: Theme.spacing.lg,
    paddingVertical: Theme.spacing.xl,
  },
  featureItem: {
    alignItems: 'center',
    gap: Theme.spacing.xs,
  },
  featureText: {
    ...Theme.typography.styles.caption,
    color: Theme.colors.text.secondary,
  },
  demoContainer: {
    paddingHorizontal: Theme.spacing.lg,
    marginBottom: Theme.spacing.xl,
  },
  demoCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.md,
    backgroundColor: Theme.colors.info.light + '20',
    padding: Theme.spacing.md,
    borderRadius: Theme.borderRadius.lg,
    borderLeftWidth: 4,
    borderLeftColor: Theme.colors.info.main,
  },
  demoTextContainer: {
    flex: 1,
  },
  demoTitle: {
    ...Theme.typography.styles.body2,
    fontWeight: '600',
    color: Theme.colors.text.primary,
  },
  demoCredentials: {
    ...Theme.typography.styles.caption,
    color: Theme.colors.text.secondary,
    fontFamily: Theme.typography.fontFamily.mono,
  },
  footer: {
    alignItems: 'center',
    padding: Theme.spacing.xl,
    gap: Theme.spacing.sm,
  },
  footerText: {
    ...Theme.typography.styles.caption,
    color: Theme.colors.text.disabled,
  },
  footerLinks: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.sm,
  },
  footerLink: {
    ...Theme.typography.styles.caption,
    color: Theme.colors.johnDeere.green,
  },
  footerSeparator: {
    ...Theme.typography.styles.caption,
    color: Theme.colors.text.disabled,
  },
});
