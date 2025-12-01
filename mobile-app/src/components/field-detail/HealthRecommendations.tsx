import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Card, Text } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

interface HealthRecommendationsProps {
  healthScore: number;
}

export default function HealthRecommendations({
  healthScore,
}: HealthRecommendationsProps) {
  const getRecommendation = () => {
    if (healthScore >= 80) {
      return {
        icon: 'check-circle',
        color: '#4CAF50',
        text: 'الحقل في حالة صحية ممتازة. استمر في المراقبة المنتظمة.',
      };
    } else if (healthScore >= 60) {
      return {
        icon: 'alert-circle',
        color: '#FFC107',
        text: 'الحقل يحتاج إلى اهتمام. تحقق من الري والتسميد.',
      };
    } else {
      return {
        icon: 'close-circle',
        color: '#F44336',
        text: 'تحذير: الحقل في حالة حرجة. يتطلب تدخل فوري.',
      };
    }
  };

  const recommendation = getRecommendation();

  return (
    <Card style={styles.card}>
      <Card.Content>
        <Text variant="titleMedium" style={styles.sectionTitle}>
          توصيات الصحة
        </Text>

        <View style={styles.recommendation}>
          <Icon name={recommendation.icon} size={24} color={recommendation.color} />
          <Text style={styles.recommendationText}>{recommendation.text}</Text>
        </View>
      </Card.Content>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    margin: 16,
    marginTop: 0,
    elevation: 2,
    borderRadius: 12,
  },
  sectionTitle: {
    fontWeight: 'bold',
    marginBottom: 16,
  },
  recommendation: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    padding: 12,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
  },
  recommendationText: {
    flex: 1,
    color: '#666',
    lineHeight: 20,
  },
});
