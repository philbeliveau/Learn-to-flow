# 🔗 SPÉCIFICATIONS D'INTÉGRATION - EZBI ANALYTICS

## 🎯 PHILOSOPHIE D'INTÉGRATION

### Vision Integration-First
```
🔗 "Seamless Manufacturing Ecosystem"

Principes Directeurs:
├── Manufacturing Native: Optimisé pour écosystème industriel français
├── ERP Integration: Sage, SAP, solutions locales
├── Banking APIs: Open Banking natif
├── Real-time Sync: Synchronisation temps réel
└── Security First: Sécurité et conformité RGPD
```

### Architecture d'Intégration
```
🌐 Integration Architecture Overview

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                EZBI ANALYTICS                                       │
│                              Integration Layer                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
            ┌───────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
            │  ERP SYSTEMS │    │  BANK APIs  │    │  EXTERNAL   │
            │              │    │             │    │   SERVICES  │
            │ - Sage       │    │ - Open Bank │    │ - Slack     │
            │ - SAP        │    │ - Direct    │    │ - Email     │
            │ - Cegid      │    │ - Agrégateurs│    │ - Webhooks  │
            │ - Custom     │    │ - Fintech   │    │ - APIs      │
            └──────────────┘    └─────────────┘    └─────────────┘
                    │                   │                   │
                    └───────────────────┼───────────────────┘
                                        │
                    ┌───────────────────▼───────────────────┐
                    │          MIDDLEWARE LAYER            │
                    │                                       │
                    │ - API Gateway                        │
                    │ - Rate Limiting                      │
                    │ - Authentication                     │
                    │ - Data Transformation               │
                    │ - Error Handling                    │
                    │ - Monitoring                        │
                    └───────────────────────────────────────┘
```

---

## 🏭 INTÉGRATIONS ERP

