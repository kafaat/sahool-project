/**
 * Design System - Sahool Agricultural Platform
 * نظام التصميم الموحد للمنصة الزراعية
 *
 * This file contains all design tokens, colors, typography, spacing, and shadows
 * for consistent UI across the application.
 */

export const Colors = {
  // Primary Colors - الألوان الرئيسية
  primary: {
    50: '#E8F5E9',
    100: '#C8E6C9',
    200: '#A5D6A7',
    300: '#81C784',
    400: '#66BB6A',
    500: '#4CAF50',  // Main primary
    600: '#43A047',
    700: '#388E3C',
    800: '#2E7D32',
    900: '#1B5E20',
  },

  // Secondary Colors - الألوان الثانوية
  secondary: {
    50: '#FFF3E0',
    100: '#FFE0B2',
    200: '#FFCC80',
    300: '#FFB74D',
    400: '#FFA726',
    500: '#FF9800',  // Main secondary
    600: '#FB8C00',
    700: '#F57C00',
    800: '#EF6C00',
    900: '#E65100',
  },

  // Semantic Colors - الألوان الدلالية
  success: {
    light: '#81C784',
    main: '#4CAF50',
    dark: '#388E3C',
    contrastText: '#FFFFFF',
  },

  warning: {
    light: '#FFB74D',
    main: '#FF9800',
    dark: '#F57C00',
    contrastText: '#FFFFFF',
  },

  error: {
    light: '#E57373',
    main: '#F44336',
    dark: '#D32F2F',
    contrastText: '#FFFFFF',
  },

  info: {
    light: '#64B5F6',
    main: '#2196F3',
    dark: '#1976D2',
    contrastText: '#FFFFFF',
  },

  // Grayscale - الرمادي
  gray: {
    50: '#FAFAFA',
    100: '#F5F5F5',
    200: '#EEEEEE',
    300: '#E0E0E0',
    400: '#BDBDBD',
    500: '#9E9E9E',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121',
  },

  // Background Colors - ألوان الخلفية
  background: {
    default: '#FAFAFA',
    paper: '#FFFFFF',
    elevated: '#FFFFFF',
  },

  // Text Colors - ألوان النص
  text: {
    primary: 'rgba(0, 0, 0, 0.87)',
    secondary: 'rgba(0, 0, 0, 0.60)',
    disabled: 'rgba(0, 0, 0, 0.38)',
    hint: 'rgba(0, 0, 0, 0.38)',
  },

  // Agricultural Specific - ألوان زراعية محددة
  agricultural: {
    soil: '#8D6E63',
    water: '#03A9F4',
    crop: '#66BB6A',
    ndvi: {
      poor: '#D32F2F',
      moderate: '#FFA726',
      good: '#66BB6A',
      excellent: '#2E7D32',
    },
    health: {
      critical: '#D32F2F',
      warning: '#FF9800',
      good: '#66BB6A',
      excellent: '#4CAF50',
    },
  },

  // Dark Mode Colors - ألوان الوضع الداكن
  dark: {
    background: {
      default: '#121212',
      paper: '#1E1E1E',
      elevated: '#2C2C2C',
    },
    text: {
      primary: 'rgba(255, 255, 255, 0.87)',
      secondary: 'rgba(255, 255, 255, 0.60)',
      disabled: 'rgba(255, 255, 255, 0.38)',
      hint: 'rgba(255, 255, 255, 0.38)',
    },
  },
};

export const Typography = {
  // Font Families
  fontFamily: {
    primary: 'System',  // Default system font
    arabic: 'Cairo',     // Arabic font
    mono: 'Courier',     // Monospace for code/numbers
  },

  // Font Sizes
  fontSize: {
    xs: 10,
    sm: 12,
    base: 14,
    md: 16,
    lg: 18,
    xl: 20,
    '2xl': 24,
    '3xl': 30,
    '4xl': 36,
    '5xl': 48,
  },

  // Font Weights
  fontWeight: {
    light: '300',
    regular: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    extrabold: '800',
  },

  // Line Heights
  lineHeight: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.75,
    loose: 2,
  },

  // Text Styles - أنماط النص الجاهزة
  styles: {
    h1: {
      fontSize: 36,
      fontWeight: '700',
      lineHeight: 1.2,
    },
    h2: {
      fontSize: 30,
      fontWeight: '700',
      lineHeight: 1.3,
    },
    h3: {
      fontSize: 24,
      fontWeight: '600',
      lineHeight: 1.4,
    },
    h4: {
      fontSize: 20,
      fontWeight: '600',
      lineHeight: 1.4,
    },
    h5: {
      fontSize: 18,
      fontWeight: '500',
      lineHeight: 1.5,
    },
    h6: {
      fontSize: 16,
      fontWeight: '500',
      lineHeight: 1.5,
    },
    body1: {
      fontSize: 16,
      fontWeight: '400',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: 14,
      fontWeight: '400',
      lineHeight: 1.5,
    },
    subtitle1: {
      fontSize: 16,
      fontWeight: '500',
      lineHeight: 1.75,
    },
    subtitle2: {
      fontSize: 14,
      fontWeight: '500',
      lineHeight: 1.57,
    },
    caption: {
      fontSize: 12,
      fontWeight: '400',
      lineHeight: 1.66,
    },
    overline: {
      fontSize: 10,
      fontWeight: '400',
      lineHeight: 2.66,
      textTransform: 'uppercase',
    },
    button: {
      fontSize: 14,
      fontWeight: '500',
      lineHeight: 1.75,
      textTransform: 'uppercase',
    },
  },
};

