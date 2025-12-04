import { useCallback } from "react";
import {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  withSequence,
} from "react-native-reanimated";

const SPRING_CONFIG = {
  damping: 15,
  stiffness: 150,
  mass: 0.5,
};

// Press Animation
export function usePressAnimation(scaleValue = 0.95) {
  const scale = useSharedValue(1);
  const opacity = useSharedValue(1);

  const pressIn = useCallback(() => {
    scale.value = withSpring(scaleValue, SPRING_CONFIG);
    opacity.value = withTiming(0.8, { duration: 100 });
  }, [scaleValue]);

  const pressOut = useCallback(() => {
    scale.value = withSpring(1, SPRING_CONFIG);
    opacity.value = withTiming(1, { duration: 100 });
  }, []);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    opacity: opacity.value,
  }));

  return { scale, opacity, pressIn, pressOut, animatedStyle };
}

// Pulse Animation
export function usePulseAnimation() {
  const scale = useSharedValue(1);

  const pulse = useCallback(() => {
    scale.value = withSequence(
      withSpring(1.1, SPRING_CONFIG),
      withSpring(1, SPRING_CONFIG)
    );
  }, []);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return { pulse, animatedStyle };
}

// Shake Animation
export function useShakeAnimation() {
  const translateX = useSharedValue(0);

  const shake = useCallback(() => {
    translateX.value = withSequence(
      withTiming(-10, { duration: 50 }),
      withTiming(10, { duration: 50 }),
      withTiming(-10, { duration: 50 }),
      withTiming(10, { duration: 50 }),
      withTiming(0, { duration: 50 })
    );
  }, []);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }],
  }));

  return { shake, animatedStyle };
}

// Legacy export
export function useMicroInteraction() {
  return usePressAnimation();
}