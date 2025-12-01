/**
 * Button Component Tests
 * اختبارات مكون الزر
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import Button from '../Button';

describe('Button Component', () => {
  describe('Rendering', () => {
    it('should render correctly with title', () => {
      const { getByText } = render(
        <Button title="Test Button" onPress={() => {}} />
      );
      expect(getByText('Test Button')).toBeTruthy();
    });

    it('should render with different variants', () => {
      const { rerender, getByA11yRole } = render(
        <Button title="Test" onPress={() => {}} variant="contained" />
      );
      expect(getByA11yRole('button')).toBeTruthy();

      rerender(<Button title="Test" onPress={() => {}} variant="outlined" />);
      expect(getByA11yRole('button')).toBeTruthy();

      rerender(<Button title="Test" onPress={() => {}} variant="text" />);
      expect(getByA11yRole('button')).toBeTruthy();
    });

    it('should render with different colors', () => {
      const colors = ['primary', 'secondary', 'success', 'error', 'warning'] as const;

      colors.forEach((color) => {
        const { getByText } = render(
          <Button title={`${color} Button`} onPress={() => {}} color={color} />
        );
        expect(getByText(`${color} Button`)).toBeTruthy();
      });
    });

    it('should render with different sizes', () => {
      const sizes = ['small', 'medium', 'large'] as const;

      sizes.forEach((size) => {
        const { getByText } = render(
          <Button title={`${size} Button`} onPress={() => {}} size={size} />
        );
        expect(getByText(`${size} Button`)).toBeTruthy();
      });
    });

    it('should render loading state', () => {
      const { getByA11yState } = render(
        <Button title="Loading" onPress={() => {}} loading={true} />
      );

      const button = getByA11yState({ busy: true });
      expect(button).toBeTruthy();
    });

    it('should render disabled state', () => {
      const { getByA11yState } = render(
        <Button title="Disabled" onPress={() => {}} disabled={true} />
      );

      const button = getByA11yState({ disabled: true });
      expect(button).toBeTruthy();
    });
  });

  describe('Interactions', () => {
    it('should handle onPress events', () => {
      const onPress = jest.fn();
      const { getByText } = render(
        <Button title="Press Me" onPress={onPress} />
      );

      fireEvent.press(getByText('Press Me'));
      expect(onPress).toHaveBeenCalledTimes(1);
    });

    it('should not trigger onPress when disabled', () => {
      const onPress = jest.fn();
      const { getByText } = render(
        <Button title="Disabled" onPress={onPress} disabled={true} />
      );

      fireEvent.press(getByText('Disabled'));
      expect(onPress).not.toHaveBeenCalled();
    });

    it('should not trigger onPress when loading', () => {
      const onPress = jest.fn();
      const { getByA11yRole } = render(
        <Button title="Loading" onPress={onPress} loading={true} />
      );

      const button = getByA11yRole('button');
      fireEvent.press(button);
      expect(onPress).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have correct accessibility role', () => {
      const { getByA11yRole } = render(
        <Button title="Test" onPress={() => {}} />
      );

      expect(getByA11yRole('button')).toBeTruthy();
    });

    it('should use title as accessibility label by default', () => {
      const { getByA11yLabel } = render(
        <Button title="Test Button" onPress={() => {}} />
      );

      expect(getByA11yLabel('Test Button')).toBeTruthy();
    });

    it('should use custom accessibility label when provided', () => {
      const { getByA11yLabel } = render(
        <Button
          title="Test"
          onPress={() => {}}
          accessibilityLabel="Custom Label"
        />
      );

      expect(getByA11yLabel('Custom Label')).toBeTruthy();
    });

    it('should have accessibility hint when provided', () => {
      const { getByA11yHint } = render(
        <Button
          title="Test"
          onPress={() => {}}
          accessibilityHint="Press to submit"
        />
      );

      expect(getByA11yHint('Press to submit')).toBeTruthy();
    });

    it('should update accessibility state when disabled', () => {
      const { getByA11yState } = render(
        <Button title="Test" onPress={() => {}} disabled={true} />
      );

      const button = getByA11yState({ disabled: true });
      expect(button).toBeTruthy();
    });

    it('should update accessibility state when loading', () => {
      const { getByA11yState } = render(
        <Button title="Test" onPress={() => {}} loading={true} />
      );

      const button = getByA11yState({ busy: true, disabled: true });
      expect(button).toBeTruthy();
    });
  });

  describe('Styling', () => {
    it('should apply custom styles', () => {
      const customStyle = { marginTop: 20 };
      const { getByA11yRole } = render(
        <Button title="Test" onPress={() => {}} style={customStyle} />
      );

      const button = getByA11yRole('button');
      expect(button.props.style).toContainEqual(customStyle);
    });

    it('should render full width when specified', () => {
      const { getByA11yRole } = render(
        <Button title="Test" onPress={() => {}} fullWidth={true} />
      );

      const button = getByA11yRole('button');
      expect(button).toBeTruthy();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty title gracefully', () => {
      const { getByA11yRole } = render(
        <Button title="" onPress={() => {}} />
      );

      expect(getByA11yRole('button')).toBeTruthy();
    });

    it('should handle very long titles', () => {
      const longTitle = 'A'.repeat(100);
      const { getByText } = render(
        <Button title={longTitle} onPress={() => {}} />
      );

      expect(getByText(longTitle)).toBeTruthy();
    });

    it('should handle rapid press events', () => {
      const onPress = jest.fn();
      const { getByText } = render(
        <Button title="Test" onPress={onPress} />
      );

      const button = getByText('Test');
      fireEvent.press(button);
      fireEvent.press(button);
      fireEvent.press(button);

      expect(onPress).toHaveBeenCalledTimes(3);
    });
  });
});
