import { useCallback } from "react";
import {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
} from "react-native-reanimated";

export function usePressAnimation() {
  const scale = useSharedValue(1);

  const pressIn = useCallback(() => {
    scale.value = withSpring(0.95, { stiffness: 500, damping: 10 });
  }, []);

  const pressOut = useCallback(() => {
    scale.value = withSpring(1, { stiffness: 500, damping: 10 });
  }, []);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return { pressIn, pressOut, animatedStyle, scale };
}