### Sage Integration
```python
# 🏭 integrations/sage_integration.py - Intégration Sage

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import requests
from app.core.config import settings
from app.models.transaction import Transaction
from app.schemas.integration import SageTransaction, SyncResult
import xml.etree.ElementTree as ET

class SageIntegration:
    """Intégration avec Sage (100, X3, etc.)"""
    
    def __init__(self, company_config: Dict):
        self.base_url = company_config.get('sage_url')
        self.username = company_config.get('sage_username')
        self.password = company_config.get('sage_password')
        self.database = company_config.get('sage_database')
        self.version = company_config.get('sage_version', '100')
        self.session = requests.Session()
        self.auth_token = None
    
    async def authenticate(self) -> bool:
        """Authentification avec Sage"""
        
        if self.version == '100':
            return await self._authenticate_sage100()
        elif self.version == 'X3':
            return await self._authenticate_sageX3()
        else:
            raise ValueError(f"Version Sage non supportée: {self.version}")
    
    async def _authenticate_sage100(self) -> bool:
        """Authentification Sage 100"""
        
        auth_payload = {
            'username': self.username,
            'password': self.password,
            'database': self.database
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=auth_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                self.auth_token = response.json().get('token')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                return True
            
            return False
            
        except Exception as e:
            print(f"Erreur authentification Sage 100: {e}")
            return False
    
    async def sync_transactions(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> SyncResult:
        """Synchroniser les transactions depuis Sage"""
        
        if not await self.authenticate():
            raise Exception("Échec de l'authentification Sage")
        
        # Récupérer les factures clients
        sales_data = await self._get_sales_invoices(start_date, end_date)
        
        # Récupérer les factures fournisseurs
        purchase_data = await self._get_purchase_invoices(start_date, end_date)
        
        # Récupérer les paiements
        payment_data = await self._get_payments(start_date, end_date)
        
        # Transformer les données
        transactions = []
        transactions.extend(self._transform_sales_data(sales_data))
        transactions.extend(self._transform_purchase_data(purchase_data))
        transactions.extend(self._transform_payment_data(payment_data))
        
        return SyncResult(
            total_records=len(transactions),
            successful_records=len(transactions),
            failed_records=0,
            transactions=transactions,
            sync_timestamp=datetime.utcnow()
        )
    
    async def _get_sales_invoices(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Récupérer les factures de vente"""
        
        # Sage 100 SQL query equivalent
        query_params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'table': 'F_DOCENTETE',
            'fields': [
                'DO_Piece',      # Numéro de pièce
                'DO_Date',       # Date
                'DO_Tiers',      # Client
                'DO_TotalHT',    # Montant HT
                'DO_TotalTTC',   # Montant TTC
                'DO_Echeance',   # Échéance
                'DO_Statut'      # Statut
            ]
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/documents/invoices",
                params=query_params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('data', [])
            
            return []
            
        except Exception as e:
            print(f"Erreur récupération factures ventes: {e}")
            return []
    
    async def _get_purchase_invoices(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Récupérer les factures d'achat"""
        
        query_params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'document_type': 'PURCHASE_INVOICE'
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/documents/purchases",
                params=query_params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('data', [])
            
            return []
            
        except Exception as e:
            print(f"Erreur récupération factures achats: {e}")
            return []
    
    def _transform_sales_data(self, sales_data: List[Dict]) -> List[SageTransaction]:
        """Transformer les données de vente"""
        
        transactions = []
        
        for sale in sales_data:
            transaction = SageTransaction(
                external_id=sale['DO_Piece'],
                transaction_date=datetime.strptime(sale['DO_Date'], '%Y-%m-%d'),
                amount=float(sale['DO_TotalTTC']),
                type='sale',
                description=f"Facture vente {sale['DO_Piece']}",
                customer_code=sale['DO_Tiers'],
                payment_terms=self._calculate_payment_terms(sale['DO_Echeance']),
                metadata={
                    'sage_document_type': 'SALES_INVOICE',
                    'sage_status': sale['DO_Statut'],
                    'amount_ht': float(sale['DO_TotalHT']),
                    'amount_ttc': float(sale['DO_TotalTTC'])
                }
            )
            transactions.append(transaction)
        
        return transactions
    
    async def create_customer_invoice(
        self,
        customer_code: str,
        amount: float,
        due_date: datetime,
        description: str
    ) -> Dict:
        """Créer une facture client dans Sage"""
        
        invoice_data = {
            'customer_code': customer_code,
            'amount': amount,
            'due_date': due_date.strftime('%Y-%m-%d'),
            'description': description,
            'currency': 'EUR'
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/documents/create_invoice",
                json=invoice_data,
                timeout=30
            )
            
            if response.status_code == 201:
                return response.json()
            
            raise Exception(f"Erreur création facture: {response.status_code}")
            
        except Exception as e:
            print(f"Erreur création facture Sage: {e}")
            raise
    
    def _calculate_payment_terms(self, echeance: str) -> int:
        """Calculer les délais de paiement"""
        
        # Mapping des codes échéance Sage vers jours
        echeance_mapping = {
            '001': 30,  # 30 jours
            '002': 60,  # 60 jours
            '003': 90,  # 90 jours
            '004': 0,   # Comptant
            '005': 45   # 45 jours
        }
        
        return echeance_mapping.get(echeance, 30)
```

