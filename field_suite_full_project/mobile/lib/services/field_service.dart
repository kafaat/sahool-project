import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/field_boundary.dart';
import '../config/app_config.dart';

class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final String? requestId;

  ApiException(this.message, {this.statusCode, this.requestId});

  @override
  String toString() => 'ApiException: $message (status: $statusCode, requestId: $requestId)';
}

class FieldService {
  /// API Base URL - configurable via AppConfig
  static String get baseUrl => AppConfig.apiBaseUrl;

  final http.Client _client;

  FieldService({http.Client? client}) : _client = client ?? http.Client();

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Client-Version': AppConfig.appVersion,
  };

  /// Extract request ID from response headers for debugging
  String? _getRequestId(http.Response response) {
    return response.headers['x-request-id'];
  }

  Future<bool> healthCheck() async {
    try {
      final response = await _client
          .get(Uri.parse(baseUrl))
          .timeout(AppConfig.connectionTimeout);
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<Map<String, dynamic>> getHealthDetails() async {
    try {
      final response = await _client.get(
        Uri.parse(baseUrl),
        headers: _headers,
      ).timeout(AppConfig.connectionTimeout);

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
      return {'status': 'error', 'message': 'Failed to get health details'};
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  Future<List<FieldBoundary>> listFields() async {
    try {
      final response = await _client.get(
        Uri.parse('$baseUrl/fields/'),
        headers: _headers,
      ).timeout(AppConfig.receiveTimeout);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final fields = data['fields'] as List;
        return fields.map((f) => FieldBoundary.fromJson(f)).toList();
      } else if (response.statusCode == 429) {
        throw ApiException(
          'Rate limit exceeded. Please wait and try again.',
          statusCode: response.statusCode,
          requestId: _getRequestId(response),
        );
      } else {
        throw ApiException(
          'Failed to load fields',
          statusCode: response.statusCode,
          requestId: _getRequestId(response),
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  Future<FieldBoundary> getField(String id) async {
    try {
      final response = await _client.get(
        Uri.parse('$baseUrl/fields/$id'),
        headers: _headers,
      ).timeout(AppConfig.receiveTimeout);

      if (response.statusCode == 200) {
        return FieldBoundary.fromJson(jsonDecode(response.body));
      } else if (response.statusCode == 404) {
        throw ApiException(
          'Field not found',
          statusCode: 404,
          requestId: _getRequestId(response),
        );
      } else if (response.statusCode == 429) {
        throw ApiException(
          'Rate limit exceeded',
          statusCode: response.statusCode,
          requestId: _getRequestId(response),
        );
      } else {
        throw ApiException(
          'Failed to get field',
          statusCode: response.statusCode,
          requestId: _getRequestId(response),
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  Future<FieldBoundary> createField(FieldBoundary field) async {
    try {
      final response = await _client.post(
        Uri.parse('$baseUrl/fields/'),
        headers: _headers,
        body: jsonEncode(field.toJson()),
      ).timeout(AppConfig.receiveTimeout);

      if (response.statusCode == 201) {
        return FieldBoundary.fromJson(jsonDecode(response.body));
      } else if (response.statusCode == 429) {
        throw ApiException(
          'Rate limit exceeded',
          statusCode: response.statusCode,
          requestId: _getRequestId(response),
        );
      } else {
        final error = jsonDecode(response.body);
        throw ApiException(
          error['detail'] ?? 'Failed to create field',
          statusCode: response.statusCode,
          requestId: _getRequestId(response),
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  Future<FieldBoundary> updateField(String id, FieldBoundary field) async {
    try {
      final response = await _client.put(
        Uri.parse('$baseUrl/fields/$id'),
        headers: _headers,
        body: jsonEncode(field.toJson()),
      ).timeout(AppConfig.receiveTimeout);

      if (response.statusCode == 200) {
        return FieldBoundary.fromJson(jsonDecode(response.body));
      } else if (response.statusCode == 404) {
        throw ApiException(
          'Field not found',
          statusCode: 404,
          requestId: _getRequestId(response),
        );
      } else if (response.statusCode == 429) {
        throw ApiException(
          'Rate limit exceeded',
          statusCode: response.statusCode,
          requestId: _getRequestId(response),
        );
      } else {
        throw ApiException(
          'Failed to update field',
          statusCode: response.statusCode,
          requestId: _getRequestId(response),
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  Future<void> deleteField(String id) async {
    try {
      final response = await _client.delete(
        Uri.parse('$baseUrl/fields/$id'),
        headers: _headers,
      ).timeout(AppConfig.receiveTimeout);

      if (response.statusCode != 204) {
        if (response.statusCode == 404) {
          throw ApiException(
            'Field not found',
            statusCode: 404,
            requestId: _getRequestId(response),
          );
        } else if (response.statusCode == 429) {
          throw ApiException(
            'Rate limit exceeded',
            statusCode: response.statusCode,
            requestId: _getRequestId(response),
          );
        }
        throw ApiException(
          'Failed to delete field',
          statusCode: response.statusCode,
          requestId: _getRequestId(response),
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  Future<List<FieldBoundary>> autoDetect({bool mock = true}) async {
    try {
      final response = await _client.post(
        Uri.parse('$baseUrl/fields/auto-detect'),
        headers: _headers,
        body: jsonEncode({'mock': mock}),
      ).timeout(AppConfig.receiveTimeout);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final fields = data['fields'] as List;
        return fields.map((f) => FieldBoundary.fromJson(f)).toList();
      } else if (response.statusCode == 429) {
        throw ApiException(
          'Rate limit exceeded',
          statusCode: response.statusCode,
          requestId: _getRequestId(response),
        );
      } else {
        throw ApiException(
          'Auto-detect failed',
          statusCode: response.statusCode,
          requestId: _getRequestId(response),
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  Future<List<FieldBoundary>> splitIntoZones(FieldBoundary field, int zones) async {
    try {
      final response = await _client.post(
        Uri.parse('$baseUrl/fields/zones'),
        headers: _headers,
        body: jsonEncode({
          'field': field.toJson(),
          'zones': zones,
        }),
      ).timeout(AppConfig.receiveTimeout);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final fields = data['fields'] as List;
        return fields.map((f) => FieldBoundary.fromJson(f)).toList();
      } else if (response.statusCode == 429) {
        throw ApiException(
          'Rate limit exceeded',
          statusCode: response.statusCode,
          requestId: _getRequestId(response),
        );
      } else {
        throw ApiException(
          'Zone split failed',
          statusCode: response.statusCode,
          requestId: _getRequestId(response),
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }
}
