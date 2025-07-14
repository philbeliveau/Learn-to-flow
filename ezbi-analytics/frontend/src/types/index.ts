// Core Types for EZBI Analytics
export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'admin' | 'manager' | 'analyst' | 'operator';
  company?: string;
  department?: string;
  avatar?: string;
  lastLogin?: Date;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

// Manufacturing Data Types
export interface ManufacturingData {
  id: string;
  timestamp: Date;
  productionLine: string;
  batchId: string;
  parameters: {
    temperature: number;
    pressure: number;
    humidity: number;
    vibration: number;
    speed: number;
    [key: string]: number | string | boolean;
  };
  qualityMetrics: {
    defectRate: number;
    efficiency: number;
    yield: number;
    throughput: number;
  };
  sensorData: SensorReading[];
  alerts: Alert[];
  metadata: {
    operator: string;
    shift: 'day' | 'night' | 'swing';
    product: string;
    version: string;
  };
}

export interface SensorReading {
  id: string;
  sensorId: string;
  sensorType: 'temperature' | 'pressure' | 'vibration' | 'flow' | 'level';
  value: number;
  unit: string;
  timestamp: Date;
  status: 'normal' | 'warning' | 'critical';
  calibrationDate?: Date;
}

export interface Alert {
  id: string;
  type: 'warning' | 'error' | 'info' | 'critical';
  message: string;
  source: string;
  timestamp: Date;
  acknowledged: boolean;
  resolvedAt?: Date;
  severity: 1 | 2 | 3 | 4 | 5;
  category: 'quality' | 'maintenance' | 'production' | 'safety';
}

// AI Prediction Types
export interface PredictionResult {
  id: string;
  modelId: string;
  modelName: string;
  modelVersion: string;
  predictionType: 'quality' | 'maintenance' | 'demand' | 'anomaly';
  confidence: number;
  result: {
    prediction: number | string | boolean;
    probability?: number;
    alternatives?: Array<{
      value: number | string | boolean;
      probability: number;
    }>;
  };
  inputData: ManufacturingData;
  timestamp: Date;
  processingTime: number;
  features: {
    [key: string]: number | string | boolean;
  };
  explanation?: {
    topFeatures: Array<{
      feature: string;
      importance: number;
      direction: 'positive' | 'negative';
    }>;
    reasoning: string;
  };
}

export interface MLModel {
  id: string;
  name: string;
  version: string;
  type: 'classification' | 'regression' | 'clustering' | 'anomaly';
  description: string;
  algorithm: string;
  status: 'training' | 'active' | 'deprecated' | 'error';
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  trainingDate: Date;
  lastUsed: Date;
  inputFeatures: string[];
  outputType: string;
  parameters: {
    [key: string]: any;
  };
  metrics: {
    [key: string]: number;
  };
}

// Component Props Types
export interface PredictionCardProps {
  prediction: PredictionResult;
  onDetailsClick?: (prediction: PredictionResult) => void;
  onRerun?: (predictionId: string) => void;
  className?: string;
}

export interface ConfidenceIndicatorProps {
  confidence: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  showPercentage?: boolean;
  threshold?: {
    low: number;
    medium: number;
    high: number;
  };
  className?: string;
}

export interface SmartUploadZoneProps {
  onFileUpload: (files: File[]) => void;
  onDataParsed?: (data: ManufacturingData[]) => void;
  acceptedTypes?: string[];
  maxSize?: number;
  maxFiles?: number;
  autoProcess?: boolean;
  className?: string;
}

// State Management Types
export interface AppState {
  auth: AuthState;
  dashboard: DashboardState;
  predictions: PredictionState;
  data: DataState;
  ui: UIState;
}

export interface DashboardState {
  currentView: 'overview' | 'analytics' | 'models' | 'alerts';
  selectedTimeRange: '1h' | '24h' | '7d' | '30d' | 'custom';
  customTimeRange?: {
    start: Date;
    end: Date;
  };
  filters: {
    productionLine?: string[];
    product?: string[];
    shift?: ('day' | 'night' | 'swing')[];
    operator?: string[];
  };
  refreshInterval: number;
  isRealTime: boolean;
}

export interface PredictionState {
  predictions: PredictionResult[];
  isLoading: boolean;
  error: string | null;
  models: MLModel[];
  selectedModel: MLModel | null;
  filters: {
    type?: string[];
    confidence?: [number, number];
    timeRange?: {
      start: Date;
      end: Date;
    };
  };
}

export interface DataState {
  manufacturingData: ManufacturingData[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  totalRecords: number;
  pageSize: number;
  currentPage: number;
  searchQuery: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

export interface UIState {
  theme: 'light' | 'dark' | 'system';
  language: 'en' | 'fr';
  sidebarCollapsed: boolean;
  notifications: Notification[];
  modals: {
    [key: string]: {
      isOpen: boolean;
      data?: any;
    };
  };
  toast: {
    isVisible: boolean;
    type: 'success' | 'error' | 'warning' | 'info';
    message: string;
    duration?: number;
  };
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  actionUrl?: string;
  actionText?: string;
}

// API Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  pagination?: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
}

export interface ApiError {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
}

// Form Types
export interface LoginFormData {
  email: string;
  password: string;
  remember?: boolean;
}

export interface RegisterFormData {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
  company?: string;
  department?: string;
  role: string;
}

export interface ResetPasswordFormData {
  email: string;
}

export interface ChangePasswordFormData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

// Utility Types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type Timestamp = string | Date;

export interface SelectOption<T = string> {
  value: T;
  label: string;
  disabled?: boolean;
  icon?: string;
}

// Chart Types
export interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
    fill?: boolean;
    tension?: number;
  }>;
}

export interface ChartOptions {
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  plugins?: {
    legend?: {
      display?: boolean;
      position?: 'top' | 'bottom' | 'left' | 'right';
    };
    title?: {
      display?: boolean;
      text?: string;
    };
  };
  scales?: {
    x?: {
      display?: boolean;
      title?: {
        display?: boolean;
        text?: string;
      };
    };
    y?: {
      display?: boolean;
      title?: {
        display?: boolean;
        text?: string;
      };
    };
  };
}

// PWA Types
export interface PWAInstallPrompt {
  platforms: string[];
  userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}

declare global {
  interface Window {
    deferredPrompt: PWAInstallPrompt;
  }
}

export interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}