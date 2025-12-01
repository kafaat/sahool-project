import React, { useEffect, useRef, useState, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import { useFieldContext } from '../context/FieldContext';

import 'maplibre-gl/dist/maplibre-gl.css';

const FIELD_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1',
];

export const FieldMap: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);

  const { state, addDrawingCoord, finishDrawing, cancelDrawing, selectField } = useFieldContext();
  const [fieldName, setFieldName] = useState('');
  const [showNameModal, setShowNameModal] = useState(false);

  // Initialize map
  useEffect(() => {
    if (mapRef.current || !containerRef.current) return;

    mapRef.current = new maplibregl.Map({
      container: containerRef.current,
      style: 'https://demotiles.maplibre.org/style.json',
      center: [45, 24],
      zoom: 6,
    });

    mapRef.current.addControl(new maplibregl.NavigationControl(), 'bottom-right');

    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  // Handle map clicks for drawing
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const handleClick = (e: maplibregl.MapMouseEvent) => {
      if (state.activeTool !== 'select' && state.isDrawing) {
        const coord: [number, number] = [e.lngLat.lng, e.lngLat.lat];
        addDrawingCoord(coord);
      }
    };

    map.on('click', handleClick);
    return () => {
      map.off('click', handleClick);
    };
  }, [state.activeTool, state.isDrawing, addDrawingCoord]);

  // Update cursor based on tool
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (state.activeTool !== 'select') {
      map.getCanvas().style.cursor = 'crosshair';
    } else {
      map.getCanvas().style.cursor = '';
    }
  }, [state.activeTool]);

  // Draw current drawing coords as markers
  useEffect(() => {
    // Clear existing markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    if (!mapRef.current || state.drawingCoords.length === 0) return;

    // Add markers for drawing points
    state.drawingCoords.forEach((coord, index) => {
      const el = document.createElement('div');
      el.className = 'drawing-marker';
      el.style.cssText = `
        width: 12px;
        height: 12px;
        background: #3b82f6;
        border: 2px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      `;
      if (index === 0) {
        el.style.background = '#10b981';
        el.style.width = '16px';
        el.style.height = '16px';
      }

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat(coord)
        .addTo(mapRef.current!);
      markersRef.current.push(marker);
    });

    // Draw line connecting points
    const sourceId = 'drawing-line';
    const layerId = 'drawing-line-layer';

    if (mapRef.current.getSource(sourceId)) {
      (mapRef.current.getSource(sourceId) as maplibregl.GeoJSONSource).setData({
        type: 'Feature',
        properties: {},
        geometry: {
          type: 'LineString',
          coordinates: state.drawingCoords,
        },
      });
    } else {
      mapRef.current.addSource(sourceId, {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: {
            type: 'LineString',
            coordinates: state.drawingCoords,
          },
        },
      });

      mapRef.current.addLayer({
        id: layerId,
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': '#3b82f6',
          'line-width': 2,
          'line-dasharray': [2, 2],
        },
      });
    }
  }, [state.drawingCoords]);

  // Render saved fields as polygons
  const renderFields = useCallback(() => {
    const map = mapRef.current;
    if (!map || !map.loaded()) return;

    // Remove existing field layers
    for (let i = 0; i < 50; i++) {
      const layerId = `field-fill-${i}`;
      const outlineId = `field-outline-${i}`;
      const sourceId = `field-source-${i}`;

      if (map.getLayer(layerId)) map.removeLayer(layerId);
      if (map.getLayer(outlineId)) map.removeLayer(outlineId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
    }

    // Add field polygons
    state.fields.forEach((field, index) => {
      if (!field.coordinates || !field.coordinates[0]) return;

      const sourceId = `field-source-${index}`;
      const fillLayerId = `field-fill-${index}`;
      const outlineLayerId = `field-outline-${index}`;
      const color = FIELD_COLORS[index % FIELD_COLORS.length];
      const isSelected = field.id === state.selectedFieldId;

      map.addSource(sourceId, {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: { id: field.id, name: field.name },
          geometry: {
            type: 'Polygon',
            coordinates: field.coordinates,
          },
        },
      });

      map.addLayer({
        id: fillLayerId,
        type: 'fill',
        source: sourceId,
        paint: {
          'fill-color': color,
          'fill-opacity': isSelected ? 0.5 : 0.3,
        },
      });

      map.addLayer({
        id: outlineLayerId,
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': color,
          'line-width': isSelected ? 3 : 2,
        },
      });

      // Add click handler for selection
      map.on('click', fillLayerId, () => {
        selectField(field.id || null);
      });

      map.on('mouseenter', fillLayerId, () => {
        map.getCanvas().style.cursor = 'pointer';
      });

      map.on('mouseleave', fillLayerId, () => {
        map.getCanvas().style.cursor = state.activeTool !== 'select' ? 'crosshair' : '';
      });
    });
  }, [state.fields, state.selectedFieldId, state.activeTool, selectField]);

  // Re-render fields when they change
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const onLoad = () => renderFields();

    if (map.loaded()) {
      renderFields();
    } else {
      map.on('load', onLoad);
    }

    return () => {
      map.off('load', onLoad);
    };
  }, [renderFields]);

  const handleFinish = () => {
    if (state.drawingCoords.length >= 3) {
      setShowNameModal(true);
    }
  };

  const handleSaveField = async () => {
    if (fieldName.trim()) {
      await finishDrawing(fieldName.trim());
      setFieldName('');
      setShowNameModal(false);
    }
  };

  const handleCancelDrawing = () => {
    cancelDrawing();
    // Clear drawing line
    const map = mapRef.current;
    if (map) {
      if (map.getLayer('drawing-line-layer')) {
        map.removeLayer('drawing-line-layer');
      }
      if (map.getSource('drawing-line')) {
        map.removeSource('drawing-line');
      }
    }
  };

  return (
    <div style={{ height: '100%', position: 'relative' }}>
      <div ref={containerRef} style={{ height: '100%', width: '100%' }} />

      {/* Map Controls */}
      {state.isDrawing && state.activeTool !== 'select' && (
        <div className="map-controls">
          {state.drawingCoords.length >= 3 && (
            <button className="map-control-btn finish" onClick={handleFinish}>
              Finish Drawing
            </button>
          )}
          <button className="map-control-btn cancel" onClick={handleCancelDrawing}>
            Cancel
          </button>
        </div>
      )}

      {/* Drawing Info */}
      {state.isDrawing && state.activeTool !== 'select' && (
        <div className="drawing-info">
          Drawing {state.activeTool} • {state.drawingCoords.length} points
          {state.drawingCoords.length < 3 && ' (min 3 required)'}
        </div>
      )}

      {/* Name Modal */}
      {showNameModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>Name Your Field</h2>
            <div className="form-group">
              <label>Field Name</label>
              <input
                type="text"
                className="form-input"
                value={fieldName}
                onChange={(e) => setFieldName(e.target.value)}
                placeholder="Enter field name..."
                autoFocus
                onKeyDown={(e) => e.key === 'Enter' && handleSaveField()}
              />
            </div>
            <div className="modal-actions">
              <button
                className="action-btn secondary"
                onClick={() => {
                  setShowNameModal(false);
                  setFieldName('');
                }}
              >
                Cancel
              </button>
              <button
                className="action-btn primary"
                onClick={handleSaveField}
                disabled={!fieldName.trim()}
              >
                Save Field
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
