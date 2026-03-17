# Autoscaling Analysis for Web Traffic

## Overview
This project analyzes web server traffic logs and builds a forecasting system to support autoscaling decisions. The goal is to predict future load and determine when to scale resources up or down.

---

## Problem
Given historical request logs:
- Predict future traffic load
- Trigger autoscaling decisions based on predicted demand

---

## Data Pipeline Architecture

The system implements a proactive **Autoscaling** framework using the **MAPE** (Monitor-Analyze-Plan-Execute) closed-loop architecture.

### 1. Data Collection (Monitor)
* **Dataset**: Utilizes NASA server access logs with over 2 million records.
* **Primary Metrics**: 
    * **Requests Per Second (RPS)**: Measures incoming traffic intensity.
    * **Throughput (Bytes/sec)**: Evaluates bandwidth utilization.
    * **Error Rate**: Monitors 4xx/5xx responses to detect system instability.

### 2. Feature Engineering & Analysis (Analyze)
* **Time Windows**:
    * **1-minute (Extraction)**: Preserves data burstiness while filtering second-level noise.
    * **5-minute (Decision)**: Prevents extreme reactions to transient fluctuations.
* **Statistical Indicators**:
    * **Burstiness Analysis**: Uses the Coefficient of Variation ($CV_{score}$) to distinguish signal from noise and provide early warnings.
    * **Inter-arrival Time (IAT)**: Analyzes request density to confirm heavy-tail distribution patterns.
    * **Auto-Correlation Function (ACF)**: Identifies time dependencies for effective lag-based feature selection.

### 3. Forecasting Framework (Plan)
* **Model Selection**: Hybrid **LightGBM + EWMA** (Exponential Weighted Moving Average).
* **Optimization**: EWMA smooths signals to reduce noise, while LightGBM captures complex non-linear HTTP traffic patterns.
* **Performance**: Achieves $R^2 \approx 0.89$ at a 15-minute horizon, providing a "golden window" to mitigate container cold start latency.

### 4. Scaling Execution (Execute)
* **Finite State Machine (FSM)**: Manages transitions between `STABLE`, `SCALING_UP`, `SCALING_DOWN`, and `PANIC` states.
* **Proactive Formula**: Target replicas ($N_{raw}$) are calculated based on predicted traffic ($\hat{R}_{t+h}$):
  $$
  N_{raw} = \lceil \frac{\hat{R}_{t+h}}{C} \times (1 + k) \rceil
  $$
* **Stability Controls**:
    * **Asymmetric Hysteresis**: Uses different thresholds for scaling up ($\delta_{up}$) and down ($\delta_{down}$) to prevent "flapping".
    * **Asymmetric Cooldown**: Priorities high availability with $T_{cooldown}^{down} \gg T_{cooldown}^{up}$.
    * **Reactive Fallback**: Triggers immediate scaling in **PANIC** mode if $Latency_{p95} > SLO$ or prediction error exceeds limits.

---

## Modeling
We experimented with:
- Time Series models: LightGBM + EMWA
- Input: historical traffic
- Output: predicted request load

---

## Results
Evaluation metrics: (15 minutes)
- RMSE: 116.118
- MAE: 84.982

Model performance shows ability to capture traffic trends and spikes.

---

## Full Report
[Link to PDF](https://drive.google.com/file/d/1o391kAKipRAC__mSMdQhG8rylAGETSt9/view?usp=sharing)

---

## Authors
FantasticFour Team