### SAP Integration
```python
# 🏭 integrations/sap_integration.py - Intégration SAP

from typing import Dict, List, Optional
from datetime import datetime
import pyrfc
from app.schemas.integration import SAPTransaction, SyncResult

class SAPIntegration:
    """Intégration avec SAP (Business One, ECC, S/4HANA)"""
    
    def __init__(self, company_config: Dict):
        self.sap_type = company_config.get('sap_type', 'business_one')
        self.connection_params = {
            'ashost': company_config.get('sap_host'),
            'sysnr': company_config.get('sap_system_number'),
            'client': company_config.get('sap_client'),
            'user': company_config.get('sap_username'),
            'passwd': company_config.get('sap_password'),
            'lang': 'FR'
        }
        self.connection = None
    
    async def connect(self) -> bool:
        """Connexion à SAP"""
        
        try:
            self.connection = pyrfc.Connection(**self.connection_params)
            return True
        except Exception as e:
            print(f"Erreur connexion SAP: {e}")
            return False
    
    async def sync_transactions(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> SyncResult:
        """Synchroniser les transactions depuis SAP"""
        
        if not await self.connect():
            raise Exception("Échec de la connexion SAP")
        
        transactions = []
        
        # Récupérer les documents de vente
        sales_docs = await self._get_sales_documents(start_date, end_date)
        transactions.extend(self._transform_sales_documents(sales_docs))
        
        # Récupérer les documents d'achat
        purchase_docs = await self._get_purchase_documents(start_date, end_date)
        transactions.extend(self._transform_purchase_documents(purchase_docs))
        
        # Récupérer les paiements
        payments = await self._get_payments(start_date, end_date)
        transactions.extend(self._transform_payments(payments))
        
        return SyncResult(
            total_records=len(transactions),
            successful_records=len(transactions),
            failed_records=0,
            transactions=transactions,
            sync_timestamp=datetime.utcnow()
        )
    
    async def _get_sales_documents(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Récupérer les documents de vente SAP"""
        
        # RFC function call pour récupérer les factures
        rfc_params = {
            'I_DATE_FROM': start_date.strftime('%Y%m%d'),
            'I_DATE_TO': end_date.strftime('%Y%m%d'),
            'I_DOCUMENT_TYPE': 'F2'  # Facture client
        }
        
        try:
            result = self.connection.call('BAPI_BILLINGDOC_GETLIST', **rfc_params)
            return result.get('BILLING_DOCUMENTS', [])
        except Exception as e:
            print(f"Erreur récupération documents vente SAP: {e}")
            return []
    
    def _transform_sales_documents(self, docs: List[Dict]) -> List[SAPTransaction]:
        """Transformer les documents de vente SAP"""
        
        transactions = []
        
        for doc in docs:
            transaction = SAPTransaction(
                external_id=doc['BILLING_DOC'],
                transaction_date=datetime.strptime(doc['BILL_DATE'], '%Y%m%d'),
                amount=float(doc['NET_VALUE']),
                type='sale',
                description=f"Facture SAP {doc['BILLING_DOC']}",
                customer_code=doc['SOLD_TO_PARTY'],
                currency=doc['CURRENCY'],
                metadata={
                    'sap_document_type': doc['BILL_TYPE'],
                    'sap_company_code': doc['COMP_CODE'],
                    'sap_sales_org': doc['SALES_ORG']
                }
            )
            transactions.append(transaction)
        
        return transactions
```

---

## 🏦 INTÉGRATIONS BANCAIRES

