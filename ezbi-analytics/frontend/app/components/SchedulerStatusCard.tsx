/**
 * Scheduler Status Card Component
 * Shows detailed scheduler status including jobs, next runs, and system health
 */

'use client';

import React, { useState } from 'react';
import useSchedulerStatus from '../hooks/useSchedulerStatus';

const SchedulerStatusCard: React.FC = () => {
  const { status, loading, error, refreshStatus } = useSchedulerStatus();
  const [showDetails, setShowDetails] = useState(false);

  const getStatusColor = () => {
    if (loading) return 'text-yellow-400';
    if (error) return 'text-red-400';
    if (status?.running) return 'text-green-400';
    return 'text-gray-400';
  };

  const getStatusText = () => {
    if (loading) return 'Checking...';
    if (error) return 'Error';
    if (status?.running) return 'Active';
    return 'Offline';
  };

  const formatNextRun = (nextRun: string | undefined) => {
    if (!nextRun) return 'N/A';
    try {
      const date = new Date(nextRun);
      return date.toLocaleString('fr-FR', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'N/A';
    }
  };

  const getJobsByTimeOrder = () => {
    if (!status?.jobs) return [];
    return [...status.jobs].sort((a, b) => {
      if (!a.next_run) return 1;
      if (!b.next_run) return -1;
      return new Date(a.next_run).getTime() - new Date(b.next_run).getTime();
    });
  };

  return (
    <div className="bg-white/5 border border-white/20 rounded-lg p-6 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getStatusColor().replace('text-', 'bg-')}`}></div>
            <h3 className="text-lg font-semibold text-white">Planificateur de Données</h3>
          </div>
          <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor()}`}>
            {getStatusText()}
          </span>
        </div>
        <button
          onClick={refreshStatus}
          className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
          title="Actualiser le statut"
        >
          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white/60 mx-auto"></div>
          <p className="text-white/60 mt-2">Vérification du statut...</p>
        </div>
      )}

      {error && (
        <div className="text-center py-8">
          <div className="text-red-400 text-sm mb-2">
            <svg className="w-6 h-6 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            Erreur de connexion au planificateur
          </div>
          <p className="text-white/60 text-xs">{error}</p>
        </div>
      )}

      {status && (
        <div className="space-y-4">
          {/* Status Summary */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white/5 rounded-lg p-4">
              <div className="text-2xl font-bold text-white">{status.jobs_count}</div>
              <div className="text-white/60 text-sm">Tâches Programmées</div>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <div className="text-2xl font-bold text-white">{status.timezone}</div>
              <div className="text-white/60 text-sm">Fuseau Horaire</div>
            </div>
          </div>

          {/* Jobs Details Toggle */}
          <div className="flex items-center justify-between">
            <h4 className="text-white font-medium">Tâches Quotidiennes</h4>
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-white/60 hover:text-white transition-colors text-sm"
            >
              {showDetails ? 'Masquer' : 'Afficher'} les détails
            </button>
          </div>

          {showDetails && (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {getJobsByTimeOrder().map((job, index) => (
                <div key={job.id} className="bg-white/5 rounded-lg p-3 border border-white/10">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${job.enabled ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                      <span className="text-white text-sm font-medium">{job.name || job.id}</span>
                    </div>
                    <span className="text-white/60 text-xs">
                      {formatNextRun(job.next_run)}
                    </span>
                  </div>
                  <div className="text-white/60 text-xs">
                    {job.description}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Next Job Info */}
          {status.jobs.length > 0 && (
            <div className="bg-blue-500/20 border border-blue-500/40 rounded-lg p-3">
              <div className="flex items-center gap-2 text-blue-400 text-sm">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Prochaine exécution: {formatNextRun(getJobsByTimeOrder()[0]?.next_run)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SchedulerStatusCard;