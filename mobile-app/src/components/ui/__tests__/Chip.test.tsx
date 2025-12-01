/**
 * Chip Component Tests
 * اختبارات مكون الشريحة
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import Chip from '../Chip';

describe('Chip Component', () => {
  describe('Rendering', () => {
    it('should render label correctly', () => {
      const { getByText } = render(<Chip label="Test Chip" />);
      expect(getByText('Test Chip')).toBeTruthy();
    });

    it('should render with different variants', () => {
      const { getByText, rerender } = render(
        <Chip label="Filled" variant="filled" />
      );
      expect(getByText('Filled')).toBeTruthy();

      rerender(<Chip label="Outlined" variant="outlined" />);
      expect(getByText('Outlined')).toBeTruthy();
    });

    it('should render with different colors', () => {
      const colors = ['primary', 'secondary', 'success', 'error', 'warning', 'info', 'default'] as const;

      colors.forEach((color) => {
        const { getByText } = render(<Chip label={color} color={color} />);
        expect(getByText(color)).toBeTruthy();
      });
    });

    it('should render with different sizes', () => {
      const { getByText, rerender } = render(<Chip label="Small" size="small" />);
      expect(getByText('Small')).toBeTruthy();

      rerender(<Chip label="Medium" size="medium" />);
      expect(getByText('Medium')).toBeTruthy();
    });

    it('should render selected state', () => {
      const { getByA11yState } = render(
        <Chip label="Selected" selected={true} onPress={() => {}} />
      );

      const chip = getByA11yState({ selected: true });
      expect(chip).toBeTruthy();
    });

    it('should render disabled state', () => {
      const { getByA11yState } = render(
        <Chip label="Disabled" disabled={true} onPress={() => {}} />
      );

      const chip = getByA11yState({ disabled: true });
      expect(chip).toBeTruthy();
    });
  });

  describe('Interactions', () => {
    it('should handle onPress events', () => {
      const onPress = jest.fn();
      const { getByText } = render(<Chip label="Clickable" onPress={onPress} />);

      fireEvent.press(getByText('Clickable'));
      expect(onPress).toHaveBeenCalledTimes(1);
    });

    it('should handle onDelete events', () => {
      const onDelete = jest.fn();
      const { getByA11yLabel } = render(
        <Chip label="Deletable" onDelete={onDelete} />
      );

      const deleteButton = getByA11yLabel('حذف Deletable');
      fireEvent.press(deleteButton);
      expect(onDelete).toHaveBeenCalledTimes(1);
    });

    it('should not trigger onPress when disabled', () => {
      const onPress = jest.fn();
      const { getByA11yRole } = render(
        <Chip label="Disabled" onPress={onPress} disabled={true} />
      );

      const chip = getByA11yRole('button');
      fireEvent.press(chip);
      expect(onPress).not.toHaveBeenCalled();
    });

    it('should not trigger onDelete when disabled', () => {
      const onDelete = jest.fn();
      const { getByA11yLabel } = render(
        <Chip label="Test" onDelete={onDelete} disabled={true} />
      );

      const deleteButton = getByA11yLabel('حذف Test');
      fireEvent.press(deleteButton);
      expect(onDelete).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have button role when pressable', () => {
      const { getByA11yRole } = render(
        <Chip label="Test" onPress={() => {}} />
      );

      expect(getByA11yRole('button')).toBeTruthy();
    });

    it('should have text role when not pressable', () => {
      const { getByA11yRole } = render(<Chip label="Test" />);

      expect(getByA11yRole('text')).toBeTruthy();
    });

    it('should use label as accessibility label by default', () => {
      const { getByA11yLabel } = render(<Chip label="Test Label" />);

      expect(getByA11yLabel('Test Label')).toBeTruthy();
    });

    it('should use custom accessibility label when provided', () => {
      const { getByA11yLabel } = render(
        <Chip label="Test" accessibilityLabel="Custom Label" />
      );

      expect(getByA11yLabel('Custom Label')).toBeTruthy();
    });

    it('should have accessibility hint when provided', () => {
      const { getByA11yHint } = render(
        <Chip
          label="Test"
          onPress={() => {}}
          accessibilityHint="Press to filter"
        />
      );

      expect(getByA11yHint('Press to filter')).toBeTruthy();
    });

    it('should have default delete accessibility label', () => {
      const { getByA11yLabel } = render(
        <Chip label="Tag" onDelete={() => {}} />
      );

      expect(getByA11yLabel('حذف Tag')).toBeTruthy();
    });

    it('should use custom delete accessibility label', () => {
      const { getByA11yLabel } = render(
        <Chip
          label="Tag"
          onDelete={() => {}}
          deleteAccessibilityLabel="Remove Tag"
        />
      );

      expect(getByA11yLabel('Remove Tag')).toBeTruthy();
    });

    it('should update accessibility state when selected', () => {
      const { getByA11yState } = render(
        <Chip label="Test" selected={true} onPress={() => {}} />
      );

      const chip = getByA11yState({ selected: true });
      expect(chip).toBeTruthy();
    });

    it('should update accessibility state when disabled', () => {
      const { getByA11yState } = render(
        <Chip label="Test" disabled={true} onPress={() => {}} />
      );

      const chip = getByA11yState({ disabled: true });
      expect(chip).toBeTruthy();
    });
  });

  describe('Styling', () => {
    it('should apply custom styles', () => {
      const customStyle = { marginLeft: 10 };
      const { getByA11yRole } = render(
        <Chip label="Test" style={customStyle} />
      );

      const chip = getByA11yRole('text');
      expect(chip.props.style).toContainEqual(customStyle);
    });
  });

  describe('Icons', () => {
    it('should render with icon', () => {
      const Icon = () => <></>;
      const { getByA11yRole } = render(
        <Chip label="With Icon" icon={<Icon />} />
      );

      expect(getByA11yRole('text')).toBeTruthy();
    });

    it('should render with custom delete icon', () => {
      const DeleteIcon = () => <></>;
      const { getByA11yLabel } = render(
        <Chip label="Test" onDelete={() => {}} deleteIcon={<DeleteIcon />} />
      );

      expect(getByA11yLabel('حذف Test')).toBeTruthy();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty label gracefully', () => {
      const { getByA11yRole } = render(<Chip label="" />);

      expect(getByA11yRole('text')).toBeTruthy();
    });

    it('should handle very long labels', () => {
      const longLabel = 'A'.repeat(100);
      const { getByText } = render(<Chip label={longLabel} />);

      expect(getByText(longLabel)).toBeTruthy();
    });

    it('should handle rapid press events', () => {
      const onPress = jest.fn();
      const { getByA11yRole } = render(
        <Chip label="Test" onPress={onPress} />
      );

      const chip = getByA11yRole('button');
      fireEvent.press(chip);
      fireEvent.press(chip);
      fireEvent.press(chip);

      expect(onPress).toHaveBeenCalledTimes(3);
    });

    it('should handle rapid delete events', () => {
      const onDelete = jest.fn();
      const { getByA11yLabel } = render(
        <Chip label="Test" onDelete={onDelete} />
      );

      const deleteButton = getByA11yLabel('حذف Test');
      fireEvent.press(deleteButton);
      fireEvent.press(deleteButton);
      fireEvent.press(deleteButton);

      expect(onDelete).toHaveBeenCalledTimes(3);
    });
  });

  describe('Animation', () => {
    it('should handle press animations', () => {
      const { getByA11yRole } = render(
        <Chip label="Test" onPress={() => {}} />
      );

      const chip = getByA11yRole('button');
      fireEvent(chip, 'pressIn');
      fireEvent(chip, 'pressOut');

      // Animation should complete without errors
      expect(chip).toBeTruthy();
    });
  });

  describe('Component State', () => {
    it('should toggle selected state visually', () => {
      const { getByA11yState, rerender } = render(
        <Chip label="Test" selected={false} onPress={() => {}} />
      );

      let chip = getByA11yState({ selected: false });
      expect(chip).toBeTruthy();

      rerender(<Chip label="Test" selected={true} onPress={() => {}} />);

      chip = getByA11yState({ selected: true });
      expect(chip).toBeTruthy();
    });
  });
});