### Open Banking Integration
```python
# 🏦 integrations/open_banking.py - Intégration Open Banking

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import requests
import base64
import jwt
from app.core.config import settings
from app.schemas.integration import BankTransaction, SyncResult

class OpenBankingIntegration:
    """Intégration Open Banking (PSD2) pour banques françaises"""
    
    def __init__(self, bank_config: Dict):
        self.bank_code = bank_config.get('bank_code')  # BNP, CA, SG, etc.
        self.client_id = bank_config.get('client_id')
        self.client_secret = bank_config.get('client_secret')
        self.certificate = bank_config.get('certificate')
        self.private_key = bank_config.get('private_key')
        self.base_url = self._get_bank_api_url()
        self.access_token = None
        self.account_id = bank_config.get('account_id')
    
    def _get_bank_api_url(self) -> str:
        """Récupérer l'URL API selon la banque"""
        
        bank_urls = {
            'BNP': 'https://api.bnpparibas.com/psd2',
            'CA': 'https://api.ca-des-particuliers.com/psd2',
            'SG': 'https://api.societegenerale.com/psd2',
            'LCL': 'https://api.lcl.com/psd2',
            'BNPP': 'https://api.bnpparibas.com/psd2'
        }
        
        return bank_urls.get(self.bank_code, 'https://api.generic-bank.com/psd2')
    
    async def authenticate(self) -> bool:
        """Authentification Open Banking avec certificat"""
        
        # Créer le JWT pour l'authentification
        jwt_payload = {
            'iss': self.client_id,
            'sub': self.client_id,
            'aud': f"{self.base_url}/token",
            'exp': datetime.utcnow() + timedelta(minutes=5),
            'iat': datetime.utcnow(),
            'jti': f"jwt_{datetime.utcnow().timestamp()}"
        }
        
        # Signer le JWT avec la clé privée
        client_assertion = jwt.encode(
            jwt_payload,
            self.private_key,
            algorithm='RS256'
        )
        
        # Demander le token d'accès
        token_data = {
            'grant_type': 'client_credentials',
            'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
            'client_assertion': client_assertion,
            'scope': 'accounts transactions'
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/token",
                data=token_data,
                cert=(self.certificate, self.private_key),
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if response.status_code == 200:
                token_response = response.json()
                self.access_token = token_response['access_token']
                return True
            
            return False
            
        except Exception as e:
            print(f"Erreur authentification Open Banking: {e}")
            return False
    
    async def get_account_transactions(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[BankTransaction]:
        """Récupérer les transactions du compte"""
        
        if not self.access_token:
            if not await self.authenticate():
                raise Exception("Échec de l'authentification bancaire")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Request-ID': f"req_{datetime.utcnow().timestamp()}"
        }
        
        params = {
            'dateFrom': start_date.strftime('%Y-%m-%d'),
            'dateTo': end_date.strftime('%Y-%m-%d'),
            'limit': 1000
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/accounts/{self.account_id}/transactions",
                headers=headers,
                params=params,
                cert=(self.certificate, self.private_key),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._transform_bank_transactions(data.get('transactions', []))
            
            return []
            
        except Exception as e:
            print(f"Erreur récupération transactions bancaires: {e}")
            return []
    
    def _transform_bank_transactions(self, transactions: List[Dict]) -> List[BankTransaction]:
        """Transformer les transactions bancaires"""
        
        transformed = []
        
        for transaction in transactions:
            bank_transaction = BankTransaction(
                external_id=transaction['transactionId'],
                transaction_date=datetime.strptime(
                    transaction['valueDate'], 
                    '%Y-%m-%d'
                ),
                amount=float(transaction['transactionAmount']['amount']),
                currency=transaction['transactionAmount']['currency'],
                type=self._classify_transaction_type(transaction),
                description=transaction.get('remittanceInformationUnstructured', ''),
                counterpart_name=transaction.get('debtorName') or transaction.get('creditorName'),
                counterpart_account=transaction.get('debtorAccount') or transaction.get('creditorAccount'),
                reference=transaction.get('endToEndId'),
                metadata={
                    'bank_code': self.bank_code,
                    'transaction_code': transaction.get('bankTransactionCode'),
                    'booking_date': transaction.get('bookingDate'),
                    'value_date': transaction.get('valueDate')
                }
            )
            transformed.append(bank_transaction)
        
        return transformed
    
    def _classify_transaction_type(self, transaction: Dict) -> str:
        """Classifier le type de transaction"""
        
        amount = float(transaction['transactionAmount']['amount'])
        description = transaction.get('remittanceInformationUnstructured', '').lower()
        
        # Entrant = vente potentielle
        if amount > 0:
            if any(word in description for word in ['virement', 'facture', 'paiement']):
                return 'sale'
            return 'income'
        
        # Sortant = achat/dépense
        else:
            if any(word in description for word in ['fournisseur', 'achat', 'commande']):
                return 'purchase'
            return 'expense'
    
    async def get_account_balance(self) -> Dict:
        """Récupérer le solde du compte"""
        
        if not self.access_token:
            if not await self.authenticate():
                raise Exception("Échec de l'authentification bancaire")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Request-ID': f"req_{datetime.utcnow().timestamp()}"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/accounts/{self.account_id}/balances",
                headers=headers,
                cert=(self.certificate, self.private_key),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                balances = data.get('balances', [])
                
                # Trouver le solde courant
                current_balance = next(
                    (b for b in balances if b['balanceType'] == 'closingBooked'),
                    None
                )
                
                if current_balance:
                    return {
                        'balance': float(current_balance['balanceAmount']['amount']),
                        'currency': current_balance['balanceAmount']['currency'],
                        'date': current_balance['referenceDate']
                    }
            
            return {}
            
        except Exception as e:
            print(f"Erreur récupération solde: {e}")
            return {}
```

---

## 🔗 INTÉGRATIONS EXTERNES

