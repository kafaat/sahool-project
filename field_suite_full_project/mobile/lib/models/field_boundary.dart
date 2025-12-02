class FieldMetadata {
  final String? source;
  final String? createdAt;
  final String? updatedAt;
  final String? cropType;
  final String? notes;

  FieldMetadata({
    this.source,
    this.createdAt,
    this.updatedAt,
    this.cropType,
    this.notes,
  });

  factory FieldMetadata.fromJson(Map<String, dynamic> json) {
    return FieldMetadata(
      source: json['source'],
      createdAt: json['createdAt'],
      updatedAt: json['updatedAt'],
      cropType: json['cropType'],
      notes: json['notes'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (source != null) 'source': source,
      if (createdAt != null) 'createdAt': createdAt,
      if (updatedAt != null) 'updatedAt': updatedAt,
      if (cropType != null) 'cropType': cropType,
      if (notes != null) 'notes': notes,
    };
  }
}

class FieldBoundary {
  final String? id;
  final String name;
  final String geometryType;
  final List<List<List<double>>> coordinates;
  final List<double>? center;
  final double? radiusMeters;
  final FieldMetadata? metadata;

  FieldBoundary({
    this.id,
    required this.name,
    required this.geometryType,
    required this.coordinates,
    this.center,
    this.radiusMeters,
    this.metadata,
  });

  factory FieldBoundary.fromJson(Map<String, dynamic> json) {
    return FieldBoundary(
      id: json['id'],
      name: json['name'],
      geometryType: json['geometryType'],
      coordinates: (json['coordinates'] as List)
          .map((ring) => (ring as List)
              .map((point) => (point as List).map((c) => (c as num).toDouble()).toList())
              .toList())
          .toList(),
      center: json['center'] != null
          ? (json['center'] as List).map((c) => (c as num).toDouble()).toList()
          : null,
      radiusMeters: json['radiusMeters']?.toDouble(),
      metadata: json['metadata'] != null
          ? FieldMetadata.fromJson(json['metadata'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (id != null) 'id': id,
      'name': name,
      'geometryType': geometryType,
      'coordinates': coordinates,
      if (center != null) 'center': center,
      if (radiusMeters != null) 'radiusMeters': radiusMeters,
      if (metadata != null) 'metadata': metadata!.toJson(),
    };
  }

  FieldBoundary copyWith({
    String? id,
    String? name,
    String? geometryType,
    List<List<List<double>>>? coordinates,
    List<double>? center,
    double? radiusMeters,
    FieldMetadata? metadata,
  }) {
    return FieldBoundary(
      id: id ?? this.id,
      name: name ?? this.name,
      geometryType: geometryType ?? this.geometryType,
      coordinates: coordinates ?? this.coordinates,
      center: center ?? this.center,
      radiusMeters: radiusMeters ?? this.radiusMeters,
      metadata: metadata ?? this.metadata,
    );
  }
}
