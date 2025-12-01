/**
 * Field Suite CopilotKit Actions
 * AG-UI compatible actions for field management
 */

import { useCopilotAction, useCopilotReadable } from '@copilotkit/react-core';
import { useFieldContext } from '../context/FieldContext';
import type { FieldBoundary, GeometryType } from '../shared/models/field_boundary';

/**
 * Hook to register all Field Suite actions with CopilotKit
 */
export function useFieldActions() {
  const {
    state,
    createField,
    deleteField,
    selectField,
    setTool,
    autoDetect,
    splitIntoZones,
    loadFields,
  } = useFieldContext();

  // Make field state readable by the AI
  useCopilotReadable({
    description: 'The current list of agricultural fields',
    value: state.fields,
  });

  useCopilotReadable({
    description: 'The currently selected field',
    value: state.selectedFieldId
      ? state.fields.find((f) => f.id === state.selectedFieldId)
      : null,
  });

  useCopilotReadable({
    description: 'The current active drawing tool',
    value: state.activeTool,
  });

  useCopilotReadable({
    description: 'Whether the API backend is connected',
    value: state.isApiConnected,
  });

  // Action: Create a new field
  useCopilotAction({
    name: 'createField',
    description: 'Create a new agricultural field with specified boundaries',
    parameters: [
      {
        name: 'name',
        type: 'string',
        description: 'The name of the field',
        required: true,
      },
      {
        name: 'geometryType',
        type: 'string',
        description: 'The type of geometry: Polygon, Rectangle, Circle, or Pivot',
        required: true,
        enum: ['Polygon', 'Rectangle', 'Circle', 'Pivot'],
      },
      {
        name: 'coordinates',
        type: 'object',
        description: 'Array of coordinate rings, each containing [lng, lat] pairs',
        required: true,
      },
      {
        name: 'cropType',
        type: 'string',
        description: 'The type of crop planted in this field',
        required: false,
      },
      {
        name: 'notes',
        type: 'string',
        description: 'Additional notes about the field',
        required: false,
      },
    ],
    handler: async ({ name, geometryType, coordinates, cropType, notes }) => {
      const field: Omit<FieldBoundary, 'id'> = {
        name,
        geometryType: geometryType as GeometryType,
        coordinates: coordinates as number[][][],
        metadata: {
          source: 'manual',
          cropType,
          notes,
        },
      };

      const created = await createField(field);
      return created
        ? `Successfully created field "${name}" with ID ${created.id}`
        : 'Failed to create field';
    },
  });

  // Action: List all fields
  useCopilotAction({
    name: 'listFields',
    description: 'Get a list of all agricultural fields',
    parameters: [],
    handler: async () => {
      await loadFields();
      const fields = state.fields;
      if (fields.length === 0) {
        return 'No fields found. You can create fields using the drawing tools or auto-detect feature.';
      }
      return fields.map((f) => ({
        id: f.id,
        name: f.name,
        type: f.geometryType,
        cropType: f.metadata?.cropType || 'Not specified',
      }));
    },
  });

  // Action: Select a field
  useCopilotAction({
    name: 'selectField',
    description: 'Select a field by its ID or name',
    parameters: [
      {
        name: 'identifier',
        type: 'string',
        description: 'The field ID or name to select',
        required: true,
      },
    ],
    handler: async ({ identifier }) => {
      const field = state.fields.find(
        (f) => f.id === identifier || f.name.toLowerCase() === identifier.toLowerCase()
      );
      if (field) {
        selectField(field.id!);
        return `Selected field "${field.name}"`;
      }
      return `Field "${identifier}" not found`;
    },
  });

  // Action: Delete a field
  useCopilotAction({
    name: 'deleteField',
    description: 'Delete a field by its ID or name',
    parameters: [
      {
        name: 'identifier',
        type: 'string',
        description: 'The field ID or name to delete',
        required: true,
      },
    ],
    handler: async ({ identifier }) => {
      const field = state.fields.find(
        (f) => f.id === identifier || f.name.toLowerCase() === identifier.toLowerCase()
      );
      if (field) {
        await deleteField(field.id!);
        return `Deleted field "${field.name}"`;
      }
      return `Field "${identifier}" not found`;
    },
  });

  // Action: Auto-detect fields
  useCopilotAction({
    name: 'autoDetectFields',
    description: 'Automatically detect field boundaries using satellite imagery analysis (NDVI)',
    parameters: [],
    handler: async () => {
      await autoDetect();
      return 'Auto-detection complete. New fields have been added based on NDVI analysis.';
    },
  });

  // Action: Split field into zones
  useCopilotAction({
    name: 'splitFieldIntoZones',
    description: 'Split a field into management zones for variable rate application',
    parameters: [
      {
        name: 'fieldIdentifier',
        type: 'string',
        description: 'The field ID or name to split',
        required: true,
      },
      {
        name: 'numberOfZones',
        type: 'number',
        description: 'Number of zones to create (2-10)',
        required: true,
      },
    ],
    handler: async ({ fieldIdentifier, numberOfZones }) => {
      const field = state.fields.find(
        (f) =>
          f.id === fieldIdentifier ||
          f.name.toLowerCase() === fieldIdentifier.toLowerCase()
      );
      if (!field) {
        return `Field "${fieldIdentifier}" not found`;
      }
      if (numberOfZones < 2 || numberOfZones > 10) {
        return 'Number of zones must be between 2 and 10';
      }
      await splitIntoZones(field.id!, numberOfZones);
      return `Split "${field.name}" into ${numberOfZones} management zones`;
    },
  });

  // Action: Set drawing tool
  useCopilotAction({
    name: 'setDrawingTool',
    description: 'Activate a drawing tool for creating field boundaries',
    parameters: [
      {
        name: 'tool',
        type: 'string',
        description: 'The tool to activate: select, Polygon, Rectangle, Circle, or Pivot',
        required: true,
        enum: ['select', 'Polygon', 'Rectangle', 'Circle', 'Pivot'],
      },
    ],
    handler: async ({ tool }) => {
      setTool(tool as GeometryType | 'select');
      if (tool === 'select') {
        return 'Selection tool activated. Click on fields to select them.';
      }
      return `${tool} drawing tool activated. Click on the map to start drawing.`;
    },
  });

  // Action: Get field statistics
  useCopilotAction({
    name: 'getFieldStatistics',
    description: 'Get statistics about all fields',
    parameters: [],
    handler: async () => {
      const fields = state.fields;
      const stats = {
        totalFields: fields.length,
        byType: {} as Record<string, number>,
        byCropType: {} as Record<string, number>,
        bySource: {} as Record<string, number>,
      };

      fields.forEach((f) => {
        // By geometry type
        stats.byType[f.geometryType] = (stats.byType[f.geometryType] || 0) + 1;

        // By crop type
        const crop = f.metadata?.cropType || 'Unspecified';
        stats.byCropType[crop] = (stats.byCropType[crop] || 0) + 1;

        // By source
        const source = f.metadata?.source || 'Unknown';
        stats.bySource[source] = (stats.bySource[source] || 0) + 1;
      });

      return stats;
    },
  });

  // Action: Get crop recommendations
  useCopilotAction({
    name: 'getCropRecommendations',
    description: 'Get crop recommendations for a specific field based on its properties',
    parameters: [
      {
        name: 'fieldIdentifier',
        type: 'string',
        description: 'The field ID or name',
        required: true,
      },
    ],
    handler: async ({ fieldIdentifier }) => {
      const field = state.fields.find(
        (f) =>
          f.id === fieldIdentifier ||
          f.name.toLowerCase() === fieldIdentifier.toLowerCase()
      );
      if (!field) {
        return `Field "${fieldIdentifier}" not found`;
      }

      // Mock recommendations - in production, this would use real data
      const recommendations = [
        'Based on the field geometry, consider crop rotation with legumes to improve soil nitrogen.',
        'The field shape is suitable for precision agriculture techniques.',
        'Recommend soil testing before the next planting season.',
        'Consider cover crops during off-season to prevent erosion.',
      ];

      return {
        field: field.name,
        currentCrop: field.metadata?.cropType || 'Not specified',
        recommendations,
      };
    },
  });
}
