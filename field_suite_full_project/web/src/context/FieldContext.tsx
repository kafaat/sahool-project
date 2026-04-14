import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import type { FieldBoundary, GeometryType } from '../shared/models/field_boundary';
import { fieldApi } from '../services/api';

// Types
export type DrawingTool = GeometryType | 'select';

interface Toast {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
}

interface FieldState {
  fields: FieldBoundary[];
  selectedFieldId: string | null;
  activeTool: DrawingTool;
  isDrawing: boolean;
  drawingCoords: [number, number][];
  isLoading: boolean;
  isApiConnected: boolean;
  toasts: Toast[];
}

type FieldAction =
  | { type: 'SET_FIELDS'; payload: FieldBoundary[] }
  | { type: 'ADD_FIELD'; payload: FieldBoundary }
  | { type: 'UPDATE_FIELD'; payload: FieldBoundary }
  | { type: 'DELETE_FIELD'; payload: string }
  | { type: 'SELECT_FIELD'; payload: string | null }
  | { type: 'SET_TOOL'; payload: DrawingTool }
  | { type: 'START_DRAWING' }
  | { type: 'ADD_DRAWING_COORD'; payload: [number, number] }
  | { type: 'CLEAR_DRAWING' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_API_CONNECTED'; payload: boolean }
  | { type: 'ADD_TOAST'; payload: Toast }
  | { type: 'REMOVE_TOAST'; payload: string };

const initialState: FieldState = {
  fields: [],
  selectedFieldId: null,
  activeTool: 'select',
  isDrawing: false,
  drawingCoords: [],
  isLoading: false,
  isApiConnected: false,
  toasts: [],
};

function fieldReducer(state: FieldState, action: FieldAction): FieldState {
  switch (action.type) {
    case 'SET_FIELDS':
      return { ...state, fields: action.payload };
    case 'ADD_FIELD':
      return { ...state, fields: [...state.fields, action.payload] };
    case 'UPDATE_FIELD':
      return {
        ...state,
        fields: state.fields.map((f) =>
          f.id === action.payload.id ? action.payload : f
        ),
      };
    case 'DELETE_FIELD':
      return {
        ...state,
        fields: state.fields.filter((f) => f.id !== action.payload),
        selectedFieldId:
          state.selectedFieldId === action.payload ? null : state.selectedFieldId,
      };
    case 'SELECT_FIELD':
      return { ...state, selectedFieldId: action.payload };
    case 'SET_TOOL':
      return {
        ...state,
        activeTool: action.payload,
        isDrawing: action.payload !== 'select',
        drawingCoords: action.payload !== 'select' ? [] : state.drawingCoords,
      };
    case 'START_DRAWING':
      return { ...state, isDrawing: true, drawingCoords: [] };
    case 'ADD_DRAWING_COORD':
      return { ...state, drawingCoords: [...state.drawingCoords, action.payload] };
    case 'CLEAR_DRAWING':
      return { ...state, isDrawing: false, drawingCoords: [], activeTool: 'select' };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_API_CONNECTED':
      return { ...state, isApiConnected: action.payload };
    case 'ADD_TOAST':
      return { ...state, toasts: [...state.toasts, action.payload] };
    case 'REMOVE_TOAST':
      return { ...state, toasts: state.toasts.filter((t) => t.id !== action.payload) };
    default:
      return state;
  }
}

// Context
interface FieldContextType {
  state: FieldState;
  loadFields: () => Promise<void>;
  createField: (field: Omit<FieldBoundary, 'id'>) => Promise<FieldBoundary | null>;
  updateField: (id: string, field: FieldBoundary) => Promise<void>;
  deleteField: (id: string) => Promise<void>;
  selectField: (id: string | null) => void;
  setTool: (tool: DrawingTool) => void;
  addDrawingCoord: (coord: [number, number]) => void;
  finishDrawing: (name: string) => Promise<void>;
  cancelDrawing: () => void;
  autoDetect: () => Promise<void>;
  splitIntoZones: (fieldId: string, zones: number) => Promise<void>;
  showToast: (type: Toast['type'], message: string) => void;
  checkApiConnection: () => Promise<void>;
}

const FieldContext = createContext<FieldContextType | null>(null);

export const useFieldContext = () => {
  const context = useContext(FieldContext);
  if (!context) {
    throw new Error('useFieldContext must be used within FieldProvider');
  }
  return context;
};

export const FieldProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(fieldReducer, initialState);

  const showToast = useCallback((type: Toast['type'], message: string) => {
    const id = Date.now().toString();
    dispatch({ type: 'ADD_TOAST', payload: { id, type, message } });
    setTimeout(() => {
      dispatch({ type: 'REMOVE_TOAST', payload: id });
    }, 4000);
  }, []);

  const checkApiConnection = useCallback(async () => {
    const { data, error } = await fieldApi.healthCheck();
    dispatch({ type: 'SET_API_CONNECTED', payload: !error && data?.status === 'healthy' });
  }, []);

  const loadFields = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    const { data, error } = await fieldApi.listFields();
    if (error) {
      showToast('error', `Failed to load fields: ${error}`);
    } else if (data) {
      dispatch({ type: 'SET_FIELDS', payload: data.fields });
    }
    dispatch({ type: 'SET_LOADING', payload: false });
  }, [showToast]);

  const createField = useCallback(
    async (field: Omit<FieldBoundary, 'id'>): Promise<FieldBoundary | null> => {
      dispatch({ type: 'SET_LOADING', payload: true });
      const { data, error } = await fieldApi.createField(field);
      if (error) {
        showToast('error', `Failed to create field: ${error}`);
        dispatch({ type: 'SET_LOADING', payload: false });
        return null;
      }
      if (data) {
        dispatch({ type: 'ADD_FIELD', payload: data });
        showToast('success', `Field "${data.name}" created successfully`);
      }
      dispatch({ type: 'SET_LOADING', payload: false });
      return data;
    },
    [showToast]
  );

  const updateField = useCallback(
    async (id: string, field: FieldBoundary) => {
      dispatch({ type: 'SET_LOADING', payload: true });
      const { data, error } = await fieldApi.updateField(id, field);
      if (error) {
        showToast('error', `Failed to update field: ${error}`);
      } else if (data) {
        dispatch({ type: 'UPDATE_FIELD', payload: data });
        showToast('success', `Field "${data.name}" updated`);
      }
      dispatch({ type: 'SET_LOADING', payload: false });
    },
    [showToast]
  );

  const deleteField = useCallback(
    async (id: string) => {
      const field = state.fields.find((f) => f.id === id);
      dispatch({ type: 'SET_LOADING', payload: true });
      const { error } = await fieldApi.deleteField(id);
      if (error) {
        showToast('error', `Failed to delete field: ${error}`);
      } else {
        dispatch({ type: 'DELETE_FIELD', payload: id });
        showToast('success', `Field "${field?.name}" deleted`);
      }
      dispatch({ type: 'SET_LOADING', payload: false });
    },
    [state.fields, showToast]
  );

  const selectField = useCallback((id: string | null) => {
    dispatch({ type: 'SELECT_FIELD', payload: id });
  }, []);

  const setTool = useCallback((tool: DrawingTool) => {
    dispatch({ type: 'SET_TOOL', payload: tool });
  }, []);

  const addDrawingCoord = useCallback((coord: [number, number]) => {
    dispatch({ type: 'ADD_DRAWING_COORD', payload: coord });
  }, []);

  const finishDrawing = useCallback(
    async (name: string) => {
      if (state.drawingCoords.length < 3) {
        showToast('error', 'At least 3 points required');
        return;
      }

      const coords = [...state.drawingCoords, state.drawingCoords[0]];
      const field: Omit<FieldBoundary, 'id'> = {
        name,
        geometryType: state.activeTool as GeometryType,
        coordinates: [coords],
        metadata: { source: 'manual' },
      };

      const created = await createField(field);
      if (created) {
        dispatch({ type: 'CLEAR_DRAWING' });
        dispatch({ type: 'SELECT_FIELD', payload: created.id || null });
      }
    },
    [state.drawingCoords, state.activeTool, createField, showToast]
  );

  const cancelDrawing = useCallback(() => {
    dispatch({ type: 'CLEAR_DRAWING' });
  }, []);

  const autoDetect = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    const { data, error } = await fieldApi.autoDetect(true);
    if (error) {
      showToast('error', `Auto-detect failed: ${error}`);
    } else if (data) {
      data.fields.forEach((f) => dispatch({ type: 'ADD_FIELD', payload: f }));
      showToast('success', `Detected ${data.count} field(s)`);
    }
    dispatch({ type: 'SET_LOADING', payload: false });
  }, [showToast]);

  const splitIntoZones = useCallback(
    async (fieldId: string, zones: number) => {
      const field = state.fields.find((f) => f.id === fieldId);
      if (!field) return;

      dispatch({ type: 'SET_LOADING', payload: true });
      const { data, error } = await fieldApi.splitIntoZones(field, zones);
      if (error) {
        showToast('error', `Zone split failed: ${error}`);
      } else if (data) {
        data.fields.forEach((f) => dispatch({ type: 'ADD_FIELD', payload: f }));
        showToast('success', `Created ${data.count} zones`);
      }
      dispatch({ type: 'SET_LOADING', payload: false });
    },
    [state.fields, showToast]
  );

  // Initial load
  useEffect(() => {
    checkApiConnection();
    loadFields();
  }, [checkApiConnection, loadFields]);

  // Periodic health check
  useEffect(() => {
    const interval = setInterval(checkApiConnection, 30000);
    return () => clearInterval(interval);
  }, [checkApiConnection]);

  const value: FieldContextType = {
    state,
    loadFields,
    createField,
    updateField,
    deleteField,
    selectField,
    setTool,
    addDrawingCoord,
    finishDrawing,
    cancelDrawing,
    autoDetect,
    splitIntoZones,
    showToast,
    checkApiConnection,
  };

  return <FieldContext.Provider value={value}>{children}</FieldContext.Provider>;
};
