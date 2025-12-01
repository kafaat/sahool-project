/**
 * Brute Force Protection
 * حماية من هجمات القوة الغاشمة على تسجيل الدخول
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import DeviceInfo from 'react-native-device-info';

interface LoginAttempt {
  count: number;
  lastAttempt: number;
  lockedUntil?: number;
}

export class BruteForceProtection {
  private static readonly MAX_ATTEMPTS = 5;
  private static readonly LOCKOUT_DURATION = 15 * 60 * 1000; // 15 minutes
  private static readonly STORAGE_KEY_PREFIX = '@sahool_login_attempts_';

  /**
   * Get device identifier for tracking attempts
   */
  private static async getDeviceId(): Promise<string> {
    try {
      return await DeviceInfo.getUniqueId();
    } catch {
      // Fallback to a stored identifier
      let deviceId = await AsyncStorage.getItem('@sahool_device_id');
      if (!deviceId) {
        deviceId = `web_${Date.now()}_${Math.random()}`;
        await AsyncStorage.setItem('@sahool_device_id', deviceId);
      }
      return deviceId;
    }
  }

  /**
   * Get storage key for a specific email
   */
  private static async getStorageKey(email: string): Promise<string> {
    const deviceId = await this.getDeviceId();
    return `${this.STORAGE_KEY_PREFIX}${deviceId}:${email}`;
  }

  /**
   * Get login attempts for an email
   */
  private static async getAttempts(email: string): Promise<LoginAttempt> {
    try {
      const key = await this.getStorageKey(email);
      const data = await AsyncStorage.getItem(key);

      if (!data) {
        return { count: 0, lastAttempt: Date.now() };
      }

      return JSON.parse(data);
    } catch {
      return { count: 0, lastAttempt: Date.now() };
    }
  }

  /**
   * Save login attempts for an email
   */
  private static async saveAttempts(
    email: string,
    attempts: LoginAttempt
  ): Promise<void> {
    const key = await this.getStorageKey(email);
    await AsyncStorage.setItem(key, JSON.stringify(attempts));
  }

  /**
   * Check if login attempt is allowed
   * Returns { allowed: boolean, remainingAttempts?: number, lockedUntil?: Date, message?: string }
   */
  static async checkRateLimit(email: string): Promise<{
    allowed: boolean;
    remainingAttempts?: number;
    lockedUntil?: Date;
    message?: string;
  }> {
    const attempts = await this.getAttempts(email);

    // Check if account is locked
    if (attempts.lockedUntil && Date.now() < attempts.lockedUntil) {
      const remainingTime = Math.ceil(
        (attempts.lockedUntil - Date.now()) / 60000
      );

      return {
        allowed: false,
        lockedUntil: new Date(attempts.lockedUntil),
        message: `الحساب مقفل مؤقتاً. حاول مرة أخرى بعد ${remainingTime} دقيقة`,
      };
    }

    // Check if max attempts reached
    if (attempts.count >= this.MAX_ATTEMPTS) {
      const timeSinceLastAttempt = Date.now() - attempts.lastAttempt;

      if (timeSinceLastAttempt < this.LOCKOUT_DURATION) {
        // Lock the account
        const lockedUntil = attempts.lastAttempt + this.LOCKOUT_DURATION;
        await this.saveAttempts(email, {
          ...attempts,
          lockedUntil,
        });

        const remainingTime = Math.ceil(
          (lockedUntil - Date.now()) / 60000
        );

        return {
          allowed: false,
          lockedUntil: new Date(lockedUntil),
          message: `محاولات كثيرة خاطئة. حاول مرة أخرى بعد ${remainingTime} دقيقة`,
        };
      } else {
        // Reset attempts after lockout duration
        await this.saveAttempts(email, { count: 0, lastAttempt: Date.now() });
      }
    }

    return {
      allowed: true,
      remainingAttempts: this.MAX_ATTEMPTS - attempts.count,
    };
  }

  /**
   * Record a failed login attempt
   */
  static async recordFailedAttempt(email: string): Promise<void> {
    const attempts = await this.getAttempts(email);

    await this.saveAttempts(email, {
      count: attempts.count + 1,
      lastAttempt: Date.now(),
    });
  }

  /**
   * Clear login attempts after successful login
   */
  static async clearAttempts(email: string): Promise<void> {
    const key = await this.getStorageKey(email);
    await AsyncStorage.removeItem(key);
  }

  /**
   * Get remaining attempts before lockout
   */
  static async getRemainingAttempts(email: string): Promise<number> {
    const attempts = await this.getAttempts(email);
    return Math.max(0, this.MAX_ATTEMPTS - attempts.count);
  }
}

// ============================================================================
// Usage Example in LoginScreen
// ============================================================================

/*
import { BruteForceProtection } from '../utils/BruteForceProtection';

const handleLogin = async () => {
  if (!email || !password) {
    Alert.alert('خطأ', 'الرجاء إدخال البريد الإلكتروني وكلمة المرور');
    return;
  }

  // Check rate limit
  const rateLimitCheck = await BruteForceProtection.checkRateLimit(email);

  if (!rateLimitCheck.allowed) {
    Alert.alert('خطأ', rateLimitCheck.message || 'محاولات كثيرة');
    return;
  }

  setLoading(true);

  try {
    const response = await login(email, password);

    // Clear attempts on successful login
    await BruteForceProtection.clearAttempts(email);

    // Save token and navigate
    await AsyncStorage.setItem('userToken', response.token);
    navigation.replace('Main');

  } catch (error: any) {
    // Record failed attempt
    await BruteForceProtection.recordFailedAttempt(email);

    // Get remaining attempts
    const remaining = await BruteForceProtection.getRemainingAttempts(email);

    let message = error.response?.data?.detail || 'فشل تسجيل الدخول';

    if (remaining > 0) {
      message += `\n\nمحاولات متبقية: ${remaining}`;
    }

    Alert.alert('خطأ في تسجيل الدخول', message);

  } finally {
    setLoading(false);
  }
};
*/
