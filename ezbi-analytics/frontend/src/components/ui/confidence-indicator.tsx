'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ConfidenceIndicatorProps } from '@/types';
import { cn, formatPercentage } from '@/lib/utils';

const defaultThreshold = {
  low: 0.6,
  medium: 0.8,
  high: 0.95,
};

export function ConfidenceIndicator({
  confidence,
  size = 'md',
  showLabel = false,
  showPercentage = false,
  threshold = defaultThreshold,
  className
}: ConfidenceIndicatorProps) {
  const getConfidenceLevel = () => {
    if (confidence >= threshold.high) return 'high';
    if (confidence >= threshold.medium) return 'medium';
    return 'low';
  };
  
  const getConfidenceColor = () => {
    const level = getConfidenceLevel();
    switch (level) {
      case 'high':
        return 'text-green-600 dark:text-green-400';
      case 'medium':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'low':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };
  
  const getConfidenceRingColor = () => {
    const level = getConfidenceLevel();
    switch (level) {
      case 'high':
        return 'stroke-green-600 dark:stroke-green-400';
      case 'medium':
        return 'stroke-yellow-600 dark:stroke-yellow-400';
      case 'low':
        return 'stroke-red-600 dark:stroke-red-400';
      default:
        return 'stroke-gray-600 dark:stroke-gray-400';
    }
  };
  
  const getConfidenceLabel = () => {
    const level = getConfidenceLevel();
    switch (level) {
      case 'high':
        return 'Élevée';
      case 'medium':
        return 'Moyenne';
      case 'low':
        return 'Faible';
      default:
        return 'Inconnue';
    }
  };
  
  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return {
          container: 'w-8 h-8',
          svg: 'w-8 h-8',
          text: 'text-xs',
          strokeWidth: 2,
          radius: 12,
        };
      case 'lg':
        return {
          container: 'w-16 h-16',
          svg: 'w-16 h-16',
          text: 'text-lg',
          strokeWidth: 3,
          radius: 28,
        };
      default: // md
        return {
          container: 'w-12 h-12',
          svg: 'w-12 h-12',
          text: 'text-sm',
          strokeWidth: 2.5,
          radius: 20,
        };
    }
  };
  
  const sizeClasses = getSizeClasses();
  const circumference = 2 * Math.PI * sizeClasses.radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (confidence * circumference);
  
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className={cn('relative', sizeClasses.container)}>
        <svg
          className={cn('transform -rotate-90', sizeClasses.svg)}
          viewBox="0 0 40 40"
        >
          {/* Background circle */}
          <circle
            cx="20"
            cy="20"
            r={sizeClasses.radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={sizeClasses.strokeWidth}
            className="text-gray-200 dark:text-gray-700"
          />
          
          {/* Progress circle */}
          <motion.circle
            cx="20"
            cy="20"
            r={sizeClasses.radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={sizeClasses.strokeWidth}
            strokeLinecap="round"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            className={getConfidenceRingColor()}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1, ease: "easeInOut" }}
          />
        </svg>
        
        {/* Percentage in center */}
        <div className={cn(
          'absolute inset-0 flex items-center justify-center',
          sizeClasses.text,
          'font-semibold',
          getConfidenceColor()
        )}>
          {Math.round(confidence * 100)}%
        </div>
      </div>
      
      {/* Label and percentage */}
      {(showLabel || showPercentage) && (
        <div className="flex flex-col">
          {showLabel && (
            <span className={cn(
              'text-sm font-medium',
              getConfidenceColor()
            )}>
              {getConfidenceLabel()}
            </span>
          )}
          {showPercentage && !showLabel && (
            <span className={cn(
              'text-sm font-medium',
              getConfidenceColor()
            )}>
              {formatPercentage(confidence)}
            </span>
          )}
        </div>
      )}
    </div>
  );
}