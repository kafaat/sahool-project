/**
 * Card Component Tests
 * اختبارات مكون البطاقة
 */

import React from 'react';
import { Text } from 'react-native';
import { render, fireEvent } from '@testing-library/react-native';
import Card from '../Card';

describe('Card Component', () => {
  describe('Rendering', () => {
    it('should render children correctly', () => {
      const { getByText } = render(
        <Card>
          <Text>Test Content</Text>
        </Card>
      );

      expect(getByText('Test Content')).toBeTruthy();
    });

    it('should render with different elevations', () => {
      const elevations = ['sm', 'md', 'lg', 'xl'] as const;

      elevations.forEach((elevation) => {
        const { getByText } = render(
          <Card elevation={elevation}>
            <Text>{elevation}</Text>
          </Card>
        );
        expect(getByText(elevation)).toBeTruthy();
      });
    });

    it('should render with different variants', () => {
      const variants = ['elevated', 'outlined', 'filled'] as const;

      variants.forEach((variant) => {
        const { getByText } = render(
          <Card variant={variant}>
            <Text>{variant}</Text>
          </Card>
        );
        expect(getByText(variant)).toBeTruthy();
      });
    });

    it('should render with different rounded values', () => {
      const roundedValues = ['sm', 'md', 'lg', 'xl'] as const;

      roundedValues.forEach((rounded) => {
        const { getByText } = render(
          <Card rounded={rounded}>
            <Text>{rounded}</Text>
          </Card>
        );
        expect(getByText(rounded)).toBeTruthy();
      });
    });
  });

  describe('Pressable Functionality', () => {
    it('should handle onPress events when pressable', () => {
      const onPress = jest.fn();
      const { getByA11yRole } = render(
        <Card pressable={true} onPress={onPress}>
          <Text>Pressable Card</Text>
        </Card>
      );

      const button = getByA11yRole('button');
      fireEvent.press(button);
      expect(onPress).toHaveBeenCalledTimes(1);
    });

    it('should be pressable when onPress is provided', () => {
      const onPress = jest.fn();
      const { getByA11yRole } = render(
        <Card onPress={onPress}>
          <Text>Card with onPress</Text>
        </Card>
      );

      const button = getByA11yRole('button');
      fireEvent.press(button);
      expect(onPress).toHaveBeenCalledTimes(1);
    });

    it('should not be pressable by default', () => {
      const { queryByA11yRole } = render(
        <Card>
          <Text>Non-pressable Card</Text>
        </Card>
      );

      const button = queryByA11yRole('button');
      expect(button).toBeNull();
    });
  });

  describe('Accessibility', () => {
    it('should have button role when pressable', () => {
      const { getByA11yRole } = render(
        <Card pressable={true} onPress={() => {}}>
          <Text>Pressable</Text>
        </Card>
      );

      expect(getByA11yRole('button')).toBeTruthy();
    });

    it('should use custom accessibility label when provided', () => {
      const { getByA11yLabel } = render(
        <Card
          pressable={true}
          onPress={() => {}}
          accessibilityLabel="Custom Card Label"
        >
          <Text>Content</Text>
        </Card>
      );

      expect(getByA11yLabel('Custom Card Label')).toBeTruthy();
    });

    it('should have accessibility hint when provided', () => {
      const { getByA11yHint } = render(
        <Card
          pressable={true}
          onPress={() => {}}
          accessibilityHint="Tap to view details"
        >
          <Text>Content</Text>
        </Card>
      );

      expect(getByA11yHint('Tap to view details')).toBeTruthy();
    });

    it('should use custom accessibility role when provided', () => {
      const { getByA11yRole } = render(
        <Card accessibilityLabel="Header" accessibilityRole="header">
          <Text>Header Content</Text>
        </Card>
      );

      expect(getByA11yRole('header')).toBeTruthy();
    });

    it('should not be accessible when no label and not pressable', () => {
      const { queryByA11yLabel } = render(
        <Card>
          <Text>Regular Card</Text>
        </Card>
      );

      // Card should not have accessibility label by default
      expect(queryByA11yLabel('Regular Card')).toBeNull();
    });
  });

  describe('Styling', () => {
    it('should apply custom styles', () => {
      const customStyle = { marginTop: 20, backgroundColor: 'red' };
      const { getByText } = render(
        <Card style={customStyle}>
          <Text>Styled Card</Text>
        </Card>
      );

      const card = getByText('Styled Card').parent;
      expect(card?.props.style).toContainEqual(customStyle);
    });
  });

  describe('Animation', () => {
    it('should handle press in animation', () => {
      const onPress = jest.fn();
      const { getByA11yRole } = render(
        <Card onPress={onPress}>
          <Text>Animated Card</Text>
        </Card>
      );

      const button = getByA11yRole('button');
      fireEvent(button, 'pressIn');
      fireEvent(button, 'pressOut');

      // Animation should complete without errors
      expect(button).toBeTruthy();
    });
  });

  describe('Edge Cases', () => {
    it('should handle null children gracefully', () => {
      const { container } = render(
        <Card>
          {null}
        </Card>
      );

      expect(container).toBeTruthy();
    });

    it('should handle multiple children', () => {
      const { getByText } = render(
        <Card>
          <Text>Child 1</Text>
          <Text>Child 2</Text>
          <Text>Child 3</Text>
        </Card>
      );

      expect(getByText('Child 1')).toBeTruthy();
      expect(getByText('Child 2')).toBeTruthy();
      expect(getByText('Child 3')).toBeTruthy();
    });

    it('should handle rapid press events', () => {
      const onPress = jest.fn();
      const { getByA11yRole } = render(
        <Card onPress={onPress}>
          <Text>Test</Text>
        </Card>
      );

      const button = getByA11yRole('button');
      fireEvent.press(button);
      fireEvent.press(button);
      fireEvent.press(button);

      expect(onPress).toHaveBeenCalledTimes(3);
    });
  });

  describe('Component Integration', () => {
    it('should work with complex nested content', () => {
      const { getByText } = render(
        <Card>
          <Text>Title</Text>
          <Card>
            <Text>Nested Card</Text>
          </Card>
        </Card>
      );

      expect(getByText('Title')).toBeTruthy();
      expect(getByText('Nested Card')).toBeTruthy();
    });
  });
});
