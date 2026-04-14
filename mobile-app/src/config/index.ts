// App Configuration
export const APP_CONFIG = {
  // App Info
  name: 'سهول',
  nameEn: 'Sahool',
  version: '1.0.0',
  description: 'منصة سهول الزراعية الذكية',

  // API Configuration
  api: {
    baseUrl: process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000',
    timeout: 10000,
    version: 'v1',
  },

  // Map Configuration
  map: {
    defaultRegion: {
      latitude: 15.3694,
      longitude: 44.191,
      latitudeDelta: 5,
      longitudeDelta: 5,
    },
    yemen: {
      north: 19.0,
      south: 12.0,
      east: 54.0,
      west: 42.0,
    },
  },

  // NDVI Configuration
  ndvi: {
    thresholds: {
      veryHigh: 0.7,
      high: 0.5,
      moderate: 0.3,
      low: 0.1,
    },
    colors: {
      veryHigh: '#1B5E20',
      high: '#4CAF50',
      moderate: '#8BC34A',
      low: '#CDDC39',
      veryLow: '#FFC107',
    },
    labels: {
      veryHigh: 'نباتات كثيفة',
      high: 'نباتات صحية',
      moderate: 'نباتات معتدلة',
      low: 'نباتات ضعيفة',
      veryLow: 'تربة عارية',
    },
  },

  // Theme Colors
  colors: {
    primary: '#2E7D32',
    primaryDark: '#1B5E20',
    primaryLight: '#4CAF50',
    secondary: '#1976D2',
    accent: '#FF5722',
    success: '#4CAF50',
    warning: '#FF9800',
    error: '#F44336',
    info: '#2196F3',
    background: '#F5F5F5',
    surface: '#FFFFFF',
    text: '#212121',
    textSecondary: '#757575',
    border: '#E0E0E0',
  },

  // Supported Crops in Yemen
  crops: [
    { id: 'wheat', name: 'قمح', nameEn: 'Wheat' },
    { id: 'barley', name: 'شعير', nameEn: 'Barley' },
    { id: 'sorghum', name: 'ذرة رفيعة', nameEn: 'Sorghum' },
    { id: 'millet', name: 'دخن', nameEn: 'Millet' },
    { id: 'maize', name: 'ذرة شامية', nameEn: 'Maize' },
    { id: 'coffee', name: 'بن', nameEn: 'Coffee' },
    { id: 'qat', name: 'قات', nameEn: 'Qat' },
    { id: 'grapes', name: 'عنب', nameEn: 'Grapes' },
    { id: 'mango', name: 'مانجو', nameEn: 'Mango' },
    { id: 'banana', name: 'موز', nameEn: 'Banana' },
    { id: 'papaya', name: 'بابايا', nameEn: 'Papaya' },
    { id: 'citrus', name: 'حمضيات', nameEn: 'Citrus' },
    { id: 'vegetables', name: 'خضروات', nameEn: 'Vegetables' },
    { id: 'alfalfa', name: 'برسيم', nameEn: 'Alfalfa' },
    { id: 'sesame', name: 'سمسم', nameEn: 'Sesame' },
    { id: 'cotton', name: 'قطن', nameEn: 'Cotton' },
  ],

  // Yemen Regions
  regions: [
    { id: 'sanaa', name: 'صنعاء', nameEn: 'Sanaa' },
    { id: 'aden', name: 'عدن', nameEn: 'Aden' },
    { id: 'taiz', name: 'تعز', nameEn: 'Taiz' },
    { id: 'hodeidah', name: 'الحديدة', nameEn: 'Hodeidah' },
    { id: 'ibb', name: 'إب', nameEn: 'Ibb' },
    { id: 'dhamar', name: 'ذمار', nameEn: 'Dhamar' },
    { id: 'hajjah', name: 'حجة', nameEn: 'Hajjah' },
    { id: 'amran', name: 'عمران', nameEn: 'Amran' },
    { id: 'saada', name: 'صعدة', nameEn: 'Saada' },
    { id: 'marib', name: 'مأرب', nameEn: 'Marib' },
    { id: 'lahj', name: 'لحج', nameEn: 'Lahj' },
    { id: 'abyan', name: 'أبين', nameEn: 'Abyan' },
    { id: 'shabwa', name: 'شبوة', nameEn: 'Shabwa' },
    { id: 'hadramout', name: 'حضرموت', nameEn: 'Hadramout' },
    { id: 'al-mahrah', name: 'المهرة', nameEn: 'Al-Mahrah' },
    { id: 'al-jawf', name: 'الجوف', nameEn: 'Al-Jawf' },
    { id: 'al-bayda', name: 'البيضاء', nameEn: 'Al-Bayda' },
    { id: 'al-mahweet', name: 'المحويت', nameEn: 'Al-Mahweet' },
    { id: 'raymah', name: 'ريمة', nameEn: 'Raymah' },
    { id: 'al-dhale', name: 'الضالع', nameEn: 'Al-Dhale' },
    { id: 'socotra', name: 'سقطرى', nameEn: 'Socotra' },
  ],

  // Irrigation Types
  irrigationTypes: [
    { id: 'drip', name: 'تنقيط', nameEn: 'Drip' },
    { id: 'sprinkler', name: 'رش', nameEn: 'Sprinkler' },
    { id: 'flood', name: 'غمر', nameEn: 'Flood' },
    { id: 'furrow', name: 'أخدود', nameEn: 'Furrow' },
    { id: 'rainfed', name: 'بعلي', nameEn: 'Rainfed' },
    { id: 'well', name: 'بئر', nameEn: 'Well' },
  ],

  // Soil Types
  soilTypes: [
    { id: 'clay', name: 'طينية', nameEn: 'Clay' },
    { id: 'sandy', name: 'رملية', nameEn: 'Sandy' },
    { id: 'loamy', name: 'طميية', nameEn: 'Loamy' },
    { id: 'silt', name: 'غرينية', nameEn: 'Silt' },
    { id: 'rocky', name: 'صخرية', nameEn: 'Rocky' },
  ],

  // Storage Keys
  storageKeys: {
    authToken: 'authToken',
    refreshToken: 'refreshToken',
    user: 'user',
    settings: 'settings',
    onboardingComplete: 'onboardingComplete',
  },
};

export default APP_CONFIG;
