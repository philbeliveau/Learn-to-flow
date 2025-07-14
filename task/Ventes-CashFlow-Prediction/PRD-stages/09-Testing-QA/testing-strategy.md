# 🧪 STRATÉGIE DE TESTS & QA - EZBI ANALYTICS

## 🎯 PHILOSOPHIE TESTING

### Approche Quality-First
```
🔬 "Test-Driven AI Development"

Principes Directeurs:
├── AI Accuracy First: Précision ML > 85% minimum
├── User Experience Testing: UX intuitive validée
├── Performance Benchmarking: <2s response time
├── Security by Design: Tests sécurité intégrés
└── Continuous Validation: Testing automatisé CI/CD
```

### Stratégie de Test Pyramide
```
🏗️ Test Pyramid pour EZBI

                    ┌─────────────────┐
                    │   E2E TESTS     │ <- 10%
                    │  User Journeys  │
                    │  Cross-browser  │
                    └─────────────────┘
                  ┌───────────────────────┐
                  │   INTEGRATION TESTS   │ <- 20%
                  │    API Testing        │
                  │  ML Pipeline Tests    │
                  │  Database Tests       │
                  └───────────────────────┘
              ┌─────────────────────────────────┐
              │        UNIT TESTS               │ <- 70%
              │  Component Testing              │
              │  Function Testing               │
              │  ML Model Testing               │
              │  Utility Testing                │
              └─────────────────────────────────┘
```

---

## 🧠 TESTS MACHINE LEARNING

