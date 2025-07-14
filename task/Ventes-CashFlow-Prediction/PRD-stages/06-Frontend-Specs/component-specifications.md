# 🎨 SPÉCIFICATIONS FRONTEND - EZBI ANALYTICS

## 🎯 ARCHITECTURE FRONTEND

### Next.js 14 App Router Structure
```
📁 Frontend Architecture Complète

ezbi-frontend/
├── app/                          # App Router (Next.js 14)
│   ├── (auth)/                   # Route Groups
│   │   ├── login/
│   │   │   ├── page.tsx
│   │   │   └── loading.tsx
│   │   ├── register/
│   │   │   ├── page.tsx
│   │   │   └── components/
│   │   └── layout.tsx
│   │
│   ├── (dashboard)/              # Protected Routes
│   │   ├── dashboard/
│   │   │   ├── page.tsx
│   │   │   ├── loading.tsx
│   │   │   └── components/
│   │   ├── predictions/
│   │   │   ├── page.tsx
│   │   │   ├── [id]/
│   │   │   └── components/
│   │   ├── upload/
│   │   │   ├── page.tsx
│   │   │   └── components/
│   │   ├── analytics/
│   │   │   ├── page.tsx
│   │   │   └── components/
│   │   ├── settings/
│   │   │   ├── page.tsx
│   │   │   └── components/
│   │   └── layout.tsx
│   │
│   ├── api/                      # API Routes
│   │   ├── auth/
│   │   ├── predictions/
│   │   ├── upload/
│   │   └── webhooks/
│   │
│   ├── globals.css
│   ├── layout.tsx
│   ├── page.tsx
│   └── not-found.tsx
│
├── components/                   # Reusable Components
│   ├── ui/                      # Shadcn/ui Components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   ├── table.tsx
│   │   └── dialog.tsx
│   │
│   ├── charts/                  # Chart Components
│   │   ├── PredictionChart.tsx
│   │   ├── CashFlowChart.tsx
│   │   ├── ConfidenceChart.tsx
│   │   └── TrendChart.tsx
│   │
│   ├── forms/                   # Form Components
│   │   ├── UploadForm.tsx
│   │   ├── PredictionForm.tsx
│   │   └── SettingsForm.tsx
│   │
│   ├── layout/                  # Layout Components
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   ├── Footer.tsx
│   │   └── Navigation.tsx
│   │
│   └── features/                # Feature Components
│       ├── PredictionCard.tsx
│       ├── SmartUploadZone.tsx
│       ├── AIInsights.tsx
│       └── ConfidenceIndicator.tsx
│
├── hooks/                       # Custom Hooks
│   ├── useAuth.ts
│   ├── usePredictions.ts
│   ├── useUpload.ts
│   └── useWebSocket.ts
│
├── lib/                         # Utilities
│   ├── auth.ts
│   ├── api.ts
│   ├── utils.ts
│   ├── validations.ts
│   └── constants.ts
│
├── store/                       # State Management
│   ├── authStore.ts
│   ├── predictionStore.ts
│   ├── uploadStore.ts
│   └── uiStore.ts
│
├── types/                       # TypeScript Types
│   ├── auth.ts
│   ├── predictions.ts
│   ├── api.ts
│   └── common.ts
│
└── styles/                      # Styling
    ├── globals.css
    ├── components.css
    └── utilities.css
```

---

## 🧩 COMPOSANTS SIGNATURE

