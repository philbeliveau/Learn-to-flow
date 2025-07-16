/**
 * 🛡️ Enhanced Error Boundary with Recovery Mechanisms
 * Catches and handles React errors with automatic recovery
 */

'use client';

import React, { ErrorInfo, ReactNode } from 'react';
import { robustApiService } from '../services/robustApiService';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  resetOnPropsChange?: boolean;
  resetTimeout?: number;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retryCount: number;
  lastError: number;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private resetTimeoutId: NodeJS.Timeout | null = null;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
      lastError: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
      lastError: Date.now()
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      errorInfo,
      retryCount: this.state.retryCount + 1
    });

    // Log error details
    console.error('ErrorBoundary caught an error:', error);
    console.error('Error info:', errorInfo);

    // Call custom error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Auto-retry mechanism
    if (this.state.retryCount < 3) {
      this.scheduleAutoRetry();
    }

    // Send error to monitoring service (if available)
    this.reportError(error, errorInfo);
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    // Reset error state when props change (if enabled)
    if (this.props.resetOnPropsChange && prevProps.children !== this.props.children) {
      if (this.state.hasError) {
        this.resetError();
      }
    }
  }

  componentWillUnmount() {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
  }

  private scheduleAutoRetry = () => {
    const timeout = this.props.resetTimeout || 5000;
    
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }

    this.resetTimeoutId = setTimeout(() => {
      console.log('ErrorBoundary: Attempting auto-retry...');
      this.resetError();
    }, timeout);
  };

  private reportError = async (error: Error, errorInfo: ErrorInfo) => {
    try {
      // Report to console in development
      if (process.env.NODE_ENV === 'development') {
        console.group('🚨 Error Boundary Report');
        console.error('Error:', error);
        console.error('Component Stack:', errorInfo.componentStack);
        console.error('Error Stack:', error.stack);
        console.groupEnd();
      }

      // In production, you would send this to your error tracking service
      // Example: Sentry, LogRocket, etc.
      
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  };

  private resetError = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });

    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
      this.resetTimeoutId = null;
    }
  };

  private handleRetry = () => {
    this.resetError();
  };

  private handleRefreshData = async () => {
    try {
      // Try to refresh critical data
      await robustApiService.clearCache();
      await robustApiService.testAllEndpoints();
      this.resetError();
    } catch (error) {
      console.error('Failed to refresh data:', error);
    }
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return <FallbackComponent error={this.state.error!} resetError={this.resetError} />;
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-black text-white flex items-center justify-center p-4">
          <div className="max-w-md w-full">
            <div className="bg-red-900/20 border border-red-500 rounded-lg p-6">
              <div className="flex items-center mb-4">
                <svg className="w-8 h-8 text-red-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <h2 className="text-xl font-semibold text-red-400">Something went wrong</h2>
              </div>
              
              <p className="text-red-300 mb-4">
                The application encountered an unexpected error. Don't worry, we can try to recover.
              </p>

              {this.state.error && (
                <div className="bg-red-800/30 border border-red-600 rounded p-3 mb-4">
                  <p className="text-red-200 text-sm font-mono">
                    {this.state.error.message}
                  </p>
                </div>
              )}

              <div className="flex flex-col gap-2">
                <button
                  onClick={this.handleRetry}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded transition-colors"
                >
                  Try Again
                </button>
                
                <button
                  onClick={this.handleRefreshData}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded transition-colors"
                >
                  Refresh Data
                </button>
                
                <button
                  onClick={() => window.location.reload()}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded transition-colors"
                >
                  Reload Page
                </button>
              </div>

              <div className="mt-4 pt-4 border-t border-red-500/30">
                <p className="text-red-300 text-sm">
                  Retry Count: {this.state.retryCount}/3
                </p>
                <p className="text-red-300 text-sm">
                  Last Error: {new Date(this.state.lastError).toLocaleTimeString()}
                </p>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// HOC for wrapping components with error boundary
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Partial<ErrorBoundaryProps>
) {
  return function WithErrorBoundaryComponent(props: P) {
    return (
      <ErrorBoundary {...errorBoundaryProps}>
        <Component {...props} />
      </ErrorBoundary>
    );
  };
}

// Hook for handling errors in functional components
export function useErrorHandler() {
  const [error, setError] = React.useState<Error | null>(null);

  const resetError = React.useCallback(() => {
    setError(null);
  }, []);

  const handleError = React.useCallback((error: Error) => {
    setError(error);
    console.error('useErrorHandler caught error:', error);
  }, []);

  React.useEffect(() => {
    if (error) {
      throw error;
    }
  }, [error]);

  return { handleError, resetError };
}

// Default error fallback component
export function DefaultErrorFallback({ error, resetError }: { error: Error; resetError: () => void }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 my-4">
      <div className="flex items-center mb-2">
        <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
        <h3 className="text-red-800 font-medium">Component Error</h3>
      </div>
      <p className="text-red-700 text-sm mb-3">
        {error.message}
      </p>
      <button
        onClick={resetError}
        className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm"
      >
        Try Again
      </button>
    </div>
  );
}