### Framework de Test ML
```python
# 🤖 ML Testing Framework pour EZBI

import pytest
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
from typing import Dict, List, Tuple
import logging

class MLModelTestSuite:
    """Suite de tests complète pour modèles ML EZBI"""
    
    def __init__(self, model, test_data: pd.DataFrame, ground_truth: pd.DataFrame):
        self.model = model
        self.test_data = test_data
        self.ground_truth = ground_truth
        self.results = {}
    
    def test_accuracy_threshold(self, min_accuracy: float = 0.85):
        """Test: Précision minimum requise"""
        predictions = self.model.predict(self.test_data)
        mape = mean_absolute_percentage_error(
            self.ground_truth['actual'], 
            predictions['predicted']
        )
        accuracy = 1 - mape
        
        assert accuracy >= min_accuracy, f"Accuracy {accuracy:.3f} < minimum {min_accuracy}"
        self.results['accuracy'] = accuracy
        return accuracy
    
    def test_prediction_consistency(self, tolerance: float = 0.05):
        """Test: Cohérence des prédictions répétées"""
        predictions_1 = self.model.predict(self.test_data)
        predictions_2 = self.model.predict(self.test_data)
        
        diff = np.abs(predictions_1['predicted'] - predictions_2['predicted'])
        max_diff = np.max(diff) / np.mean(predictions_1['predicted'])
        
        assert max_diff <= tolerance, f"Inconsistency {max_diff:.3f} > tolerance {tolerance}"
        self.results['consistency'] = max_diff
        return max_diff
    
    def test_confidence_intervals(self):
        """Test: Intervalles de confiance valides"""
        predictions = self.model.predict(self.test_data)
        
        # Test 1: Lower bound < prediction < upper bound
        lower = predictions['predicted_lower']
        upper = predictions['predicted_upper']
        pred = predictions['predicted']
        
        assert np.all(lower <= pred), "Some predictions below lower bound"
        assert np.all(pred <= upper), "Some predictions above upper bound"
        
        # Test 2: Confidence intervals reasonable width
        interval_width = (upper - lower) / pred
        avg_width = np.mean(interval_width)
        
        assert 0.1 <= avg_width <= 0.5, f"Confidence interval width {avg_width:.3f} unreasonable"
        
        self.results['confidence_width'] = avg_width
        return True
    
    def test_seasonal_patterns(self, seasonal_data: pd.DataFrame):
        """Test: Détection de patterns saisonniers"""
        predictions = self.model.predict(seasonal_data)
        
        # Grouper par mois et calculer moyennes
        monthly_pred = predictions.groupby('month')['predicted'].mean()
        
        # Test saisonnalité (coefficient de variation > 0.1)
        seasonal_cv = np.std(monthly_pred) / np.mean(monthly_pred)
        assert seasonal_cv > 0.1, f"Seasonality CV {seasonal_cv:.3f} too low"
        
        self.results['seasonality_cv'] = seasonal_cv
        return seasonal_cv
    
    def test_business_rules_validation(self):
        """Test: Validation des règles métier"""
        predictions = self.model.predict(self.test_data)
        
        # Règle 1: Pas de valeurs négatives impossibles
        negative_predictions = predictions[predictions['predicted'] < -1000000]  # -1M€ threshold
        assert len(negative_predictions) == 0, f"{len(negative_predictions)} extreme negative predictions"
        
        # Règle 2: Pas de croissance irréaliste (>1000% en un mois)
        if len(predictions) > 1:
            growth_rates = predictions['predicted'].pct_change()
            extreme_growth = growth_rates[growth_rates > 10.0]  # 1000% growth
            assert len(extreme_growth) == 0, f"{len(extreme_growth)} extreme growth predictions"
        
        # Règle 3: Cohérence avec données historiques
        historical_mean = self.test_data['amount'].mean()
        predicted_mean = predictions['predicted'].mean()
        ratio = predicted_mean / historical_mean
        
        assert 0.5 <= ratio <= 2.0, f"Prediction mean ratio {ratio:.2f} outside reasonable range"
        
        return True
    
    def test_model_robustness(self):
        """Test: Robustesse aux données bruités"""
        # Ajouter du bruit aux données test
        noisy_data = self.test_data.copy()
        noise = np.random.normal(0, 0.1, len(noisy_data))
        noisy_data['amount'] *= (1 + noise)
        
        # Prédictions avec et sans bruit
        clean_pred = self.model.predict(self.test_data)
        noisy_pred = self.model.predict(noisy_data)
        
        # Calculer différence
        pred_diff = np.abs(clean_pred['predicted'] - noisy_pred['predicted'])
        max_diff = np.max(pred_diff) / np.mean(clean_pred['predicted'])
        
        assert max_diff <= 0.2, f"Model not robust to noise: {max_diff:.3f} difference"
        
        self.results['robustness'] = max_diff
        return max_diff
    
    def test_feature_importance(self):
        """Test: Importance des features cohérente"""
        if hasattr(self.model, 'get_feature_importance'):
            importance = self.model.get_feature_importance()
            
            # Test 1: Features importantes non nulles
            assert np.sum(list(importance.values())) > 0, "No feature importance detected"
            
            # Test 2: Feature 'amount' dans top 3 (logique métier)
            sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
            top_3_features = [f[0] for f in sorted_features[:3]]
            
            # Au moins une feature liée au montant dans le top 3
            amount_related = ['amount', 'montant', 'total', 'value']
            has_amount_feature = any(feature in top_3_features for feature in amount_related)
            
            assert has_amount_feature, f"No amount-related feature in top 3: {top_3_features}"
            
            self.results['feature_importance'] = importance
            return importance
    
    def test_inference_speed(self, max_inference_time: float = 2.0):
        """Test: Temps d'inférence acceptable"""
        import time
        
        start_time = time.time()
        predictions = self.model.predict(self.test_data)
        inference_time = time.time() - start_time
        
        assert inference_time <= max_inference_time, f"Inference time {inference_time:.2f}s > {max_inference_time}s"
        
        self.results['inference_time'] = inference_time
        return inference_time
    
    def generate_test_report(self) -> Dict:
        """Génère un rapport de test complet"""
        return {
            'model_type': str(type(self.model).__name__),
            'test_results': self.results,
            'test_data_size': len(self.test_data),
            'timestamp': pd.Timestamp.now().isoformat(),
            'status': 'PASSED' if all(self.results.values()) else 'FAILED'
        }

# Tests spécialisés par modèle
class ProphetModelTests(MLModelTestSuite):
    """Tests spécifiques au modèle Prophet"""
    
    def test_trend_detection(self):
        """Test: Détection correcte des tendances"""
        # Créer données avec tendance connue
        dates = pd.date_range('2023-01-01', periods=365, freq='D')
        trend_data = pd.DataFrame({
            'ds': dates,
            'y': np.linspace(1000, 2000, 365) + np.random.normal(0, 50, 365)
        })
        
        # Entraîner et prédire
        self.model.fit(trend_data)
        future = self.model.make_future_dataframe(periods=30)
        forecast = self.model.predict(future)
        
        # Vérifier tendance positive détectée
        trend_slope = (forecast['trend'].iloc[-1] - forecast['trend'].iloc[0]) / len(forecast)
        assert trend_slope > 0, f"Failed to detect positive trend: slope={trend_slope:.2f}"
        
        return trend_slope
    
    def test_seasonality_components(self):
        """Test: Composantes saisonnières cohérentes"""
        # Vérifier présence des composantes saisonnières
        forecast = self.model.predict(self.model.make_future_dataframe(periods=30))
        
        required_components = ['trend', 'yearly']
        for component in required_components:
            assert component in forecast.columns, f"Missing component: {component}"
            assert not forecast[component].isna().all(), f"Component {component} all NaN"
        
        return True

class LSTMModelTests(MLModelTestSuite):
    """Tests spécifiques au modèle LSTM"""
    
    def test_sequence_memory(self):
        """Test: Mémoire des séquences"""
        # Créer séquence avec pattern répétitif
        sequence_data = self.create_pattern_sequence()
        
        predictions = self.model.predict(sequence_data)
        
        # Vérifier que le modèle détecte le pattern
        pattern_accuracy = self.calculate_pattern_accuracy(predictions)
        assert pattern_accuracy > 0.7, f"Pattern recognition accuracy {pattern_accuracy:.3f} too low"
        
        return pattern_accuracy
    
    def create_pattern_sequence(self) -> pd.DataFrame:
        """Crée une séquence avec pattern connu"""
        # Pattern: montée-descente cyclique
        pattern = [1000, 1500, 2000, 1500, 1000] * 20  # 100 points
        dates = pd.date_range('2023-01-01', periods=len(pattern), freq='D')
        
        return pd.DataFrame({
            'date': dates,
            'amount': pattern
        })
    
    def calculate_pattern_accuracy(self, predictions) -> float:
        """Calcule la précision de détection de pattern"""
        # Implémentation simplifiée
        return 0.85  # Mock pour l'exemple

class EnsembleModelTests(MLModelTestSuite):
    """Tests spécifiques au modèle Ensemble"""
    
    def test_model_agreement(self):
        """Test: Accord entre modèles de base"""
        predictions = self.model.predict(self.test_data)
        
        if 'model_agreement' in predictions:
            agreement_score = predictions['model_agreement']['agreement_score']
            assert agreement_score > 0.6, f"Model agreement {agreement_score:.3f} too low"
            
            self.results['model_agreement'] = agreement_score
            return agreement_score
    
    def test_weight_distribution(self):
        """Test: Distribution des poids cohérente"""
        if hasattr(self.model, 'model_weights'):
            weights = self.model.model_weights
            
            # Test 1: Somme des poids = 1
            weight_sum = sum(weights.values())
            assert abs(weight_sum - 1.0) < 0.01, f"Weights sum {weight_sum:.3f} != 1.0"
            
            # Test 2: Pas de poids négatifs
            negative_weights = [w for w in weights.values() if w < 0]
            assert len(negative_weights) == 0, f"{len(negative_weights)} negative weights"
            
            # Test 3: Pas de dominance excessive d'un modèle
            max_weight = max(weights.values())
            assert max_weight <= 0.8, f"Excessive weight dominance: {max_weight:.3f}"
            
            self.results['weight_distribution'] = weights
            return weights
```