### PredictionCard - Composant Principal
```typescript
// 🎯 PredictionCard.tsx - Composant signature d'EZBI

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PredictionCardProps {
  prediction: {
    id: string;
    targetDate: string;
    predictedValue: number;
    confidence: number;
    trend: 'up' | 'down' | 'stable';
    variance: number;
    modelType: 'prophet' | 'lstm' | 'ensemble';
    accuracy: number;
    factors: string[];
  };
  variant?: 'default' | 'compact' | 'detailed';
  className?: string;
}

export const PredictionCard: React.FC<PredictionCardProps> = ({
  prediction,
  variant = 'default',
  className
}) => {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'bg-confidence-high-500';
    if (confidence >= 0.7) return 'bg-confidence-medium-500';
    return 'bg-confidence-low-500';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.9) return 'Très élevée';
    if (confidence >= 0.7) return 'Élevée';
    if (confidence >= 0.5) return 'Moyenne';
    return 'Faible';
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'down': return <TrendingDown className="h-4 w-4 text-red-500" />;
      default: return <div className="h-4 w-4 bg-gray-400 rounded-full" />;
    }
  };

  const getModelBadge = (modelType: string) => {
    const variants = {
      'prophet': 'bg-blue-100 text-blue-800',
      'lstm': 'bg-purple-100 text-purple-800',
      'ensemble': 'bg-green-100 text-green-800'
    };
    return variants[modelType as keyof typeof variants] || 'bg-gray-100 text-gray-800';
  };

  if (variant === 'compact') {
    return (
      <Card className={cn('w-full', className)}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {getTrendIcon(prediction.trend)}
              <span className="text-lg font-semibold">
                {new Intl.NumberFormat('fr-FR', {
                  style: 'currency',
                  currency: 'EUR'
                }).format(prediction.predictedValue)}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <div className={cn(
                'h-2 w-2 rounded-full',
                getConfidenceColor(prediction.confidence)
              )} />
              <span className="text-sm text-gray-500">
                {Math.round(prediction.confidence * 100)}%
              </span>
            </div>
          </div>
          <div className="mt-2 text-sm text-gray-600">
            {new Date(prediction.targetDate).toLocaleDateString('fr-FR', {
              day: 'numeric',
              month: 'long',
              year: 'numeric'
            })}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn('w-full hover:shadow-lg transition-shadow', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center space-x-2">
            {getTrendIcon(prediction.trend)}
            <span>Prédiction Cash Flow</span>
          </CardTitle>
          <Badge className={getModelBadge(prediction.modelType)}>
            {prediction.modelType.toUpperCase()}
          </Badge>
        </div>
        <div className="text-sm text-gray-500">
          {new Date(prediction.targetDate).toLocaleDateString('fr-FR', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
          })}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Montant Prédit */}
        <div className="text-center">
          <div className="text-3xl font-bold text-ezbi-primary-600">
            {new Intl.NumberFormat('fr-FR', {
              style: 'currency',
              currency: 'EUR'
            }).format(prediction.predictedValue)}
          </div>
          <div className="text-sm text-gray-500 mt-1">
            ±{new Intl.NumberFormat('fr-FR', {
              style: 'currency',
              currency: 'EUR'
            }).format(prediction.variance)}
          </div>
        </div>

        {/* Niveau de Confiance */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Niveau de confiance</span>
            <span className="text-sm font-semibold">
              {getConfidenceLabel(prediction.confidence)}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={cn(
                'h-2 rounded-full transition-all',
                getConfidenceColor(prediction.confidence)
              )}
              style={{ width: `${prediction.confidence * 100}%` }}
            />
          </div>
          <div className="text-xs text-gray-500 text-center">
            {Math.round(prediction.confidence * 100)}% de confiance
          </div>
        </div>

        {/* Précision Historique */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <span className="text-sm font-medium">Précision historique</span>
          </div>
          <span className="text-sm font-semibold text-green-600">
            {Math.round(prediction.accuracy * 100)}%
          </span>
        </div>

        {/* Facteurs Clés */}
        {variant === 'detailed' && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Facteurs influents</h4>
            <div className="flex flex-wrap gap-2">
              {prediction.factors.map((factor, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {factor}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
```

