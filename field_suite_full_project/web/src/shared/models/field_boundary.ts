export type GeometryType = 'Polygon' | 'Rectangle' | 'Circle' | 'Pivot';

export interface FieldMetadata {
  source?: 'manual' | 'auto_ndvi' | 'auto_ai' | 'import_gis';
  createdAt?: string;
  updatedAt?: string;
  cropType?: string;
  notes?: string;
}

export interface FieldBoundary {
  id?: string;
  name: string;
  geometryType: GeometryType;
  coordinates: number[][][];
  center?: [number, number];
  radiusMeters?: number;
  metadata?: FieldMetadata;
}
