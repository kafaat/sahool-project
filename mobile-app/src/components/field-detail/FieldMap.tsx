import React from 'react';
import { StyleSheet, Dimensions } from 'react-native';
import { Card } from 'react-native-paper';
import MapView, { Polygon, Marker } from 'react-native-maps';

interface FieldMapProps {
  center: { lat: number; lon: number };
  boundaries: Array<{ lat: number; lon: number }>;
  name: string;
}

export default function FieldMap({ center, boundaries, name }: FieldMapProps) {
  return (
    <Card style={styles.mapCard}>
      <MapView
        style={styles.map}
        initialRegion={{
          latitude: center.lat,
          longitude: center.lon,
          latitudeDelta: 0.01,
          longitudeDelta: 0.01,
        }}
      >
        {boundaries && boundaries.length > 0 && (
          <Polygon
            coordinates={boundaries.map((point) => ({
              latitude: point.lat,
              longitude: point.lon,
            }))}
            fillColor="rgba(46, 125, 50, 0.2)"
            strokeColor="#2E7D32"
            strokeWidth={2}
          />
        )}
        <Marker
          coordinate={{
            latitude: center.lat,
            longitude: center.lon,
          }}
          title={name}
        />
      </MapView>
    </Card>
  );
}

const styles = StyleSheet.create({
  mapCard: {
    margin: 0,
    borderRadius: 0,
    overflow: 'hidden',
  },
  map: {
    width: Dimensions.get('window').width,
    height: 250,
  },
});