### SmartUploadZone - Upload Intelligent
```typescript
// 🚀 SmartUploadZone.tsx - Upload intelligent avec IA

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

interface SmartUploadZoneProps {
  onUpload: (file: File) => Promise<UploadResult>;
  acceptedTypes?: string[];
  maxSize?: number;
  className?: string;
}

interface UploadResult {
  success: boolean;
  analysisResults?: {
    dataType: string;
    rowCount: number;
    columnCount: number;
    dateRange: {
      start: string;
      end: string;
    };
    detectedColumns: string[];
    dataQuality: number;
    suggestions: string[];
  };
  error?: string;
}

export const SmartUploadZone: React.FC<SmartUploadZoneProps> = ({
  onUpload,
  acceptedTypes = ['.xlsx', '.xls', '.csv'],
  maxSize = 10 * 1024 * 1024, // 10MB
  className
}) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setProgress(0);
    setResult(null);

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const uploadResult = await onUpload(file);
      
      clearInterval(progressInterval);
      setProgress(100);
      setResult(uploadResult);
    } catch (error) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : 'Erreur lors du téléchargement'
      });
    } finally {
      setUploading(false);
    }
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv']
    },
    maxSize,
    multiple: false,
    onDragEnter: () => setDragActive(true),
    onDragLeave: () => setDragActive(false)
  });

  const getQualityColor = (quality: number) => {
    if (quality >= 0.8) return 'text-green-600';
    if (quality >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getQualityLabel = (quality: number) => {
    if (quality >= 0.8) return 'Excellente';
    if (quality >= 0.6) return 'Bonne';
    if (quality >= 0.4) return 'Moyenne';
    return 'Faible';
  };

  if (result?.success && result.analysisResults) {
    return (
      <Card className={cn('w-full', className)}>
        <CardContent className="p-6">
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <h3 className="text-lg font-semibold">Analyse complétée</h3>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="text-sm text-gray-500">Type de données</div>
                <Badge variant="secondary">{result.analysisResults.dataType}</Badge>
              </div>
              <div className="space-y-2">
                <div className="text-sm text-gray-500">Qualité des données</div>
                <div className={cn(
                  'font-semibold',
                  getQualityColor(result.analysisResults.dataQuality)
                )}>
                  {getQualityLabel(result.analysisResults.dataQuality)} ({Math.round(result.analysisResults.dataQuality * 100)}%)
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="text-sm text-gray-500">Nombre de lignes</div>
                <div className="font-semibold">
                  {result.analysisResults.rowCount.toLocaleString('fr-FR')}
                </div>
              </div>
              <div className="space-y-2">
                <div className="text-sm text-gray-500">Période couverte</div>
                <div className="font-semibold">
                  {new Date(result.analysisResults.dateRange.start).toLocaleDateString('fr-FR')} - {new Date(result.analysisResults.dateRange.end).toLocaleDateString('fr-FR')}
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-sm text-gray-500">Colonnes détectées</div>
              <div className="flex flex-wrap gap-2">
                {result.analysisResults.detectedColumns.map((column, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {column}
                  </Badge>
                ))}
              </div>
            </div>

            {result.analysisResults.suggestions.length > 0 && (
              <div className="space-y-2">
                <div className="text-sm text-gray-500">Recommandations</div>
                <div className="space-y-1">
                  {result.analysisResults.suggestions.map((suggestion, index) => (
                    <div key={index} className="flex items-start space-x-2">
                      <AlertCircle className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm">{suggestion}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex space-x-2">
              <Button onClick={() => setResult(null)} variant="outline">
                Télécharger un autre fichier
              </Button>
              <Button>
                Générer les prédictions
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn('w-full', className)}>
      <CardContent className="p-6">
        <div
          {...getRootProps()}
          className={cn(
            'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
            dragActive || isDragActive
              ? 'border-ezbi-primary-500 bg-ezbi-primary-50'
              : 'border-gray-300 hover:border-ezbi-primary-400',
            uploading && 'pointer-events-none'
          )}
        >
          <input {...getInputProps()} />
          
          {uploading ? (
            <div className="space-y-4">
              <Loader2 className="h-12 w-12 mx-auto text-ezbi-primary-500 animate-spin" />
              <div className="space-y-2">
                <div className="text-lg font-semibold">Analyse en cours...</div>
                <div className="text-sm text-gray-500">
                  L'IA analyse votre fichier et détecte la structure des données
                </div>
                <Progress value={progress} className="w-full max-w-xs mx-auto" />
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex justify-center">
                <div className="p-4 bg-ezbi-primary-100 rounded-full">
                  <Upload className="h-8 w-8 text-ezbi-primary-600" />
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="text-lg font-semibold">
                  Glissez votre fichier ici ou cliquez pour sélectionner
                </div>
                <div className="text-sm text-gray-500">
                  Formats acceptés: {acceptedTypes.join(', ')}
                </div>
                <div className="text-xs text-gray-400">
                  Taille maximale: {Math.round(maxSize / 1024 / 1024)}MB
                </div>
              </div>

              <div className="flex items-center justify-center space-x-4 text-xs text-gray-500">
                <div className="flex items-center space-x-1">
                  <FileText className="h-3 w-3" />
                  <span>Excel, CSV</span>
                </div>
                <div className="flex items-center space-x-1">
                  <CheckCircle className="h-3 w-3" />
                  <span>Sécurisé</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Upload className="h-3 w-3" />
                  <span>Analyse IA</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {result?.error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-500" />
              <div className="text-sm text-red-700">
                Erreur: {result.error}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
```