### Slack Integration
```python
# 🔗 integrations/slack_integration.py - Intégration Slack

from typing import Dict, List, Optional
import requests
from datetime import datetime
from app.core.config import settings

class SlackIntegration:
    """Intégration Slack pour notifications"""
    
    def __init__(self, webhook_url: str, channel: str = "#general"):
        self.webhook_url = webhook_url
        self.channel = channel
    
    async def send_prediction_alert(
        self,
        company_name: str,
        prediction_value: float,
        confidence: float,
        target_date: datetime
    ) -> bool:
        """Envoyer une alerte de prédiction"""
        
        # Déterminer la couleur selon la confiance
        if confidence >= 0.9:
            color = "good"
            confidence_label = "Très élevée"
        elif confidence >= 0.7:
            color = "warning"
            confidence_label = "Élevée"
        else:
            color = "danger"
            confidence_label = "Faible"
        
        # Formater le montant
        formatted_amount = f"{prediction_value:,.0f}€".replace(",", " ")
        
        message = {
            "channel": self.channel,
            "username": "EZBI Analytics",
            "icon_emoji": ":chart_with_upwards_trend:",
            "attachments": [
                {
                    "color": color,
                    "title": f"📊 Nouvelle prédiction - {company_name}",
                    "fields": [
                        {
                            "title": "Flux de trésorerie prévu",
                            "value": formatted_amount,
                            "short": True
                        },
                        {
                            "title": "Date cible",
                            "value": target_date.strftime("%d/%m/%Y"),
                            "short": True
                        },
                        {
                            "title": "Niveau de confiance",
                            "value": f"{confidence_label} ({confidence:.0%})",
                            "short": True
                        }
                    ],
                    "timestamp": datetime.utcnow().timestamp()
                }
            ]
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Erreur envoi Slack: {e}")
            return False
    
    async def send_low_cash_flow_alert(
        self,
        company_name: str,
        predicted_amount: float,
        threshold: float,
        target_date: datetime
    ) -> bool:
        """Envoyer une alerte de flux de trésorerie faible"""
        
        formatted_amount = f"{predicted_amount:,.0f}€".replace(",", " ")
        formatted_threshold = f"{threshold:,.0f}€".replace(",", " ")
        
        message = {
            "channel": self.channel,
            "username": "EZBI Analytics",
            "icon_emoji": ":warning:",
            "attachments": [
                {
                    "color": "danger",
                    "title": f"🚨 Alerte flux de trésorerie - {company_name}",
                    "text": f"Le flux de trésorerie prévu ({formatted_amount}) est en dessous du seuil d'alerte ({formatted_threshold})",
                    "fields": [
                        {
                            "title": "Montant prévu",
                            "value": formatted_amount,
                            "short": True
                        },
                        {
                            "title": "Seuil d'alerte",
                            "value": formatted_threshold,
                            "short": True
                        },
                        {
                            "title": "Date",
                            "value": target_date.strftime("%d/%m/%Y"),
                            "short": True
                        }
                    ],
                    "actions": [
                        {
                            "type": "button",
                            "text": "Voir les détails",
                            "url": f"https://ezbi.fr/dashboard/predictions"
                        }
                    ],
                    "timestamp": datetime.utcnow().timestamp()
                }
            ]
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Erreur envoi alerte Slack: {e}")
            return False
```

### Email Integration
```python
# 📧 integrations/email_integration.py - Intégration Email

from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import jinja2
from app.core.config import settings

class EmailIntegration:
    """Intégration Email pour rapports et notifications"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        
        # Template Jinja2
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('templates/email')
        )
    
    async def send_weekly_report(
        self,
        company_name: str,
        recipient_email: str,
        report_data: Dict,
        attachment_path: Optional[str] = None
    ) -> bool:
        """Envoyer le rapport hebdomadaire"""
        
        # Charger le template
        template = self.template_env.get_template('weekly_report.html')
        
        # Générer le contenu HTML
        html_content = template.render(
            company_name=company_name,
            report_data=report_data,
            generated_date=datetime.utcnow().strftime("%d/%m/%Y")
        )
        
        # Créer le message
        message = MIMEMultipart('alternative')
        message['Subject'] = f"📊 Rapport hebdomadaire EZBI - {company_name}"
        message['From'] = self.from_email
        message['To'] = recipient_email
        
        # Ajouter le contenu HTML
        html_part = MIMEText(html_content, 'html', 'utf-8')
        message.attach(html_part)
        
        # Ajouter l'attachment si présent
        if attachment_path:
            with open(attachment_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment_path.split("/")[-1]}'
                )
                message.attach(part)
        
        # Envoyer l'email
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            return True
        except Exception as e:
            print(f"Erreur envoi email: {e}")
            return False
    
    async def send_prediction_summary(
        self,
        recipient_email: str,
        predictions: List[Dict],
        company_name: str
    ) -> bool:
        """Envoyer un résumé des prédictions"""
        
        template = self.template_env.get_template('prediction_summary.html')
        
        # Calculer les statistiques
        total_predictions = len(predictions)
        avg_confidence = sum(p['confidence'] for p in predictions) / total_predictions
        
        html_content = template.render(
            company_name=company_name,
            predictions=predictions,
            total_predictions=total_predictions,
            avg_confidence=avg_confidence,
            generated_date=datetime.utcnow().strftime("%d/%m/%Y")
        )
        
        message = MIMEMultipart('alternative')
        message['Subject'] = f"🔮 Résumé des prédictions - {company_name}"
        message['From'] = self.from_email
        message['To'] = recipient_email
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        message.attach(html_part)
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            return True
        except Exception as e:
            print(f"Erreur envoi résumé prédictions: {e}")
            return False
```

