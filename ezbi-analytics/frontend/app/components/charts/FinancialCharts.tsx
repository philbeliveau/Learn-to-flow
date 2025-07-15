'use client';

import React, { useState, useEffect } from 'react';
import { Line, Bar, Pie } from 'react-chartjs-2';
import { syntheticDataService, formatCurrency, validateRealData } from '../../services/syntheticDataService';

interface FinancialChartsProps {
  chartOptions: any;
  pieChartOptions: any;
}

const FinancialCharts: React.FC<FinancialChartsProps> = ({ chartOptions, pieChartOptions }) => {
  const [cashFlowData, setCashFlowData] = useState<any>(null);
  const [bankingData, setBankingData] = useState<any>(null);
  const [currentPosition, setCurrentPosition] = useState<any>(null);
  const [quickPrediction, setQuickPrediction] = useState<any>(null);
  const [realKPIs, setRealKPIs] = useState<any>(null);
  const [timeframe, setTimeframe] = useState('6M');
  const [loading, setLoading] = useState(true);
  const [dataValidation, setDataValidation] = useState<any>(null);

  useEffect(() => {
    loadAllRealData();
    validateDataSources();
  }, [timeframe]);

  const validateDataSources = async () => {
    try {
      const validation = await syntheticDataService.validateDataSources();
      setDataValidation(validation);
      
      if (!validation.overallHealth) {
        console.warn('Financial data source validation failed:', validation);
      }
    } catch (error) {
      console.error('Failed to validate financial data sources:', error);
    }
  };

  const loadAllRealData = async () => {
    setLoading(true);
    try {
      // Load ALL financial data from real synthetic sources - NO HARDCODED VALUES
      await Promise.all([
        loadRealFinancialData(),
        loadRealCurrentPosition(),
        loadRealQuickPrediction(),
        loadRealKPIs()
      ]);
    } catch (error) {
      console.error('Failed to load all real financial data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRealFinancialData = async () => {
    try {
      // Load cash flow timeline from real synthetic data
      const cashFlowData = await syntheticDataService.getFinancialData(timeframe);
      
      // Validate that we got real data from manufacturing database
      if (!validateRealData(cashFlowData, ['chart_data'])) {
        throw new Error('Invalid financial data from synthetic source');
      }
      
      setCashFlowData(cashFlowData.chart_data);

      // Load banking trends from real synthetic data
      const bankingData = await syntheticDataService.getBankingTrends();
      
      // Validate banking trends data
      if (!validateRealData(bankingData, ['charts'])) {
        throw new Error('Invalid banking trends data from synthetic source');
      }
      
      setBankingData(bankingData.charts);

    } catch (error) {
      console.error('Failed to load real financial data:', error);
      // DO NOT fall back to hardcoded values - fail gracefully
    }
  };

  const loadRealCurrentPosition = async () => {
    try {
      const data = await syntheticDataService.getCurrentCashPosition();
      
      // Validate that we got real data from cash flow API
      if (!validateRealData(data, ['success', 'current_position', 'today_activity'])) {
        throw new Error('Invalid current position data from synthetic source');
      }
      
      setCurrentPosition(data);
    } catch (error) {
      console.error('Failed to load real current position:', error);
      // DO NOT fall back to hardcoded values - fail gracefully
    }
  };

  const loadRealQuickPrediction = async () => {
    try {
      const data = await syntheticDataService.getCashFlowPrediction(30);
      
      // Validate that we got real prediction data
      if (!validateRealData(data, ['success', 'summary'])) {
        throw new Error('Invalid quick prediction data from synthetic source');
      }
      
      setQuickPrediction(data);
    } catch (error) {
      console.error('Failed to load real quick prediction:', error);
      // DO NOT fall back to hardcoded values - fail gracefully
    }
  };

  const loadRealKPIs = async () => {
    try {
      const data = await syntheticDataService.getKPIs();
      
      // Validate that we got real KPI data
      if (!validateRealData(data, [])) { // KPIs object structure can vary
        throw new Error('Invalid KPI data from synthetic source');
      }
      
      setRealKPIs(data);
    } catch (error) {
      console.error('Failed to load real KPIs:', error);
      // DO NOT fall back to hardcoded values - fail gracefully
    }
  };

  // Use formatCurrency from syntheticDataService - NO DUPLICATED CODE

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="animate-pulse">
          <div className="h-8 bg-white/10 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-80 bg-white/10"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Controls */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-light text-white">Analyses Financières</h2>
        <select
          value={timeframe}
          onChange={(e) => setTimeframe(e.target.value)}
          className="bg-black border border-white/30 text-white px-4 py-2 font-light"
          style={{backgroundColor: 'black'}}
        >
          <option value="1M">1 Mois</option>
          <option value="3M">3 Mois</option>
          <option value="6M">6 Mois</option>
          <option value="1Y">1 Année</option>
        </select>
      </div>

      {/* Cash Flow Timeline */}
      {cashFlowData && (
        <div className="bg-black border border-white/20 p-8">
          <h3 className="text-xl font-light text-white mb-6">
            Timeline Cash Flow - {timeframe}
          </h3>
          <div className="h-80">
            <Line data={cashFlowData} options={chartOptions} />
          </div>
          <p className="text-sm font-light text-white/70 mt-4">
            Analyse des flux de trésorerie basée sur plus de 203K enregistrements réels
          </p>
        </div>
      )}

      {/* Banking Analysis Grid */}
      {bankingData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Company Comparison */}
          {bankingData.company_comparison && (
            <div className="bg-black border border-white/20 p-8">
              <h3 className="text-xl font-light text-white mb-6">
                Comparaison Entreprises
              </h3>
              <div className="h-80">
                <Bar 
                  data={{
                    labels: bankingData.company_comparison.labels,
                    datasets: [{
                      label: 'Cash Flow (€B)',
                      data: bankingData.company_comparison.data,
                      backgroundColor: '#a7292e',
                      borderColor: '#a7292e',
                      borderWidth: 1
                    }]
                  }} 
                  options={chartOptions} 
                />
              </div>
              <p className="text-sm font-light text-white/70 mt-4">
                Comparaison des performances financières inter-entreprises
              </p>
            </div>
          )}

          {/* Cash Flow Distribution */}
          {bankingData.cash_flow_distribution && (
            <div className="bg-black border border-white/20 p-8">
              <h3 className="text-xl font-light text-white mb-6">
                Distribution des Flux
              </h3>
              <div className="h-80">
                <Pie 
                  data={{
                    labels: bankingData.cash_flow_distribution.labels,
                    datasets: [{
                      data: bankingData.cash_flow_distribution.data,
                      backgroundColor: ['#a7292e', '#74a6be', '#ffffff', '#000000'],
                      borderColor: '#ffffff',
                      borderWidth: 2
                    }]
                  }} 
                  options={pieChartOptions} 
                />
              </div>
              <p className="text-sm font-light text-white/70 mt-4">
                Répartition des flux de trésorerie par catégorie
              </p>
            </div>
          )}
        </div>
      )}

      {/* Enhanced Cash Flow Analysis */}
      {currentPosition && (
        <div className="bg-black border border-white/20 p-8">
          <h3 className="text-xl font-light text-white mb-6">Position de Trésorerie Actuelle</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="space-y-2">
              <h4 className="text-sm font-light text-white/70">Solde Actuel</h4>
              <p className="text-2xl font-light text-white">
                {formatCurrency(currentPosition.current_position?.cash_balance || 0)}
              </p>
              <p className="text-xs font-light text-white/60">Position immédiate</p>
            </div>
            
            <div className="space-y-2">
              <h4 className="text-sm font-light text-white/70">Créances</h4>
              <p className="text-2xl font-light" style={{color: '#74a6be'}}>
                {formatCurrency(currentPosition.current_position?.outstanding_receivables || 0)}
              </p>
              <p className="text-xs font-light text-white/60">À encaisser</p>
            </div>
            
            <div className="space-y-2">
              <h4 className="text-sm font-light text-white/70">Dettes</h4>
              <p className="text-2xl font-light" style={{color: '#a7292e'}}>
                {formatCurrency(currentPosition.current_position?.outstanding_payables || 0)}
              </p>
              <p className="text-xs font-light text-white/60">À payer</p>
            </div>
            
            <div className="space-y-2">
              <h4 className="text-sm font-light text-white/70">BFR Net</h4>
              <p className="text-2xl font-light text-white">
                {formatCurrency(currentPosition.current_position?.net_working_capital || 0)}
              </p>
              <p className="text-xs font-light text-white/60">Besoin fonds roulement</p>
            </div>
          </div>
          
          {currentPosition.today_activity && (
            <div className="mt-6 pt-6 border-t border-white/20">
              <h4 className="text-lg font-light text-white mb-4">Activité Aujourd'hui</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-light text-white/70">Entrées:</span>
                  <span className="text-lg font-light" style={{color: '#10B981'}}>
                    {formatCurrency(currentPosition.today_activity.inflows)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-light text-white/70">Sorties:</span>
                  <span className="text-lg font-light" style={{color: '#EF4444'}}>
                    {formatCurrency(currentPosition.today_activity.outflows)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-light text-white/70">Net:</span>
                  <span className="text-lg font-light text-white">
                    {formatCurrency(currentPosition.today_activity.net_flow)}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Quick Cash Flow Prediction */}
      {quickPrediction && (
        <div className="bg-black border border-white/20 p-8">
          <h3 className="text-xl font-light text-white mb-6">Prédiction Cash Flow (30j)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <div className="border border-white/30 p-4">
                <h4 className="text-sm font-light text-white/70 mb-2">Résumé Prédiction</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-light text-white/70">Entrées prévues:</span>
                    <span className="text-lg font-light" style={{color: '#10B981'}}>
                      {formatCurrency(quickPrediction.summary?.total_predicted_inflows || 0)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-light text-white/70">Sorties prévues:</span>
                    <span className="text-lg font-light" style={{color: '#EF4444'}}>
                      {formatCurrency(quickPrediction.summary?.total_predicted_outflows || 0)}
                    </span>
                  </div>
                  <div className="flex justify-between pt-2 border-t border-white/20">
                    <span className="text-sm font-light text-white/70">Flux net prévu:</span>
                    <span className="text-xl font-light text-white">
                      {formatCurrency(quickPrediction.summary?.net_cash_flow || 0)}
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="border border-white/30 p-4">
                <h4 className="text-sm font-light text-white/70 mb-2">Solde Fin de Période</h4>
                <p className="text-3xl font-light text-white">
                  {formatCurrency(quickPrediction.summary?.ending_balance || 0)}
                </p>
                <p className="text-xs font-light text-white/60 mt-1">
                  Projection {quickPrediction.period || '30 jours'}
                </p>
              </div>
            </div>
            
            <div className="space-y-4">
              {quickPrediction.risk_factors && quickPrediction.risk_factors.length > 0 && (
                <div className="border border-red-500/30 p-4 bg-red-500/5">
                  <h4 className="text-sm font-light text-red-400 mb-2">Facteurs de Risque</h4>
                  <div className="space-y-2">
                    {quickPrediction.risk_factors.slice(0, 2).map((risk: any, idx: number) => (
                      <div key={idx} className="text-sm font-light text-white/70">
                        • {risk.description || risk}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {quickPrediction.key_insights && quickPrediction.key_insights.length > 0 && (
                <div className="border border-blue-500/30 p-4 bg-blue-500/5">
                  <h4 className="text-sm font-light text-blue-400 mb-2">Insights Clés</h4>
                  <div className="space-y-2">
                    {quickPrediction.key_insights.slice(0, 2).map((insight: any, idx: number) => (
                      <div key={idx} className="text-sm font-light text-white/70">
                        • {insight.description || insight}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Real Financial Metrics Summary - NO HARDCODED VALUES */}
      {realKPIs && (
        <div className="bg-black border border-white/20 p-8">
          <h3 className="text-xl font-light text-white mb-6">Métriques Financières Réelles</h3>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="space-y-3">
              <h4 className="text-lg font-light" style={{color: '#a7292e'}}>Liquidité (Données Synthétiques)</h4>
              <div className="space-y-2 text-sm font-light text-white/70">
                <div className="flex justify-between">
                  <span>Ratio de liquidité:</span>
                  <span className="text-white">
                    {realKPIs.liquidity_ratio ? realKPIs.liquidity_ratio.toFixed(2) : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Fonds de roulement:</span>
                  <span className="text-white">
                    {realKPIs.working_capital ? formatCurrency(realKPIs.working_capital) : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Délai de recouvrement:</span>
                  <span className="text-white">
                    {realKPIs.collection_period ? `${realKPIs.collection_period} jours` : 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="text-lg font-light" style={{color: '#a7292e'}}>Rentabilité (Données Synthétiques)</h4>
              <div className="space-y-2 text-sm font-light text-white/70">
                <div className="flex justify-between">
                  <span>Marge brute:</span>
                  <span className="text-white">
                    {realKPIs.gross_margin ? `${(realKPIs.gross_margin * 100).toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>ROE:</span>
                  <span className="text-white">
                    {realKPIs.roe ? `${(realKPIs.roe * 100).toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>ROI:</span>
                  <span className="text-white">
                    {realKPIs.roi ? `${(realKPIs.roi * 100).toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="text-lg font-light" style={{color: '#a7292e'}}>Croissance (Données Synthétiques)</h4>
              <div className="space-y-2 text-sm font-light text-white/70">
                <div className="flex justify-between">
                  <span>Croissance CA:</span>
                  <span className="text-white">
                    {realKPIs.revenue_growth ? `${(realKPIs.revenue_growth * 100).toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Croissance EBITDA:</span>
                  <span className="text-white">
                    {realKPIs.ebitda_growth ? `${(realKPIs.ebitda_growth * 100).toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Évolution trésorerie:</span>
                  <span className="text-white">
                    {realKPIs.cash_flow_growth ? `${(realKPIs.cash_flow_growth * 100).toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Data Source Validation */}
          <div className="mt-6 pt-4 border-t border-white/20">
            <div className="flex justify-between items-center">
              <span className="text-sm font-light text-white/70">Source des données:</span>
              <span className={`text-sm font-light ${
                dataValidation?.manufacturingAPI ? 'text-green-400' : 'text-red-400'
              }`}>
                {dataValidation?.manufacturingAPI ? 'Manufacturing API - Données synthétiques' : 'Données non disponibles'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* No Real KPIs State */}
      {!realKPIs && !loading && (
        <div className="bg-black border border-white/20 p-8">
          <h3 className="text-xl font-light text-white mb-6">Métriques Financières</h3>
          <div className="text-center py-8">
            <p className="text-white/70 font-light">
              Chargement des KPIs depuis les données synthétiques...
            </p>
            <p className="text-white/50 font-light text-sm mt-2">
              Toutes les métriques proviennent de la base de données manufacturière
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default FinancialCharts;