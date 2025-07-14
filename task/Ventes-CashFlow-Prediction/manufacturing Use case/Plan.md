Perfect — you're aiming for a **production-grade synthetic data engine** simulating a **manufacturing business**, with realistic financial, operational, and sales records, written daily into **Excel** and **PostgreSQL** for analysis or application use.

We’ll break this into the following structure:

---

## 🏭 SIMULATED COMPANY CONTEXT

**Business Type:** Mid-sized manufacturing company
**Product:** Custom metal parts
**Sales Model:** B2B sales with Net-30 payment terms
**Production Model:** Made-to-order (MTO), small batches
**Operating Cadence:** Daily operations, bi-weekly payroll, monthly rent, machine maintenance, variable production costs
**Financing:** Working capital loan, credit line for raw materials
**Tool Stack:**

* PostgreSQL → primary datastore
* Excel/CSV → data snapshots and reporting
* Python → simulation engine (daily loop)

---

## 🗂️ KEY DATA DOMAINS TO SIMULATE (WITH DETAIL)

### 1. **Sales and Invoices**

| Field          | Description                 |
| -------------- | --------------------------- |
| `invoice_id`   | Unique invoice ID           |
| `customer_id`  | Links to customer table     |
| `date_issued`  | Invoice date                |
| `due_date`     | Net-30 payment terms        |
| `amount`       | Value of sale (1000–50,000) |
| `status`       | Open, Paid, Overdue         |
| `payment_date` | When the invoice was paid   |

Daily events:

* 1–3 new invoices/day
* Random delays in payment (5–15% go overdue)
* Mix of large and small customers

**Excel Tab:** `invoices.xlsx`
**SQL Table:** `sales.invoices`

---

### 2. **Accounts Receivable**

AR aging buckets auto-generated:

* 0–30 days
* 31–60 days
* 61–90 days
* 90+ days

Daily reconciliation updates balances based on payments received.

**SQL Table:** `accounting.accounts_receivable`

---

### 3. **Production Orders**

| Field                | Description                     |
| -------------------- | ------------------------------- |
| `order_id`           | Unique production order ID      |
| `product_code`       | From product catalog            |
| `start_date`         | When manufacturing started      |
| `completion_date`    | Expected finish                 |
| `status`             | In progress / completed         |
| `cost_of_goods_sold` | Direct costs (labor + material) |
| `units_produced`     | Output qty                      |

Daily:

* 0–2 new production orders
* Completion lags 1–5 days
* Unit costs vary due to input prices

**SQL Table:** `operations.production_orders`
**Excel Tab:** `production.xlsx`

---

### 4. **Purchases and Accounts Payable**

| Field            | Description                         |
| ---------------- | ----------------------------------- |
| `purchase_id`    | Unique transaction ID               |
| `vendor_id`      | Vendor info                         |
| `category`       | Raw materials, tools, repairs, etc. |
| `amount`         | Purchase amount                     |
| `date`           | Purchase date                       |
| `due_date`       | Net-30 or Net-15                    |
| `payment_status` | Paid / Outstanding                  |

Simulated vendors:

* Steel supplier
* Maintenance company
* Tool manufacturer
* Software (ERP, AutoCAD licenses)

**SQL Table:** `accounting.accounts_payable`
**Excel Tab:** `payables.xlsx`

---

### 5. **Cash Flow Ledger**

This is your daily bank-like ledger:

| Field            | Description                                       |
| ---------------- | ------------------------------------------------- |
| `transaction_id` | Unique                                            |
| `date`           | Entry date                                        |
| `amount`         | Positive (inflow) or negative (outflow)           |
| `type`           | Sale, Purchase, Payroll, Loan Repayment, Interest |
| `counterparty`   | Who it came from or went to                       |
| `description`    | Human-readable label                              |

Daily:

* All invoices paid → inflow
* All purchases, rent, interest → outflow
* Payroll every 2 weeks
* Occasional loan repayment

**SQL Table:** `finance.cash_ledger`
**Excel Tab:** `cash_flow.xlsx`

---

### 6. **Debt & Financing**

| Field               | Description                  |
| ------------------- | ---------------------------- |
| `loan_id`           | ID                           |
| `type`              | Working capital, Credit Line |
| `amount`            | Outstanding amount           |
| `interest_rate`     | Simulated (5–10%)            |
| `last_payment_date` | Payment made                 |
| `next_due`          | Date                         |

Monthly interest charges + occasional principal repayments.

**SQL Table:** `finance.debt`
**Excel Tab:** `debt_schedule.xlsx`

---

### 7. **Fixed Costs (OPEX)**

Scheduled entries:

* Rent (monthly)
* Software licenses
* Utilities (weekly/monthly)
* Insurance

Pre-programmed schedule, not randomly generated.

**SQL Table:** `expenses.fixed_costs`
**Excel Tab:** `expenses.xlsx`

---

### 8. **HR & Payroll**

| Field            | Description                    |
| ---------------- | ------------------------------ |
| `employee_id`    | Unique                         |
| `department`     | Assembly, Logistics, Admin     |
| `monthly_salary` | Base salary                    |
| `pay_date`       | Bi-weekly (every other Friday) |
| `bonus`          | Optional quarterly             |

Fixed payroll schedule + annual bonuses.

**SQL Table:** `hr.payroll_log`
**Excel Tab:** `payroll.xlsx`

---

## 🔁 DAILY SIMULATION FLOW

Every simulated day (via Python cron):

1. **Create 1–3 new invoices**
2. **Create or update production orders**
3. **Update AR / AP aging and cash balances**
4. **Process due AP payments (outflows)**
5. **Receive some payments (AR inflow)**
6. **Generate ledger entries**
7. **Update Excel + PostgreSQL**

---
