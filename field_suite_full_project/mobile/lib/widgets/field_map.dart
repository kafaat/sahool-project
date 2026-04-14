import 'package:flutter/material.dart';
import 'package:maplibre_gl/maplibre_gl.dart';
import 'package:provider/provider.dart';
import '../providers/field_provider.dart';

class FieldMap extends StatefulWidget {
  const FieldMap({super.key});

  @override
  State<FieldMap> createState() => _FieldMapState();
}

class _FieldMapState extends State<FieldMap> {
  MaplibreMapController? _mapController;

  static const List<Color> fieldColors = [
    Color(0xFF3B82F6),
    Color(0xFF10B981),
    Color(0xFFF59E0B),
    Color(0xFFEF4444),
    Color(0xFF8B5CF6),
    Color(0xFFEC4899),
    Color(0xFF06B6D4),
    Color(0xFF84CC16),
  ];

  @override
  Widget build(BuildContext context) {
    return Consumer<FieldProvider>(
      builder: (context, provider, child) {
        return MaplibreMap(
          styleString: 'https://demotiles.maplibre.org/style.json',
          initialCameraPosition: const CameraPosition(
            target: LatLng(24, 45),
            zoom: 5,
          ),
          onMapCreated: _onMapCreated,
          onMapClick: (point, latLng) => _onMapClick(latLng, provider),
          myLocationEnabled: true,
          myLocationTrackingMode: MyLocationTrackingMode.None,
        );
      },
    );
  }

  void _onMapCreated(MaplibreMapController controller) {
    _mapController = controller;
    _renderFields();
  }

  void _onMapClick(LatLng latLng, FieldProvider provider) {
    if (provider.isDrawing) {
      provider.addDrawingPoint(latLng);
      _addDrawingMarker(latLng, provider.drawingPoints.length);
    }
  }

  Future<void> _addDrawingMarker(LatLng position, int index) async {
    if (_mapController == null) return;

    await _mapController!.addCircle(CircleOptions(
      geometry: position,
      circleRadius: index == 1 ? 10 : 8,
      circleColor: index == 1 ? '#10B981' : '#3B82F6',
      circleStrokeWidth: 2,
      circleStrokeColor: '#FFFFFF',
    ));
  }

  Future<void> _renderFields() async {
    if (_mapController == null) return;

    final provider = context.read<FieldProvider>();

    // Clear existing polygons
    await _mapController!.clearCircles();
    await _mapController!.clearFills();
    await _mapController!.clearLines();

    // Render each field
    for (int i = 0; i < provider.fields.length; i++) {
      final field = provider.fields[i];
      if (field.coordinates.isEmpty || field.coordinates[0].isEmpty) continue;

      final color = fieldColors[i % fieldColors.length];
      final isSelected = provider.selectedField?.id == field.id;

      // Convert coordinates to LatLng
      final points = field.coordinates[0]
          .map((c) => LatLng(c[1], c[0]))
          .toList();

      // Add fill
      await _mapController!.addFill(FillOptions(
        geometry: [points],
        fillColor: '#${color.value.toRadixString(16).substring(2)}',
        fillOpacity: isSelected ? 0.5 : 0.3,
      ));

      // Add outline
      await _mapController!.addLine(LineOptions(
        geometry: points,
        lineColor: '#${color.value.toRadixString(16).substring(2)}',
        lineWidth: isSelected ? 3 : 2,
      ));
    }
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Listen to provider changes and re-render
    context.watch<FieldProvider>().addListener(_renderFields);
  }

  @override
  void dispose() {
    _mapController = null;
    super.dispose();
  }
}
