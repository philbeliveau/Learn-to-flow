'use client';

import React, { useState, useEffect } from 'react';
import { syntheticDataService, formatCurrency, validateRealData } from '../../services/syntheticDataService';

interface OverviewChartsProps {
  kpis: any;
}

const OverviewCharts: React.FC<OverviewChartsProps> = ({ kpis }) => {
  const [realSystemData, setRealSystemData] = useState<any>(null);
  const [dataValidation, setDataValidation] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRealSystemData();
    validateDataSources();
  }, []);

  const validateDataSources = async () => {
    try {
      const validation = await syntheticDataService.validateDataSources();
      setDataValidation(validation);
      
      if (!validation.overallHealth) {
        console.warn('Overview data source validation failed:', validation);
      }
    } catch (error) {
      console.error('Failed to validate overview data sources:', error);
    }
  };

  const loadRealSystemData = async () => {
    setLoading(true);
    try {
      // Load real manufacturing system data
      const manufacturingData = await syntheticDataService.getManufacturingData();
      
      // Validate that we got real manufacturing data
      if (!validateRealData(manufacturingData, [])) {
        throw new Error('Invalid manufacturing data from synthetic source');
      }
      
      setRealSystemData(manufacturingData);
    } catch (error) {
      console.error('Failed to load real system data:', error);
      // DO NOT fall back to hardcoded values
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* KPI Summary */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-black border border-white/20 p-6 hover:scale-105 transition-transform duration-300">
          <div className="mb-4">
            <svg className="w-8 h-8" style={{color: '#74a6be'}} fill="currentColor" viewBox="0 0 24 24">
              <path d="M13 2.05v2.02c4.39.54 7.5 4.53 7.5 9.43 0 5.52-4.48 10-10 10S0 19.02 0 13.5c0-4.9 3.11-8.89 7.5-9.43V2.05C3.47 2.54 0 7.36 0 13.5 0 20.68 5.82 26.5 13 26.5s13-5.82 13-13c0-6.14-3.47-10.96-7.5-11.45z"/>
            </svg>
          </div>
          <h3 className="text-sm font-light text-white/70 mb-2">Efficacité Production (Données Synthétiques)</h3>
          <p className="text-3xl font-light text-white mb-1">
            {kpis?.production?.efficiency ? (kpis.production.efficiency * 100).toFixed(1) + '%' : 'N/A'}
          </p>
          <p className="text-xs font-light" style={{color: '#74a6be'}}>
            {kpis?.production?.efficiency_growth ? `${(kpis.production.efficiency_growth * 100).toFixed(1)}% ce mois` : 'Calcul...'}
          </p>
        </div>

        <div className="bg-black border border-white/20 p-6 hover:scale-105 transition-transform duration-300">
          <div className="mb-4">
            <svg className="w-8 h-8" style={{color: '#a7292e'}} fill="currentColor" viewBox="0 0 24 24">
              <path d="M7 15h2c0 1.08 1.37 2 3 2s3-.92 3-2c0-1.1-1.04-1.5-3.24-2.03C9.64 12.44 7 11.78 7 9c0-1.79 1.47-3.31 3.5-3.82V3h3v2.18C15.53 5.69 17 7.21 17 9h-2c0-1.08-1.37-2-3-2s-3 .92-3 2c0 1.1 1.04 1.5 3.24 2.03C14.36 11.56 17 12.22 17 15c0 1.79-1.47 3.31-3.5 3.82V21h-3v-2.18C8.47 18.31 7 16.79 7 15z"/>
            </svg>
          </div>
          <h3 className="text-sm font-light text-white/70 mb-2">Position Cash (Données Synthétiques)</h3>
          <p className="text-3xl font-light text-white mb-1">
            {kpis?.financial?.cash_position ? formatCurrency(kpis.financial.cash_position) : 'N/A'}
          </p>
          <p className="text-xs font-light" style={{color: '#a7292e'}}>
            {kpis?.financial?.cash_change ? formatCurrency(kpis.financial.cash_change) + ' ce mois' : 'Calcul...'}
          </p>
        </div>

        <div className="bg-black border border-white/20 p-6 hover:scale-105 transition-transform duration-300">
          <div className="mb-4">
            <svg className="w-8 h-8" style={{color: '#74a6be'}} fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
          </div>
          <h3 className="text-sm font-light text-white/70 mb-2">Utilisation Capacité (Données Synthétiques)</h3>
          <p className="text-3xl font-light text-white mb-1">
            {kpis?.production?.capacity_utilization ? (kpis.production.capacity_utilization * 100).toFixed(1) + '%' : 'N/A'}
          </p>
          <p className="text-xs font-light" style={{color: '#74a6be'}}>
            {kpis?.production?.capacity_growth ? `${(kpis.production.capacity_growth * 100).toFixed(1)}% ce mois` : 'Calcul...'}
          </p>
        </div>

        <div className="bg-black border border-white/20 p-6 hover:scale-105 transition-transform duration-300">
          <div className="mb-4">
            <svg className="w-8 h-8" style={{color: '#74a6be'}} fill="currentColor" viewBox="0 0 24 24">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
            </svg>
          </div>
          <h3 className="text-sm font-light text-white/70 mb-2">Taux de Défaut (Données Synthétiques)</h3>
          <p className="text-3xl font-light text-white mb-1">
            {kpis?.production?.defect_rate ? (kpis.production.defect_rate * 100).toFixed(1) + '%' : 'N/A'}
          </p>
          <p className="text-xs font-light" style={{color: '#74a6be'}}>
            {kpis?.production?.defect_improvement ? `${(kpis.production.defect_improvement * 100).toFixed(1)}% ce mois` : 'Calcul...'}
          </p>
        </div>
      </div>

      {/* Real System Status - NO HARDCODED VALUES */}
      <div className="bg-black border border-white/20 p-8">
        <h2 className="text-2xl font-light text-white mb-6">État du Système - Données Synthétiques Réelles</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="space-y-3">
            <h3 className="text-lg font-light text-white">Sources de Données</h3>
            <div className="space-y-2 text-sm font-light text-white/70">
              <div className="flex justify-between">
                <span>Cash Flow API:</span>
                <span className={`${dataValidation?.cashFlowAPI ? 'text-green-400' : 'text-red-400'}`}>
                  {dataValidation?.cashFlowAPI ? 'En ligne' : 'Hors ligne'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Manufacturing API:</span>
                <span className={`${dataValidation?.manufacturingAPI ? 'text-green-400' : 'text-red-400'}`}>
                  {dataValidation?.manufacturingAPI ? 'En ligne' : 'Hors ligne'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>PostgreSQL:</span>
                <span className={`${dataValidation?.postgresqlData ? 'text-green-400' : 'text-red-400'}`}>
                  {dataValidation?.postgresqlData ? 'Connecté' : 'Déconnecté'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Excel Business:</span>
                <span className={`${dataValidation?.excelData ? 'text-green-400' : 'text-red-400'}`}>
                  {dataValidation?.excelData ? 'Disponible' : 'Indisponible'}
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-lg font-light text-white">Moteur d'Analyse Réel</h3>
            <div className="space-y-2 text-sm font-light text-white/70">
              <div>ML Ensemble (Linear + Random Forest)</div>
              <div>PostgreSQL + Excel intégration</div>
              <div>Validation données temps réel</div>
              <div>Prédictions multi-scénarios</div>
              <div>Analyse automatique des risques</div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-lg font-light text-white">Performance Système</h3>
            <div className="space-y-2 text-sm font-light">
              <div className="flex justify-between">
                <span className="text-white/70">État global:</span>
                <span className={`${dataValidation?.overallHealth ? 'text-green-400' : 'text-red-400'}`}>
                  {dataValidation?.overallHealth ? 'Opérationnel' : 'Problème'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Sources actives:</span>
                <span style={{color: '#74a6be'}}>
                  {dataValidation ? 
                    [dataValidation.cashFlowAPI, dataValidation.manufacturingAPI, dataValidation.postgresqlData, dataValidation.excelData]
                      .filter(Boolean).length + '/4' : '0/4'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Données temps réel:</span>
                <span style={{color: '#a7292e'}}>
                  {realSystemData ? 'Disponibles' : 'Chargement...'}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        {/* Real Data Source Details */}
        {realSystemData && (
          <div className="mt-6 pt-6 border-t border-white/20">
            <h4 className="text-lg font-light text-white mb-4">Détails Sources Synthétiques</h4>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-2 text-sm font-light text-white/70">
                <div>• Base manufacturière: {realSystemData.total_records || 'N/A'} enregistrements</div>
                <div>• Transactions cash: {realSystemData.cash_transactions || 'N/A'} opérations</div>
                <div>• Prédictions actives: {realSystemData.active_predictions || 'N/A'}</div>
              </div>
              <div className="space-y-2 text-sm font-light text-white/70">
                <div>• Fichiers Excel: {realSystemData.excel_files || 'N/A'} documents</div>
                <div>• Dernière synchro: {realSystemData.last_sync || 'N/A'}</div>
                <div>• Qualité données: {realSystemData.data_quality || 'N/A'}%</div>
              </div>
            </div>
          </div>
        )}
        
        {/* Loading state for system data */}
        {loading && !realSystemData && (
          <div className="mt-6 pt-6 border-t border-white/20 text-center">
            <p className="text-white/70 font-light">Chargement des données système synthétiques...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default OverviewCharts;