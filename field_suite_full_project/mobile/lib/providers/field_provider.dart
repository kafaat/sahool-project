import 'package:flutter/material.dart';
import 'package:maplibre_gl/maplibre_gl.dart';
import '../models/field_boundary.dart';
import '../services/field_service.dart';

enum DrawingTool { select, polygon, rectangle, circle, pivot }

class FieldProvider extends ChangeNotifier {
  final FieldService _service;

  List<FieldBoundary> _fields = [];
  FieldBoundary? _selectedField;
  DrawingTool _activeTool = DrawingTool.select;
  List<LatLng> _drawingPoints = [];
  bool _isLoading = false;
  bool _isApiConnected = false;
  String? _errorMessage;

  FieldProvider(this._service) {
    _init();
  }

  // Getters
  List<FieldBoundary> get fields => _fields;
  FieldBoundary? get selectedField => _selectedField;
  DrawingTool get activeTool => _activeTool;
  List<LatLng> get drawingPoints => _drawingPoints;
  bool get isLoading => _isLoading;
  bool get isApiConnected => _isApiConnected;
  String? get errorMessage => _errorMessage;
  bool get isDrawing => _activeTool != DrawingTool.select;

  Future<void> _init() async {
    await checkApiConnection();
    if (_isApiConnected) {
      await loadFields();
    }
  }

  Future<void> checkApiConnection() async {
    _isApiConnected = await _service.healthCheck();
    notifyListeners();
  }

  Future<void> loadFields() async {
    _setLoading(true);
    _clearError();

    try {
      _fields = await _service.listFields();
    } catch (e) {
      _setError('Failed to load fields: $e');
    }

    _setLoading(false);
  }

  Future<void> createField(FieldBoundary field) async {
    _setLoading(true);
    _clearError();

    try {
      final created = await _service.createField(field);
      _fields.add(created);
      _selectedField = created;
    } catch (e) {
      _setError('Failed to create field: $e');
    }

    _setLoading(false);
  }

  Future<void> updateField(String id, FieldBoundary field) async {
    _setLoading(true);
    _clearError();

    try {
      final updated = await _service.updateField(id, field);
      final index = _fields.indexWhere((f) => f.id == id);
      if (index != -1) {
        _fields[index] = updated;
      }
      if (_selectedField?.id == id) {
        _selectedField = updated;
      }
    } catch (e) {
      _setError('Failed to update field: $e');
    }

    _setLoading(false);
  }

  Future<void> deleteField(String id) async {
    _setLoading(true);
    _clearError();

    try {
      await _service.deleteField(id);
      _fields.removeWhere((f) => f.id == id);
      if (_selectedField?.id == id) {
        _selectedField = null;
      }
    } catch (e) {
      _setError('Failed to delete field: $e');
    }

    _setLoading(false);
  }

  void selectField(FieldBoundary? field) {
    _selectedField = field;
    notifyListeners();
  }

  void setTool(DrawingTool tool) {
    _activeTool = tool;
    if (tool == DrawingTool.select) {
      _drawingPoints.clear();
    }
    notifyListeners();
  }

  void addDrawingPoint(LatLng point) {
    _drawingPoints.add(point);
    notifyListeners();
  }

  void clearDrawing() {
    _drawingPoints.clear();
    _activeTool = DrawingTool.select;
    notifyListeners();
  }

  Future<void> finishDrawing(String name) async {
    if (_drawingPoints.length < 3) {
      _setError('At least 3 points required');
      return;
    }

    final coordinates = _drawingPoints
        .map((p) => [p.longitude, p.latitude])
        .toList();
    // Close the polygon
    coordinates.add([_drawingPoints.first.longitude, _drawingPoints.first.latitude]);

    final field = FieldBoundary(
      name: name,
      geometryType: _getGeometryType(),
      coordinates: [coordinates],
      metadata: FieldMetadata(source: 'manual'),
    );

    await createField(field);
    clearDrawing();
  }

  String _getGeometryType() {
    switch (_activeTool) {
      case DrawingTool.polygon:
        return 'Polygon';
      case DrawingTool.rectangle:
        return 'Rectangle';
      case DrawingTool.circle:
        return 'Circle';
      case DrawingTool.pivot:
        return 'Pivot';
      default:
        return 'Polygon';
    }
  }

  Future<void> autoDetect() async {
    _setLoading(true);
    _clearError();

    try {
      final detected = await _service.autoDetect();
      _fields.addAll(detected);
    } catch (e) {
      _setError('Auto-detect failed: $e');
    }

    _setLoading(false);
  }

  Future<void> splitIntoZones(String fieldId, int zones) async {
    final field = _fields.firstWhere((f) => f.id == fieldId);
    _setLoading(true);
    _clearError();

    try {
      final zoneFields = await _service.splitIntoZones(field, zones);
      _fields.addAll(zoneFields);
    } catch (e) {
      _setError('Zone split failed: $e');
    }

    _setLoading(false);
  }

  void _setLoading(bool value) {
    _isLoading = value;
    notifyListeners();
  }

  void _setError(String message) {
    _errorMessage = message;
    notifyListeners();
  }

  void _clearError() {
    _errorMessage = null;
  }

  void clearError() {
    _clearError();
    notifyListeners();
  }
}