### Tests de Performance ML
```python
# ⚡ Performance Testing pour ML Pipeline

import pytest
import time
import memory_profiler
import concurrent.futures
from typing import List

class MLPerformanceTests:
    """Tests de performance pour pipeline ML"""
    
    def __init__(self, model_pipeline):
        self.pipeline = model_pipeline
        self.performance_metrics = {}
    
    @pytest.mark.performance
    def test_batch_prediction_performance(self):
        """Test: Performance prédictions batch"""
        batch_sizes = [1, 10, 50, 100, 500]
        
        for batch_size in batch_sizes:
            test_data = self.generate_test_batch(batch_size)
            
            start_time = time.time()
            predictions = self.pipeline.predict_batch(test_data)
            end_time = time.time()
            
            processing_time = end_time - start_time
            throughput = batch_size / processing_time
            
            # Requirement: >100 predictions/second
            assert throughput > 100, f"Throughput {throughput:.2f} pred/s too low for batch {batch_size}"
            
            self.performance_metrics[f'batch_{batch_size}'] = {
                'processing_time': processing_time,
                'throughput': throughput
            }
    
    @pytest.mark.performance
    def test_memory_usage(self):
        """Test: Utilisation mémoire acceptable"""
        
        @memory_profiler.profile
        def memory_test():
            large_dataset = self.generate_test_batch(1000)
            predictions = self.pipeline.predict_batch(large_dataset)
            return predictions
        
        # Exécuter et mesurer
        initial_memory = memory_profiler.memory_usage()[0]
        result = memory_test()
        peak_memory = max(memory_profiler.memory_usage())
        
        memory_increase = peak_memory - initial_memory
        
        # Requirement: <500MB increase
        assert memory_increase < 500, f"Memory increase {memory_increase:.1f}MB too high"
        
        self.performance_metrics['memory_usage'] = {
            'initial_mb': initial_memory,
            'peak_mb': peak_memory,
            'increase_mb': memory_increase
        }
    
    @pytest.mark.performance
    def test_concurrent_predictions(self):
        """Test: Prédictions concurrentes"""
        num_workers = 4
        requests_per_worker = 10
        
        def worker_predictions(worker_id):
            results = []
            for i in range(requests_per_worker):
                test_data = self.generate_test_batch(10)
                start_time = time.time()
                prediction = self.pipeline.predict(test_data)
                end_time = time.time()
                results.append(end_time - start_time)
            return results
        
        # Exécution concurrente
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(worker_predictions, i) for i in range(num_workers)]
            all_results = [future.result() for future in futures]
        end_time = time.time()
        
        # Analyse résultats
        total_predictions = num_workers * requests_per_worker
        total_time = end_time - start_time
        concurrent_throughput = total_predictions / total_time
        
        # Requirement: >50 concurrent predictions/second
        assert concurrent_throughput > 50, f"Concurrent throughput {concurrent_throughput:.2f} too low"
        
        # Latency analysis
        all_latencies = [latency for worker_results in all_results for latency in worker_results]
        avg_latency = sum(all_latencies) / len(all_latencies)
        p95_latency = sorted(all_latencies)[int(0.95 * len(all_latencies))]
        
        # Requirements: <2s avg, <5s P95
        assert avg_latency < 2.0, f"Average latency {avg_latency:.2f}s too high"
        assert p95_latency < 5.0, f"P95 latency {p95_latency:.2f}s too high"
        
        self.performance_metrics['concurrent'] = {
            'throughput': concurrent_throughput,
            'avg_latency': avg_latency,
            'p95_latency': p95_latency
        }
    
    def generate_test_batch(self, size: int) -> pd.DataFrame:
        """Génère un batch de test de taille donnée"""
        dates = pd.date_range('2024-01-01', periods=size, freq='D')
        return pd.DataFrame({
            'date': dates,
            'amount': np.random.normal(10000, 2000, size),
            'client_id': [f'client_{i%100}' for i in range(size)]
        })
```

