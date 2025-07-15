'use client';

import React, { useState, useEffect } from 'react';
import { Line, Bar, Pie } from 'react-chartjs-2';

interface FinancialChartsProps {
  chartOptions: any;
  pieChartOptions: any;
}

const FinancialCharts: React.FC<FinancialChartsProps> = ({ chartOptions, pieChartOptions }) => {
  const [cashFlowData, setCashFlowData] = useState<any>(null);
  const [bankingData, setBankingData] = useState<any>(null);
  const [currentPosition, setCurrentPosition] = useState<any>(null);
  const [quickPrediction, setQuickPrediction] = useState<any>(null);
  const [timeframe, setTimeframe] = useState('6M');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFinancialData();
    loadCurrentPosition();
    loadQuickPrediction();
  }, [timeframe]);

  const loadFinancialData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Load cash flow timeline
      const cashFlowResponse = await fetch(
        `http://localhost:8004/api/v1/analytics/cash-flow-timeline?timeframe=${timeframe}`,
        { headers }
      );
      if (cashFlowResponse.ok) {
        const cashFlowResult = await cashFlowResponse.json();
        setCashFlowData(cashFlowResult.chart_data);
      }

      // Load banking trends
      const bankingResponse = await fetch(
        'http://localhost:8004/api/v1/analytics/banking-trends',
        { headers }
      );
      if (bankingResponse.ok) {
        const bankingResult = await bankingResponse.json();
        setBankingData(bankingResult.charts);
      }

    } catch (error) {
      console.error('Erreur lors du chargement des données financières:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCurrentPosition = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      const response = await fetch(
        'http://localhost:8000/api/v1/current-cash-position',
        { headers }
      );
      
      if (response.ok) {
        const data = await response.json();
        setCurrentPosition(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement de la position actuelle:', error);
    }
  };

  const loadQuickPrediction = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      const response = await fetch(
        'http://localhost:8000/api/v1/quick-prediction?days=30',
        { headers }
      );
      
      if (response.ok) {
        const data = await response.json();
        setQuickPrediction(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement de la prédiction rapide:', error);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-FR', { 
      style: 'currency', 
      currency: 'EUR',
      minimumFractionDigits: 0
    }).format(amount);
  };

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

      {/* Financial Metrics Summary */}
      <div className="bg-black border border-white/20 p-8">
        <h3 className="text-xl font-light text-white mb-6">Métriques Financières</h3>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="space-y-3">
            <h4 className="text-lg font-light" style={{color: '#a7292e'}}>Liquidité</h4>
            <div className="space-y-2 text-sm font-light text-white/70">
              <div className="flex justify-between">
                <span>Ratio de liquidité:</span>
                <span className="text-white">2.34</span>
              </div>
              <div className="flex justify-between">
                <span>Fonds de roulement:</span>
                <span className="text-white">€1.2M</span>
              </div>
              <div className="flex justify-between">
                <span>Délai de recouvrement:</span>
                <span className="text-white">42 jours</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-lg font-light" style={{color: '#a7292e'}}>Rentabilité</h4>
            <div className="space-y-2 text-sm font-light text-white/70">
              <div className="flex justify-between">
                <span>Marge brute:</span>
                <span className="text-white">23.4%</span>
              </div>
              <div className="flex justify-between">
                <span>ROE:</span>
                <span className="text-white">15.2%</span>
              </div>
              <div className="flex justify-between">
                <span>ROI:</span>
                <span className="text-white">12.8%</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-lg font-light" style={{color: '#a7292e'}}>Croissance</h4>
            <div className="space-y-2 text-sm font-light text-white/70">
              <div className="flex justify-between">
                <span>Croissance CA:</span>
                <span className="text-white">+8.7%</span>
              </div>
              <div className="flex justify-between">
                <span>Croissance EBITDA:</span>
                <span className="text-white">+12.3%</span>
              </div>
              <div className="flex justify-between">
                <span>Évolution trésorerie:</span>
                <span className="text-white">+5.4%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FinancialCharts;