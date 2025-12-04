import { useState, useCallback, useEffect } from "react";
import * as Location from "expo-location";

interface LocationState {
  latitude: number | null;
  longitude: number | null;
  accuracy: number | null;
  altitude: number | null;
}

export function useLocation() {
  const [location, setLocation] = useState<LocationState>({
    latitude: null,
    longitude: null,
    accuracy: null,
    altitude: null,
  });
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [watchSubscription, setWatchSubscription] = useState<Location.LocationSubscription | null>(null);

  const requestPermission = useCallback(async (): Promise<boolean> => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") {
        setError("Location permission denied");
        return false;
      }
      return true;
    } catch (err) {
      setError("Error requesting permission");
      return false;
    }
  }, []);

  const getCurrentLocation = useCallback(async (): Promise<LocationState | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const hasPermission = await requestPermission();
      if (!hasPermission) return null;

      const currentLocation = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
      });

      const newLocation: LocationState = {
        latitude: currentLocation.coords.latitude,
        longitude: currentLocation.coords.longitude,
        accuracy: currentLocation.coords.accuracy,
        altitude: currentLocation.coords.altitude,
      };

      setLocation(newLocation);
      return newLocation;
    } catch (err: any) {
      setError(err.message || "Failed to get location");
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [requestPermission]);

  const watchLocation = useCallback(async () => {
    const hasPermission = await requestPermission();
    if (!hasPermission) return;

    const subscription = await Location.watchPositionAsync(
      {
        accuracy: Location.Accuracy.High,
        timeInterval: 5000,
        distanceInterval: 10,
      },
      (newLocation) => {
        setLocation({
          latitude: newLocation.coords.latitude,
          longitude: newLocation.coords.longitude,
          accuracy: newLocation.coords.accuracy,
          altitude: newLocation.coords.altitude,
        });
      }
    );

    setWatchSubscription(subscription);
  }, [requestPermission]);

  const stopWatching = useCallback(() => {
    if (watchSubscription) {
      watchSubscription.remove();
      setWatchSubscription(null);
    }
  }, [watchSubscription]);

  useEffect(() => {
    return () => {
      if (watchSubscription) {
        watchSubscription.remove();
      }
    };
  }, [watchSubscription]);

  return {
    location,
    error,
    isLoading,
    requestPermission,
    getCurrentLocation,
    watchLocation,
    stopWatching,
  };
}