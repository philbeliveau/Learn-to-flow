/**
 * Scheduler Debug Card Component
 * For testing and debugging scheduler API connections
 */

'use client';

import React, { useState } from 'react';
import useSchedulerStatus from '../hooks/useSchedulerStatus';

const SchedulerDebugCard: React.FC = () => {
  const { status, loading, error, refreshStatus } = useSchedulerStatus();
  const [runningJob, setRunningJob] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

  const runJob = async (jobId: string) => {
    try {
      setRunningJob(jobId);
      const response = await fetch(`${API_URL}/api/scheduler/jobs/${jobId}/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('Job executed successfully:', result);
        // Refresh status after running job
        setTimeout(() => refreshStatus(), 2000);
      } else {
        console.error('Failed to run job:', response.statusText);
      }
    } catch (err) {
      console.error('Error running job:', err);
    } finally {
      setRunningJob(null);
    }
  };

  const runAllJobs = async () => {
    try {
      setRunningJob('all');
      const response = await fetch(`${API_URL}/api/scheduler/run-all`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('All jobs executed:', result);
        // Refresh status after running all jobs
        setTimeout(() => refreshStatus(), 3000);
      } else {
        console.error('Failed to run all jobs:', response.statusText);
      }
    } catch (err) {
      console.error('Error running all jobs:', err);
    } finally {
      setRunningJob(null);
    }
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Scheduler Debug</h3>
        <button
          onClick={refreshStatus}
          className="p-2 rounded-lg bg-blue-600 hover:bg-blue-700 transition-colors"
          disabled={loading}
        >
          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      {loading && <p className="text-yellow-400">Loading scheduler status...</p>}
      {error && <p className="text-red-400">Error: {error}</p>}

      {status && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white/5 rounded-lg p-3">
              <div className="text-sm text-white/70">Status</div>
              <div className={`text-lg font-bold ${status.running ? 'text-green-400' : 'text-red-400'}`}>
                {status.running ? 'Running' : 'Stopped'}
              </div>
            </div>
            <div className="bg-white/5 rounded-lg p-3">
              <div className="text-sm text-white/70">Jobs</div>
              <div className="text-lg font-bold text-white">{status.jobs_count}</div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-white font-medium">Quick Actions</span>
              <button
                onClick={runAllJobs}
                disabled={runningJob !== null}
                className="px-3 py-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded text-sm text-white transition-colors"
              >
                {runningJob === 'all' ? 'Running All...' : 'Run All Jobs'}
              </button>
            </div>

            <div className="max-h-48 overflow-y-auto space-y-1">
              {status.jobs.map((job) => (
                <div key={job.id} className="flex items-center justify-between p-2 bg-white/5 rounded">
                  <div className="flex-1">
                    <div className="text-sm text-white font-medium">{job.name || job.id}</div>
                    <div className="text-xs text-white/60">{job.description}</div>
                  </div>
                  <button
                    onClick={() => runJob(job.id)}
                    disabled={runningJob !== null}
                    className="px-2 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded text-xs text-white transition-colors"
                  >
                    {runningJob === job.id ? 'Running...' : 'Run'}
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="text-xs text-white/60 bg-white/5 rounded p-2">
            <div>API URL: {API_URL}</div>
            <div>Timezone: {status.timezone}</div>
            <div>Enabled: {status.enabled ? 'Yes' : 'No'}</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SchedulerDebugCard;