### ConfidenceIndicator - Indicateur de Confiance
```typescript
// 🎯 ConfidenceIndicator.tsx - Indicateur de confiance IA

import React from 'react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface ConfidenceIndicatorProps {
  confidence: number;
  accuracy?: number;
  modelType?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'bar' | 'circle' | 'badge';
  showLabel?: boolean;
  className?: string;
}

export const ConfidenceIndicator: React.FC<ConfidenceIndicatorProps> = ({
  confidence,
  accuracy,
  modelType,
  size = 'md',
  variant = 'bar',
  showLabel = true,
  className
}) => {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return {
      bg: 'bg-confidence-high-500',
      text: 'text-confidence-high-700',
      border: 'border-confidence-high-200'
    };
    if (confidence >= 0.7) return {
      bg: 'bg-confidence-medium-500',
      text: 'text-confidence-medium-700',
      border: 'border-confidence-medium-200'
    };
    if (confidence >= 0.5) return {
      bg: 'bg-confidence-low-500',
      text: 'text-confidence-low-700',
      border: 'border-confidence-low-200'
    };
    return {
      bg: 'bg-red-500',
      text: 'text-red-700',
      border: 'border-red-200'
    };
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.9) return 'Très élevée';
    if (confidence >= 0.7) return 'Élevée';
    if (confidence >= 0.5) return 'Moyenne';
    return 'Faible';
  };

  const colors = getConfidenceColor(confidence);
  const confidencePercent = Math.round(confidence * 100);

  const sizeClasses = {
    sm: 'h-2 text-xs',
    md: 'h-3 text-sm',
    lg: 'h-4 text-base'
  };

  if (variant === 'circle') {
    const circleSize = size === 'sm' ? 'w-8 h-8' : size === 'md' ? 'w-12 h-12' : 'w-16 h-16';
    const strokeWidth = size === 'sm' ? 4 : size === 'md' ? 6 : 8;
    const radius = size === 'sm' ? 12 : size === 'md' ? 18 : 24;
    const circumference = 2 * Math.PI * radius;
    const strokeDasharray = circumference;
    const strokeDashoffset = circumference - (confidence * circumference);

    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className={cn('relative', circleSize, className)}>
              <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r={radius}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={strokeWidth}
                  className="text-gray-200"
                />
                <circle
                  cx="50"
                  cy="50"
                  r={radius}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={strokeWidth}
                  strokeDasharray={strokeDasharray}
                  strokeDashoffset={strokeDashoffset}
                  className={colors.text}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className={cn('font-semibold', sizeClasses[size], colors.text)}>
                  {confidencePercent}%
                </span>
              </div>
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <div className="space-y-1">
              <div>Confiance: {getConfidenceLabel(confidence)}</div>
              {accuracy && <div>Précision: {Math.round(accuracy * 100)}%</div>}
              {modelType && <div>Modèle: {modelType.toUpperCase()}</div>}
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  if (variant === 'badge') {
    return (
      <Badge 
        variant="secondary" 
        className={cn(
          'border-2',
          colors.border,
          colors.text,
          className
        )}
      >
        {confidencePercent}% confiance
      </Badge>
    );
  }

  // Default: bar variant
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={cn('space-y-1', className)}>
            {showLabel && (
              <div className="flex justify-between items-center">
                <span className={cn('font-medium', sizeClasses[size])}>
                  Confiance
                </span>
                <span className={cn('font-semibold', sizeClasses[size], colors.text)}>
                  {getConfidenceLabel(confidence)}
                </span>
              </div>
            )}
            <div className={cn('w-full bg-gray-200 rounded-full', sizeClasses[size])}>
              <div
                className={cn(
                  'rounded-full transition-all duration-300',
                  colors.bg,
                  sizeClasses[size]
                )}
                style={{ width: `${confidencePercent}%` }}
              />
            </div>
            {showLabel && (
              <div className="text-xs text-gray-500 text-center">
                {confidencePercent}% de confiance
              </div>
            )}
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <div className="space-y-1">
            <div>Niveau de confiance: {confidencePercent}%</div>
            <div>Qualité: {getConfidenceLabel(confidence)}</div>
            {accuracy && <div>Précision historique: {Math.round(accuracy * 100)}%</div>}
            {modelType && <div>Modèle utilisé: {modelType.toUpperCase()}</div>}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};
```

