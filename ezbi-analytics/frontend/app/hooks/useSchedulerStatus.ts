/**
 * Custom hook for monitoring scheduler status
 * Fetches and manages scheduler API status for system monitoring
 */

import { useState, useEffect } from 'react';

export interface SchedulerJob {
  id: string;
  name: string;
  description: string;
  schedule: string;
  enabled: boolean;
  next_run?: string;
}

export interface SchedulerStatus {
  enabled: boolean;
  running: boolean;
  jobs_count: number;
  timezone: string;
  jobs: SchedulerJob[];
}

export interface SchedulerStatusHook {
  status: SchedulerStatus | null;
  loading: boolean;
  error: string | null;
  refreshStatus: () => void;
}

const useSchedulerStatus = (): SchedulerStatusHook => {
  const [status, setStatus] = useState<SchedulerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get API URL from environment or fallback to localhost
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

  const fetchSchedulerStatus = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/api/scheduler/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setStatus(data);
    } catch (err) {
      console.error('Error fetching scheduler status:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch scheduler status');
      setStatus(null);
    } finally {
      setLoading(false);
    }
  };

  const refreshStatus = () => {
    fetchSchedulerStatus();
  };

  useEffect(() => {
    fetchSchedulerStatus();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchSchedulerStatus, 30000);
    
    return () => clearInterval(interval);
  }, []);

  return {
    status,
    loading,
    error,
    refreshStatus,
  };
};

export default useSchedulerStatus;