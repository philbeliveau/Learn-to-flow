import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { useAuthStore } from './auth-store';

interface PredictionResult {
  id: string;
  modelId: string;
  modelName: string;
  modelVersion: string;
  predictionType: 'quality' | 'maintenance' | 'anomaly';
  confidence: number;
  result: any;
  inputData: any;
  timestamp: Date;
  processingTime: number;
  features: Record<string, any>;
  explanation?: {
    topFeatures: Array<{
      feature: string;
      importance: number;
      direction: 'positive' | 'negative';
    }>;
    reasoning: string;
  };
}

interface MLModel {
  id: string;
  name: string;
  version: string;
  type: string;
  status: 'active' | 'training' | 'inactive';
  accuracy: number;
  lastTrained: Date;
  description: string;
}

interface PredictionState {
  predictions: PredictionResult[];
  isLoading: boolean;
  error: string | null;
  models: MLModel[];
  selectedModel: MLModel | null;
  filters: Record<string, any>;
}

interface PredictionStore extends PredictionState {
  fetchPredictions: () => Promise<void>;
  addPrediction: (prediction: PredictionResult) => void;
  updatePrediction: (id: string, updates: Partial<PredictionResult>) => void;
  deletePrediction: (id: string) => void;
  fetchModels: () => Promise<void>;
  selectModel: (model: MLModel) => void;
  updateFilters: (filters: Partial<PredictionState['filters']>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const usePredictionStore = create<PredictionStore>()(
  devtools(
    immer((set, get) => ({
      predictions: [],
      isLoading: false,
      error: null,
      models: [],
      selectedModel: null,
      filters: {},

      fetchPredictions: async () => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const { token } = useAuthStore.getState();
          const response = await fetch('/api/predictions', {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            throw new Error('Failed to fetch predictions');
          }

          const data = await response.json();
          
          set((state) => {
            state.predictions = data.data;
            state.isLoading = false;
          });
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Unknown error';
            state.isLoading = false;
          });
        }
      },

      addPrediction: (prediction) => {
        set((state) => {
          state.predictions.unshift(prediction);
        });
      },

      updatePrediction: (id, updates) => {
        set((state) => {
          const index = state.predictions.findIndex((p: PredictionResult) => p.id === id);
          if (index !== -1) {
            state.predictions[index] = { ...state.predictions[index], ...updates };
          }
        });
      },

      deletePrediction: (id) => {
        set((state) => {
          state.predictions = state.predictions.filter((p: PredictionResult) => p.id !== id);
        });
      },

      fetchModels: async () => {
        try {
          const { token } = useAuthStore.getState();
          const response = await fetch('/api/models', {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            throw new Error('Failed to fetch models');
          }

          const data = await response.json();
          
          set((state) => {
            state.models = data.data;
          });
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Unknown error';
          });
        }
      },

      selectModel: (model) => {
        set((state) => {
          state.selectedModel = model;
        });
      },

      updateFilters: (filters) => {
        set((state) => {
          state.filters = { ...state.filters, ...filters };
        });
      },

      setLoading: (loading) => {
        set((state) => {
          state.isLoading = loading;
        });
      },

      setError: (error) => {
        set((state) => {
          state.error = error;
        });
      },
    })),
    { name: 'prediction-store' }
  )
);