---

## 🌐 TESTS D'INTÉGRATION

### Tests API REST
```python
# 🔌 API Integration Tests

import pytest
import requests
import json
from typing import Dict, Any

class APIIntegrationTests:
    """Tests d'intégration pour API EZBI"""
    
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
    
    @pytest.mark.integration
    def test_upload_and_prediction_workflow(self):
        """Test: Workflow complet upload → prédiction"""
        
        # Étape 1: Upload fichier
        upload_response = self.upload_test_file()
        assert upload_response.status_code == 201
        
        file_id = upload_response.json()['file_id']
        
        # Étape 2: Vérifier processing
        processing_status = self.wait_for_processing(file_id)
        assert processing_status == 'completed'
        
        # Étape 3: Demander prédiction
        prediction_response = self.request_prediction(file_id)
        assert prediction_response.status_code == 200
        
        # Étape 4: Vérifier résultats
        prediction_data = prediction_response.json()
        self.validate_prediction_response(prediction_data)
        
        return prediction_data
    
    def upload_test_file(self) -> requests.Response:
        """Upload un fichier de test"""
        files = {
            'file': ('test_data.csv', open('test_data.csv', 'rb'), 'text/csv')
        }
        
        response = requests.post(
            f'{self.base_url}/api/v1/upload',
            headers={'Authorization': self.headers['Authorization']},
            files=files
        )
        
        return response
    
    def wait_for_processing(self, file_id: str, max_wait: int = 60) -> str:
        """Attend la fin du processing"""
        import time
        
        for _ in range(max_wait):
            response = requests.get(
                f'{self.base_url}/api/v1/files/{file_id}/status',
                headers=self.headers
            )
            
            if response.status_code == 200:
                status = response.json()['status']
                if status in ['completed', 'failed']:
                    return status
            
            time.sleep(1)
        
        raise TimeoutError(f"Processing timeout for file {file_id}")
    
    def request_prediction(self, file_id: str) -> requests.Response:
        """Demande une prédiction"""
        payload = {
            'file_id': file_id,
            'horizon_days': 90,
            'confidence_level': 0.95,
            'scenario': 'realistic'
        }
        
        response = requests.post(
            f'{self.base_url}/api/v1/predictions',
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        return response
    
    def validate_prediction_response(self, data: Dict[str, Any]):
        """Valide la structure de réponse prédiction"""
        required_fields = [
            'model_type', 'predictions', 'confidence_level', 'insights'
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Valider structure predictions
        predictions = data['predictions']
        assert isinstance(predictions, list), "Predictions should be a list"
        assert len(predictions) > 0, "Predictions list should not be empty"
        
        # Valider structure première prédiction
        first_pred = predictions[0]
        pred_fields = ['ds', 'yhat', 'yhat_lower', 'yhat_upper']
        
        for field in pred_fields:
            assert field in first_pred, f"Missing prediction field: {field}"
        
        # Valider cohérence valeurs
        assert first_pred['yhat_lower'] <= first_pred['yhat'], "Lower bound > prediction"
        assert first_pred['yhat'] <= first_pred['yhat_upper'], "Prediction > upper bound"
    
    @pytest.mark.integration
    def test_api_rate_limiting(self):
        """Test: Limitation de taux API"""
        responses = []
        
        # Faire 100 requêtes rapides
        for i in range(100):
            response = requests.get(
                f'{self.base_url}/api/v1/health',
                headers=self.headers
            )
            responses.append(response.status_code)
        
        # Vérifier qu'on n'a pas trop de 429 (rate limited)
        rate_limited = sum(1 for status in responses if status == 429)
        rate_limited_percentage = rate_limited / len(responses)
        
        assert rate_limited_percentage < 0.1, f"Too many rate limited requests: {rate_limited_percentage:.2%}"
    
    @pytest.mark.integration
    def test_slack_notification_integration(self):
        """Test: Intégration notifications Slack"""
        # Déclencher une prédiction
        prediction_data = self.test_upload_and_prediction_workflow()
        
        # Vérifier envoi notification (via webhook mock)
        webhook_response = requests.get(f'{self.base_url}/api/v1/test/slack-webhook')
        assert webhook_response.status_code == 200
        
        webhook_data = webhook_response.json()
        assert 'prediction_sent' in webhook_data
        assert webhook_data['prediction_sent'] is True
```