---

## 🔄 WEBHOOK SYSTEM

### Webhook Manager
```python
# 🔄 webhooks/webhook_manager.py - Gestionnaire de webhooks

from typing import Dict, List, Optional, Callable
from datetime import datetime
import asyncio
import httpx
from app.core.database import get_db
from app.models.webhook import WebhookEndpoint, WebhookEvent
from app.schemas.webhook import WebhookPayload, WebhookResponse

class WebhookManager:
    """Gestionnaire de webhooks pour notifications externes"""
    
    def __init__(self):
        self.endpoints: Dict[str, WebhookEndpoint] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
    
    async def register_endpoint(
        self,
        company_id: str,
        endpoint_url: str,
        events: List[str],
        secret: str,
        active: bool = True
    ) -> str:
        """Enregistrer un endpoint webhook"""
        
        endpoint = WebhookEndpoint(
            company_id=company_id,
            url=endpoint_url,
            events=events,
            secret=secret,
            active=active
        )
        
        db = next(get_db())
        db.add(endpoint)
        db.commit()
        
        self.endpoints[endpoint.id] = endpoint
        return endpoint.id
    
    async def trigger_event(
        self,
        company_id: str,
        event_type: str,
        payload: Dict
    ) -> List[WebhookResponse]:
        """Déclencher un événement webhook"""
        
        # Trouver les endpoints concernés
        relevant_endpoints = [
            endpoint for endpoint in self.endpoints.values()
            if endpoint.company_id == company_id
            and event_type in endpoint.events
            and endpoint.active
        ]
        
        responses = []
        
        for endpoint in relevant_endpoints:
            try:
                response = await self._send_webhook(endpoint, event_type, payload)
                responses.append(response)
            except Exception as e:
                print(f"Erreur envoi webhook {endpoint.url}: {e}")
        
        return responses
    
    async def _send_webhook(
        self,
        endpoint: WebhookEndpoint,
        event_type: str,
        payload: Dict
    ) -> WebhookResponse:
        """Envoyer un webhook à un endpoint"""
        
        webhook_payload = WebhookPayload(
            event_type=event_type,
            company_id=endpoint.company_id,
            timestamp=datetime.utcnow(),
            data=payload
        )
        
        # Créer la signature
        signature = self._create_signature(webhook_payload, endpoint.secret)
        
        headers = {
            'Content-Type': 'application/json',
            'X-EZBI-Signature': signature,
            'X-EZBI-Event': event_type,
            'User-Agent': 'EZBI-Webhooks/1.0'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint.url,
                json=webhook_payload.dict(),
                headers=headers,
                timeout=30
            )
        
        # Enregistrer l'événement
        db = next(get_db())
        webhook_event = WebhookEvent(
            endpoint_id=endpoint.id,
            event_type=event_type,
            payload=payload,
            response_status=response.status_code,
            response_body=response.text[:1000],  # Limiter la taille
            sent_at=datetime.utcnow()
        )
        db.add(webhook_event)
        db.commit()
        
        return WebhookResponse(
            endpoint_id=endpoint.id,
            status_code=response.status_code,
            response_body=response.text,
            sent_at=datetime.utcnow()
        )
    
    def _create_signature(self, payload: WebhookPayload, secret: str) -> str:
        """Créer la signature du webhook"""
        
        import hmac
        import hashlib
        import json
        
        payload_str = json.dumps(payload.dict(), sort_keys=True)
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
```

Cette spécification d'intégration complète permet à EZBI Analytics de s'intégrer parfaitement dans l'écosystème technologique des PME manufacturières françaises, avec des connexions natives aux principaux ERP, systèmes bancaires, et outils de communication.