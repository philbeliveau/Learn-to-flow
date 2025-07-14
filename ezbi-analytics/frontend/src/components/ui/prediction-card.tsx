'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  BarChart3,
  Lightbulb,
  Settings,
  ArrowRight
} from 'lucide-react';
import { PredictionCardProps, PredictionResult } from '@/types';
import { cn, formatPercentage, formatDateTime, getTimeAgo } from '@/lib/utils';
import { ConfidenceIndicator } from './confidence-indicator';

const predictionTypeIcons = {
  quality: CheckCircle,
  maintenance: Settings,
  demand: TrendingUp,
  anomaly: AlertTriangle,
};

const predictionTypeColors = {
  quality: 'text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-900/20',
  maintenance: 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20',
  demand: 'text-purple-600 bg-purple-50 dark:text-purple-400 dark:bg-purple-900/20',
  anomaly: 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900/20',
};

const predictionLabels = {
  quality: 'Qualité',
  maintenance: 'Maintenance',
  demand: 'Demande',
  anomaly: 'Anomalie',
};

export function PredictionCard({ 
  prediction, 
  onDetailsClick, 
  onRerun, 
  className 
}: PredictionCardProps) {
  const Icon = predictionTypeIcons[prediction.predictionType];
  const typeColor = predictionTypeColors[prediction.predictionType];
  const typeLabel = predictionLabels[prediction.predictionType];
  
  const handleDetailsClick = () => {
    onDetailsClick?.(prediction);
  };
  
  const handleRerun = () => {
    onRerun?.(prediction.id);
  };
  
  const getResultDisplay = () => {
    const { result } = prediction;
    
    if (typeof result.prediction === 'number') {
      if (prediction.predictionType === 'quality') {
        return formatPercentage(result.prediction);
      } else if (prediction.predictionType === 'demand') {
        return `${result.prediction.toFixed(0)} unités`;
      } else {
        return result.prediction.toFixed(2);
      }
    }
    
    return result.prediction.toString();
  };
  
  const getResultTrend = () => {
    if (prediction.predictionType === 'quality') {
      return prediction.result.prediction as number > 0.8 ? 'positive' : 'negative';
    } else if (prediction.predictionType === 'demand') {
      return prediction.result.prediction as number > 100 ? 'positive' : 'negative';
    } else if (prediction.predictionType === 'anomaly') {
      return prediction.result.prediction as boolean ? 'negative' : 'positive';
    }
    return 'neutral';
  };
  
  const trend = getResultTrend();
  const TrendIcon = trend === 'positive' ? TrendingUp : trend === 'negative' ? TrendingDown : BarChart3;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'card group cursor-pointer hover:shadow-md transition-all duration-200',
        'border-l-4 border-l-primary-500',
        className
      )}
      onClick={handleDetailsClick}
    >
      <div className="card-body p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={cn('p-2 rounded-lg', typeColor)}>
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">
                {typeLabel}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {prediction.modelName} v{prediction.modelVersion}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <ConfidenceIndicator 
              confidence={prediction.confidence}
              size="sm"
              showPercentage
            />
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleRerun();
              }}
              className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              title="Relancer la prédiction"
            >
              <Clock className="w-4 h-4 text-gray-500" />
            </button>
          </div>
        </div>
        
        {/* Result */}
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendIcon className={cn(
              'w-5 h-5',
              trend === 'positive' ? 'text-green-600' : 
              trend === 'negative' ? 'text-red-600' : 'text-gray-600'
            )} />
            <span className="text-2xl font-bold text-gray-900 dark:text-white">
              {getResultDisplay()}
            </span>
          </div>
          
          {prediction.result.probability && (
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Probabilité: {formatPercentage(prediction.result.probability)}
            </div>
          )}
        </div>
        
        {/* Alternatives */}
        {prediction.result.alternatives && prediction.result.alternatives.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Alternatives:
            </h4>
            <div className="space-y-1">
              {prediction.result.alternatives.slice(0, 2).map((alt, index) => (
                <div key={index} className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">
                    {alt.value.toString()}
                  </span>
                  <span className="text-gray-500 dark:text-gray-500">
                    {formatPercentage(alt.probability)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Explanation */}
        {prediction.explanation && (
          <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
            <div className="flex items-start gap-2">
              <Lightbulb className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Explication
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {prediction.explanation.reasoning}
                </p>
                
                {prediction.explanation.topFeatures && (
                  <div className="mt-2 space-y-1">
                    {prediction.explanation.topFeatures.slice(0, 3).map((feature, index) => (
                      <div key={index} className="flex items-center gap-2 text-xs">
                        <span className={cn(
                          'w-2 h-2 rounded-full',
                          feature.direction === 'positive' ? 'bg-green-500' : 'bg-red-500'
                        )} />
                        <span className="text-gray-600 dark:text-gray-400">
                          {feature.feature}
                        </span>
                        <span className="text-gray-500 dark:text-gray-500">
                          {(feature.importance * 100).toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
        
        {/* Metadata */}
        <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            <span>{getTimeAgo(prediction.timestamp)}</span>
          </div>
          
          <div className="flex items-center gap-2">
            <span>{prediction.processingTime}ms</span>
            <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>
      </div>
    </motion.div>
  );
}