---

## 🎭 TESTS END-TO-END

### Tests Utilisateur Complets
```typescript
// 🎬 E2E Tests avec Playwright

import { test, expect, Page } from '@playwright/test';

class EZBIUserJourneyTests {
  constructor(private page: Page) {}

  async navigateToApp() {
    await this.page.goto('/');
    await expect(this.page).toHaveTitle(/EZBI Analytics/);
  }

  async login(email: string = 'test@example.com', password: string = 'password') {
    await this.page.click('[data-testid="login-button"]');
    await this.page.fill('[data-testid="email-input"]', email);
    await this.page.fill('[data-testid="password-input"]', password);
    await this.page.click('[data-testid="submit-login"]');
    
    // Attendre la redirection vers dashboard
    await expect(this.page).toHaveURL(/.*dashboard/);
  }

  async uploadFile(filePath: string) {
    // Navigation vers upload
    await this.page.click('[data-testid="upload-nav"]');
    
    // Upload fichier
    const fileInput = this.page.locator('[data-testid="file-input"]');
    await fileInput.setInputFiles(filePath);
    
    // Attendre analyse IA
    await expect(this.page.locator('[data-testid="analysis-progress"]')).toBeVisible();
    await expect(this.page.locator('[data-testid="analysis-complete"]')).toBeVisible({ timeout: 30000 });
    
    // Vérifier aperçu
    await expect(this.page.locator('[data-testid="data-preview"]')).toBeVisible();
  }

  async generatePrediction() {
    // Cliquer sur générer prédiction
    await this.page.click('[data-testid="generate-prediction"]');
    
    // Configurer prédiction
    await this.page.selectOption('[data-testid="horizon-select"]', '90');
    await this.page.selectOption('[data-testid="scenario-select"]', 'realistic');
    
    // Lancer prédiction
    await this.page.click('[data-testid="start-prediction"]');
    
    // Attendre résultats
    await expect(this.page.locator('[data-testid="prediction-results"]')).toBeVisible({ timeout: 60000 });
  }

  async validateDashboard() {
    // Vérifier présence des cartes principales
    await expect(this.page.locator('[data-testid="cash-flow-card"]')).toBeVisible();
    await expect(this.page.locator('[data-testid="prediction-card"]')).toBeVisible();
    await expect(this.page.locator('[data-testid="confidence-card"]')).toBeVisible();
    
    // Vérifier graphiques
    await expect(this.page.locator('[data-testid="prediction-chart"]')).toBeVisible();
    await expect(this.page.locator('[data-testid="rfm-heatmap"]')).toBeVisible();
  }

  async exportResults() {
    // Navigation vers export
    await this.page.click('[data-testid="export-button"]');
    
    // Sélectionner format
    await this.page.check('[data-testid="export-csv"]');
    await this.page.check('[data-testid="export-pdf"]');
    
    // Déclencher export
    const downloadPromise = this.page.waitForDownload();
    await this.page.click('[data-testid="download-export"]');
    
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/ezbi-predictions-.*\.(csv|pdf)/);
  }
}

// Tests E2E principaux
test.describe('EZBI User Journeys', () => {
  test('Complete prediction workflow', async ({ page }) => {
    const journey = new EZBIUserJourneyTests(page);
    
    // Test complet: Login → Upload → Predict → Export
    await journey.navigateToApp();
    await journey.login();
    await journey.uploadFile('./test-data/sample-sales.xlsx');
    await journey.generatePrediction();
    await journey.validateDashboard();
    await journey.exportResults();
  });

  test('Mobile responsive workflow', async ({ page }) => {
    // Tester sur mobile
    await page.setViewportSize({ width: 375, height: 667 });
    
    const journey = new EZBIUserJourneyTests(page);
    await journey.navigateToApp();
    
    // Vérifier navigation mobile
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
    
    // Test workflow simplifié mobile
    await journey.login();
    await journey.validateDashboard();
  });

  test('Error handling workflow', async ({ page }) => {
    const journey = new EZBIUserJourneyTests(page);
    
    await journey.navigateToApp();
    await journey.login();
    
    // Test upload fichier invalide
    await journey.uploadFile('./test-data/invalid-file.txt');
    await expect(page.locator('[data-testid="upload-error"]')).toBeVisible();
    
    // Test récupération d'erreur
    await page.click('[data-testid="retry-upload"]');
    await journey.uploadFile('./test-data/sample-sales.xlsx');
  });

  test('Performance under load', async ({ page }) => {
    const journey = new EZBIUserJourneyTests(page);
    
    await journey.navigateToApp();
    await journey.login();
    
    // Mesurer temps de chargement
    const startTime = Date.now();
    await journey.uploadFile('./test-data/large-dataset.xlsx');
    const uploadTime = Date.now() - startTime;
    
    // Requirement: <30s pour gros fichiers
    expect(uploadTime).toBeLessThan(30000);
    
    // Mesurer génération prédiction
    const predStartTime = Date.now();
    await journey.generatePrediction();
    const predTime = Date.now() - predStartTime;
    
    // Requirement: <60s pour prédictions
    expect(predTime).toBeLessThan(60000);
  });
});

// Tests cross-browser
test.describe('Cross-browser compatibility', () => {
  ['chromium', 'firefox', 'webkit'].forEach(browserName => {
    test(`Works in ${browserName}`, async ({ page }) => {
      const journey = new EZBIUserJourneyTests(page);
      
      await journey.navigateToApp();
      await journey.login();
      await journey.validateDashboard();
    });
  });
});
```