---

## 📊 GRAPHIQUES ET VISUALISATIONS

### CashFlowChart - Graphique Principal
```typescript
// 📊 CashFlowChart.tsx - Graphique de flux de trésorerie

import React from 'react';
import { Line, LineChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface CashFlowChartProps {
  data: Array<{
    date: string;
    actual?: number;
    predicted: number;
    confidence_lower: number;
    confidence_upper: number;
  }>;
  title?: string;
  height?: number;
  showConfidenceInterval?: boolean;
  className?: string;
}

export const CashFlowChart: React.FC<CashFlowChartProps> = ({
  data,
  title = 'Prédiction de Flux de Trésorerie',
  height = 400,
  showConfidenceInterval = true,
  className
}) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      notation: 'compact'
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short'
    });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-4 border rounded-lg shadow-lg">
          <p className="font-semibold">{formatDate(label)}</p>
          {data.actual && (
            <p className="text-green-600">
              Réel: {formatCurrency(data.actual)}
            </p>
          )}
          <p className="text-ezbi-primary-600">
            Prédit: {formatCurrency(data.predicted)}
          </p>
          {showConfidenceInterval && (
            <p className="text-gray-500 text-sm">
              Intervalle: {formatCurrency(data.confidence_lower)} - {formatCurrency(data.confidence_upper)}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>{title}</CardTitle>
          <div className="flex space-x-2">
            <Badge variant="outline">
              Données réelles
            </Badge>
            <Badge variant="secondary">
              Prédictions IA
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis 
              dataKey="date" 
              tickFormatter={formatDate}
              className="text-sm"
            />
            <YAxis 
              tickFormatter={formatCurrency}
              className="text-sm"
            />
            <Tooltip content={<CustomTooltip />} />
            
            {/* Intervalle de confiance */}
            {showConfidenceInterval && (
              <Area
                type="monotone"
                dataKey="confidence_upper"
                stroke="none"
                fill="url(#confidenceGradient)"
                fillOpacity={0.2}
              />
            )}
            
            {/* Ligne des prédictions */}
            <Line
              type="monotone"
              dataKey="predicted"
              stroke="#1B365D"
              strokeWidth={2}
              dot={{ fill: '#1B365D', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, fill: '#1B365D' }}
            />
            
            {/* Ligne des données réelles */}
            <Line
              type="monotone"
              dataKey="actual"
              stroke="#2E8B57"
              strokeWidth={2}
              dot={{ fill: '#2E8B57', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, fill: '#2E8B57' }}
            />
            
            {/* Gradients pour l'intervalle de confiance */}
            <defs>
              <linearGradient id="confidenceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#1B365D" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#1B365D" stopOpacity={0.1} />
              </linearGradient>
            </defs>
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};
```