export const Spacing = {
  // Base spacing unit (4px)
  unit: 4,

  // Spacing scale - مقياس المسافات
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  '2xl': 40,
  '3xl': 48,
  '4xl': 64,
  '5xl': 80,

  // Padding presets - إعدادات Padding جاهزة
  padding: {
    xs: { padding: 4 },
    sm: { padding: 8 },
    md: { padding: 16 },
    lg: { padding: 24 },
    xl: { padding: 32 },
  },

  // Margin presets - إعدادات Margin جاهزة
  margin: {
    xs: { margin: 4 },
    sm: { margin: 8 },
    md: { margin: 16 },
    lg: { margin: 24 },
    xl: { margin: 32 },
  },
};

export const BorderRadius = {
  none: 0,
  xs: 2,
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  '2xl': 24,
  full: 9999,

  // Component-specific - خاص بالمكونات
  button: 8,
  card: 12,
  input: 8,
  modal: 16,
  chip: 16,
};

export const Shadows = {
  none: {
    shadowColor: 'transparent',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0,
    shadowRadius: 0,
    elevation: 0,
  },

  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.18,
    shadowRadius: 1.0,
    elevation: 1,
  },

  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.22,
    shadowRadius: 2.22,
    elevation: 3,
  },

  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.30,
    shadowRadius: 4.65,
    elevation: 8,
  },

  xl: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.37,
    shadowRadius: 7.49,
    elevation: 12,
  },

  '2xl': {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.51,
    shadowRadius: 13.16,
    elevation: 20,
  },
};

export const Animations = {
  // Duration - مدة الحركة
  duration: {
    fastest: 100,
    fast: 200,
    normal: 300,
    slow: 500,
    slowest: 700,
  },

  // Easing - منحنيات الحركة
  easing: {
    linear: 'linear',
    easeIn: 'ease-in',
    easeOut: 'ease-out',
    easeInOut: 'ease-in-out',
    spring: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  },
};

export const Layout = {
  // Container widths
  container: {
    sm: 640,
    md: 768,
    lg: 1024,
    xl: 1280,
  },

  // Screen breakpoints - نقاط التوقف
  breakpoints: {
    xs: 0,
    sm: 576,
    md: 768,
    lg: 992,
    xl: 1200,
  },

  // Header heights
  header: {
    sm: 56,
    md: 64,
    lg: 72,
  },

  // Footer heights
  footer: {
    sm: 48,
    md: 56,
  },
};

export const Opacities = {
  disabled: 0.38,
  hover: 0.04,
  selected: 0.08,
  focus: 0.12,
  activated: 0.12,
};

// Helper Functions - دوال مساعدة

/**
 * Get spacing value
 */
export const spacing = (multiplier: number): number => {
  return Spacing.unit * multiplier;
};

/**
 * Get color with opacity
 */
export const colorWithOpacity = (color: string, opacity: number): string => {
  // Convert hex to rgba
  const hex = color.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
};

/**
 * Get responsive value based on screen size
 */
export const responsive = <T,>(
  values: { sm?: T; md?: T; lg?: T; xl?: T },
  screenWidth: number
): T | undefined => {
  if (screenWidth >= Layout.breakpoints.xl && values.xl) return values.xl;
  if (screenWidth >= Layout.breakpoints.lg && values.lg) return values.lg;
  if (screenWidth >= Layout.breakpoints.md && values.md) return values.md;
  if (screenWidth >= Layout.breakpoints.sm && values.sm) return values.sm;
  return values.sm;
};

// Export all as Theme
export const Theme = {
  colors: Colors,
  typography: Typography,
  spacing: Spacing,
  borderRadius: BorderRadius,
  shadows: Shadows,
  animations: Animations,
  layout: Layout,
  opacities: Opacities,
};

export default Theme;