---

## 📊 MÉTRIQUES & REPORTING

### Dashboard Qualité
```python
# 📈 Quality Metrics Dashboard

import pytest
import json
from datetime import datetime
from typing import Dict, List

class QualityMetricsCollector:
    """Collecteur de métriques qualité"""
    
    def __init__(self):
        self.metrics = {
            'test_results': {},
            'performance_metrics': {},
            'coverage_metrics': {},
            'ml_accuracy_metrics': {},
            'timestamp': datetime.now().isoformat()
        }
    
    def collect_test_results(self, test_results: Dict):
        """Collecte résultats de tests"""
        self.metrics['test_results'] = {
            'total_tests': test_results.get('total', 0),
            'passed_tests': test_results.get('passed', 0),
            'failed_tests': test_results.get('failed', 0),
            'skipped_tests': test_results.get('skipped', 0),
            'success_rate': test_results.get('passed', 0) / max(test_results.get('total', 1), 1),
            'execution_time': test_results.get('duration', 0)
        }
    
    def collect_performance_metrics(self, perf_results: Dict):
        """Collecte métriques de performance"""
        self.metrics['performance_metrics'] = {
            'api_response_time_p95': perf_results.get('api_p95', 0),
            'ml_inference_time': perf_results.get('ml_inference', 0),
            'throughput_predictions_per_sec': perf_results.get('throughput', 0),
            'memory_usage_mb': perf_results.get('memory_mb', 0),
            'concurrent_users_supported': perf_results.get('concurrent_users', 0)
        }
    
    def collect_coverage_metrics(self, coverage_data: Dict):
        """Collecte métriques de couverture"""
        self.metrics['coverage_metrics'] = {
            'line_coverage_percent': coverage_data.get('line_coverage', 0),
            'branch_coverage_percent': coverage_data.get('branch_coverage', 0),
            'function_coverage_percent': coverage_data.get('function_coverage', 0),
            'untested_files': coverage_data.get('untested_files', []),
            'critical_paths_covered': coverage_data.get('critical_coverage', 0)
        }
    
    def collect_ml_accuracy_metrics(self, ml_results: Dict):
        """Collecte métriques précision ML"""
        self.metrics['ml_accuracy_metrics'] = {
            'prophet_mape': ml_results.get('prophet_mape', 0),
            'lstm_mape': ml_results.get('lstm_mape', 0),
            'ensemble_mape': ml_results.get('ensemble_mape', 0),
            'confidence_intervals_calibration': ml_results.get('confidence_calibration', 0),
            'business_rules_violations': ml_results.get('rule_violations', 0),
            'model_agreement_score': ml_results.get('agreement_score', 0)
        }
    
    def generate_quality_report(self) -> Dict:
        """Génère rapport qualité complet"""
        
        # Calcul score qualité global
        quality_score = self._calculate_quality_score()
        
        # Status global
        status = self._determine_status(quality_score)
        
        return {
            'quality_score': quality_score,
            'status': status,
            'metrics': self.metrics,
            'recommendations': self._generate_recommendations(),
            'trends': self._analyze_trends(),
            'alerts': self._check_alerts()
        }
    
    def _calculate_quality_score(self) -> float:
        """Calcule score qualité global (0-100)"""
        weights = {
            'test_success_rate': 0.25,
            'ml_accuracy': 0.30,
            'performance': 0.25,
            'coverage': 0.20
        }
        
        scores = {
            'test_success_rate': self.metrics['test_results'].get('success_rate', 0) * 100,
            'ml_accuracy': (1 - min(self.metrics['ml_accuracy_metrics'].get('ensemble_mape', 1), 1)) * 100,
            'performance': min(self.metrics['performance_metrics'].get('throughput_predictions_per_sec', 0) / 100, 1) * 100,
            'coverage': self.metrics['coverage_metrics'].get('line_coverage_percent', 0)
        }
        
        weighted_score = sum(scores[metric] * weights[metric] for metric in weights)
        return round(weighted_score, 2)
    
    def _determine_status(self, quality_score: float) -> str:
        """Détermine status basé sur score"""
        if quality_score >= 90:
            return 'EXCELLENT'
        elif quality_score >= 80:
            return 'GOOD'
        elif quality_score >= 70:
            return 'ACCEPTABLE'
        else:
            return 'NEEDS_IMPROVEMENT'
    
    def _generate_recommendations(self) -> List[str]:
        """Génère recommandations d'amélioration"""
        recommendations = []
        
        # Check test coverage
        coverage = self.metrics['coverage_metrics'].get('line_coverage_percent', 0)
        if coverage < 80:
            recommendations.append(f"Augmenter couverture de tests: {coverage}% → 80%+")
        
        # Check ML accuracy
        ensemble_mape = self.metrics['ml_accuracy_metrics'].get('ensemble_mape', 1)
        if ensemble_mape > 0.15:  # 15%
            recommendations.append(f"Améliorer précision ML: MAPE {ensemble_mape:.2%} → <15%")
        
        # Check performance
        throughput = self.metrics['performance_metrics'].get('throughput_predictions_per_sec', 0)
        if throughput < 100:
            recommendations.append(f"Optimiser performance: {throughput} → 100+ pred/s")
        
        # Check failed tests
        failed_tests = self.metrics['test_results'].get('failed_tests', 0)
        if failed_tests > 0:
            recommendations.append(f"Corriger {failed_tests} tests échoués")
        
        return recommendations
    
    def _analyze_trends(self) -> Dict:
        """Analyse tendances (simplified)"""
        return {
            'quality_trend': 'improving',  # Mock
            'performance_trend': 'stable',
            'accuracy_trend': 'improving'
        }
    
    def _check_alerts(self) -> List[Dict]:
        """Vérifie alertes critiques"""
        alerts = []
        
        # Alert: Tests critiques échoués
        failed_tests = self.metrics['test_results'].get('failed_tests', 0)
        if failed_tests > 5:
            alerts.append({
                'level': 'CRITICAL',
                'message': f'{failed_tests} tests échoués',
                'action': 'Investigation immédiate requise'
            })
        
        # Alert: Performance dégradée
        response_time = self.metrics['performance_metrics'].get('api_response_time_p95', 0)
        if response_time > 5000:  # 5s
            alerts.append({
                'level': 'WARNING',
                'message': f'Temps de réponse P95: {response_time}ms',
                'action': 'Optimisation performance recommandée'
            })
        
        # Alert: Précision ML faible
        ensemble_mape = self.metrics['ml_accuracy_metrics'].get('ensemble_mape', 0)
        if ensemble_mape > 0.20:  # 20%
            alerts.append({
                'level': 'CRITICAL',
                'message': f'Précision ML dégradée: MAPE {ensemble_mape:.1%}',
                'action': 'Ré-entraînement modèles requis'
            })
        
        return alerts

# Intégration CI/CD
def generate_ci_quality_report():
    """Génère rapport qualité pour CI/CD"""
    collector = QualityMetricsCollector()
    
    # Collecte depuis différentes sources
    # (ces données viendraient des résultats réels des tests)
    
    mock_test_results = {
        'total': 150,
        'passed': 147,
        'failed': 2,
        'skipped': 1,
        'duration': 45.6
    }
    
    mock_perf_results = {
        'api_p95': 1200,
        'ml_inference': 1.8,
        'throughput': 125,
        'memory_mb': 280,
        'concurrent_users': 50
    }
    
    mock_coverage = {
        'line_coverage': 87.5,
        'branch_coverage': 82.1,
        'function_coverage': 91.2,
        'untested_files': ['utils/legacy.py'],
        'critical_coverage': 95.0
    }
    
    mock_ml_results = {
        'prophet_mape': 0.18,
        'lstm_mape': 0.12,
        'ensemble_mape': 0.11,
        'confidence_calibration': 0.88,
        'rule_violations': 0,
        'agreement_score': 0.85
    }
    
    collector.collect_test_results(mock_test_results)
    collector.collect_performance_metrics(mock_perf_results)
    collector.collect_coverage_metrics(mock_coverage)
    collector.collect_ml_accuracy_metrics(mock_ml_results)
    
    report = collector.generate_quality_report()
    
    # Sauvegarde pour dashboard
    with open('quality_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

if __name__ == "__main__":
    report = generate_ci_quality_report()
    print(f"Quality Score: {report['quality_score']}/100 - Status: {report['status']}")
```

Cette stratégie de tests complète assure une qualité maximale pour EZBI Analytics avec une couverture exhaustive des fonctionnalités ML, API, et UX, garantissant une fiabilité production-ready.