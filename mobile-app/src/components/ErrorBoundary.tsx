/**
 * Error Boundary Component
 * مكون حدود الأخطاء - لمعالجة الأخطاء وحماية التطبيق من التعطل
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { Theme } from '../theme/design-system';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary Component
 * Catches JavaScript errors anywhere in the child component tree
 * and displays a fallback UI instead of the component tree that crashed.
 */
export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error details
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Update state with error information
    this.setState({
      error,
      errorInfo,
    });

    // Call optional error callback
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // In production, you would log this to an error reporting service
    // Example: Sentry.captureException(error, { extra: errorInfo });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI provided by parent
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <View style={styles.container}>
          <ScrollView
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
          >
            <View style={styles.iconContainer}>
              <Icon
                name="alert-circle-outline"
                size={80}
                color={Theme.colors.error.main}
              />
            </View>

            <Text style={styles.title}>حدث خطأ غير متوقع</Text>
            <Text style={styles.subtitle}>Something went wrong</Text>

            <Text style={styles.message}>
              نعتذر عن هذا الإزعاج. حدث خطأ أثناء تحميل هذا المحتوى.
            </Text>

            {__DEV__ && this.state.error && (
              <View style={styles.errorDetails}>
                <Text style={styles.errorTitle}>تفاصيل الخطأ (وضع التطوير):</Text>

                <View style={styles.errorBox}>
                  <Text style={styles.errorText}>
                    <Text style={styles.errorLabel}>Error: </Text>
                    {this.state.error.toString()}
                  </Text>
                </View>

                {this.state.errorInfo && (
                  <View style={styles.errorBox}>
                    <Text style={styles.errorText}>
                      <Text style={styles.errorLabel}>Component Stack:</Text>
                      {'\n'}
                      {this.state.errorInfo.componentStack}
                    </Text>
                  </View>
                )}
              </View>
            )}

            <Pressable
              style={({ pressed }) => [
                styles.button,
                pressed && styles.buttonPressed,
              ]}
              onPress={this.handleReset}
              accessible={true}
              accessibilityRole="button"
              accessibilityLabel="إعادة المحاولة"
              accessibilityHint="اضغط لإعادة تحميل المحتوى"
            >
              <Icon name="refresh" size={20} color="#FFFFFF" style={styles.buttonIcon} />
              <Text style={styles.buttonText}>إعادة المحاولة</Text>
            </Pressable>

            <Text style={styles.hint}>
              إذا استمرت المشكلة، يرجى الاتصال بالدعم الفني
            </Text>
          </ScrollView>
        </View>
      );
    }

    return this.props.children;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Theme.colors.background.default,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: Theme.spacing.xl,
  },
  iconContainer: {
    marginBottom: Theme.spacing.xl,
  },
  title: {
    fontSize: Theme.typography.fontSize['2xl'],
    fontWeight: Theme.typography.fontWeight.bold,
    color: Theme.colors.text.primary,
    textAlign: 'center',
    marginBottom: Theme.spacing.sm,
  },
  subtitle: {
    fontSize: Theme.typography.fontSize.md,
    color: Theme.colors.text.secondary,
    textAlign: 'center',
    marginBottom: Theme.spacing.xl,
  },
  message: {
    fontSize: Theme.typography.fontSize.base,
    color: Theme.colors.text.secondary,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: Theme.spacing.xl,
    paddingHorizontal: Theme.spacing.md,
  },
  errorDetails: {
    width: '100%',
    marginTop: Theme.spacing.xl,
    marginBottom: Theme.spacing.xl,
  },
  errorTitle: {
    fontSize: Theme.typography.fontSize.sm,
    fontWeight: Theme.typography.fontWeight.bold,
    color: Theme.colors.error.main,
    marginBottom: Theme.spacing.md,
  },
  errorBox: {
    backgroundColor: Theme.colors.error.light,
    borderLeftWidth: 4,
    borderLeftColor: Theme.colors.error.main,
    padding: Theme.spacing.md,
    borderRadius: Theme.borderRadius.md,
    marginBottom: Theme.spacing.md,
  },
  errorText: {
    fontSize: Theme.typography.fontSize.xs,
    color: Theme.colors.error.dark,
    fontFamily: 'monospace',
  },
  errorLabel: {
    fontWeight: Theme.typography.fontWeight.bold,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Theme.colors.primary.main,
    paddingHorizontal: Theme.spacing.xl,
    paddingVertical: Theme.spacing.md,
    borderRadius: Theme.borderRadius.button,
    minWidth: 200,
    marginBottom: Theme.spacing.lg,
    ...Theme.shadows.md,
  },
  buttonPressed: {
    backgroundColor: Theme.colors.primary.dark,
    transform: [{ scale: 0.98 }],
  },
  buttonIcon: {
    marginRight: Theme.spacing.sm,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: Theme.typography.fontSize.base,
    fontWeight: Theme.typography.fontWeight.medium,
  },
  hint: {
    fontSize: Theme.typography.fontSize.sm,
    color: Theme.colors.text.secondary,
    textAlign: 'center',
    fontStyle: 'italic',
  },
});