---

## 🎛️ GESTION D'ÉTAT

### Store Principal avec Zustand
```typescript
// 🎛️ Store principal avec Zustand

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  name: string;
  email: string;
  company: {
    id: string;
    name: string;
    sector: string;
  };
}

interface Prediction {
  id: string;
  targetDate: string;
  predictedValue: number;
  confidence: number;
  modelType: string;
  createdAt: string;
}

interface AppState {
  // Auth
  user: User | null;
  isAuthenticated: boolean;
  
  // Predictions
  predictions: Prediction[];
  currentPrediction: Prediction | null;
  
  // Upload
  uploadProgress: number;
  isUploading: boolean;
  
  // UI
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  
  // Actions
  setUser: (user: User | null) => void;
  setPredictions: (predictions: Prediction[]) => void;
  addPrediction: (prediction: Prediction) => void;
  setCurrentPrediction: (prediction: Prediction | null) => void;
  setUploadProgress: (progress: number) => void;
  setIsUploading: (isUploading: boolean) => void;
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      predictions: [],
      currentPrediction: null,
      uploadProgress: 0,
      isUploading: false,
      sidebarOpen: true,
      theme: 'light',
      
      // Actions
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      
      setPredictions: (predictions) => set({ predictions }),
      
      addPrediction: (prediction) => set((state) => ({
        predictions: [prediction, ...state.predictions]
      })),
      
      setCurrentPrediction: (currentPrediction) => set({ currentPrediction }),
      
      setUploadProgress: (uploadProgress) => set({ uploadProgress }),
      
      setIsUploading: (isUploading) => set({ isUploading }),
      
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      
      setTheme: (theme) => set({ theme })
    }),
    {
      name: 'ezbi-app-store',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        theme: state.theme,
        sidebarOpen: state.sidebarOpen
      })
    }
  )
);
```

---

## 🔐 HOOKS PERSONNALISÉS

### useAuth Hook
```typescript
// 🔐 useAuth.ts - Hook d'authentification

import { useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/store/appStore';

interface LoginCredentials {
  email: string;
  password: string;
}

interface RegisterData {
  name: string;
  email: string;
  password: string;
  companyName: string;
  companySize: string;
}

export const useAuth = () => {
  const router = useRouter();
  const { user, isAuthenticated, setUser } = useAppStore();

  const login = useCallback(async (credentials: LoginCredentials) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        throw new Error('Échec de la connexion');
      }

      const { user, token } = await response.json();
      
      // Store token
      localStorage.setItem('auth_token', token);
      
      // Update store
      setUser(user);
      
      // Redirect to dashboard
      router.push('/dashboard');
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Erreur inconnue' 
      };
    }
  }, [router, setUser]);

  const register = useCallback(async (data: RegisterData) => {
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Échec de l\'inscription');
      }

      const { user, token } = await response.json();
      
      // Store token
      localStorage.setItem('auth_token', token);
      
      // Update store
      setUser(user);
      
      // Redirect to dashboard
      router.push('/dashboard');
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Erreur inconnue' 
      };
    }
  }, [router, setUser]);

  const logout = useCallback(() => {
    localStorage.removeItem('auth_token');
    setUser(null);
    router.push('/login');
  }, [router, setUser]);

  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
      return false;
    }

    try {
      const response = await fetch('/api/auth/verify', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Token invalide');
      }

      const { user } = await response.json();
      setUser(user);
      return true;
    } catch (error) {
      localStorage.removeItem('auth_token');
      setUser(null);
      return false;
    }
  }, [setUser]);

  // Check auth on mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return {
    user,
    isAuthenticated,
    login,
    register,
    logout,
    checkAuth
  };
};
```

Cette spécification frontend complète fournit tous les composants, hooks et architecture nécessaires pour construire l'interface utilisateur d'EZBI Analytics avec une approche manufacturing-first et une expérience utilisateur optimisée.