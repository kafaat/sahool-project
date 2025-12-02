/// Application configuration
/// Manages environment-specific settings
class AppConfig {
  /// API Base URL
  /// - Android Emulator: 10.0.2.2
  /// - iOS Simulator: localhost
  /// - Physical Device: Your server IP
  static const String defaultApiUrl = 'http://10.0.2.2:8000';

  /// Get API URL from environment or use default
  static String get apiBaseUrl {
    // In production, this could be loaded from:
    // - Environment variables (--dart-define=API_URL=...)
    // - Remote config
    // - Build flavors
    const envUrl = String.fromEnvironment('API_URL', defaultValue: '');
    return envUrl.isNotEmpty ? envUrl : defaultApiUrl;
  }

  /// API Timeout configurations
  static const Duration connectionTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 30);

  /// Retry configuration
  static const int maxRetries = 3;
  static const Duration retryDelay = Duration(seconds: 2);

  /// Feature flags
  static const bool enableOfflineMode = false;
  static const bool enableAnalytics = false;

  /// App metadata
  static const String appName = 'Field Suite';
  static const String appVersion = '2.1.0';
}
