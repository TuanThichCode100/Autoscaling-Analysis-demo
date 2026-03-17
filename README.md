# Autoscaling Analysis for Web Traffic

## Overview
This project analyzes web server traffic logs and builds a forecasting system to support autoscaling decisions. The goal is to predict future load and determine when to scale resources up or down.

---

## Problem
Given historical request logs:
- Predict future traffic load
- Trigger autoscaling decisions based on predicted demand

---

## Data Pipeline
Raw Logs → Cleaning → Feature Engineering → Time Series Aggregation

Key features:
- Request count over time
- Traffic patterns (hourly/daily)
- Peak vs off-peak behavior

---

## Modeling
We experimented with:
- Time Series models: LightGBM + EMWA
- Input: historical traffic
- Output: predicted request load

---

## Results
Evaluation metrics:
- RMSE: 13.786
- MAE: 10.397

Model performance shows ability to capture traffic trends and spikes.

---

## Full Report
[Link to PDF](https://drive.google.com/file/d/1o391kAKipRAC__mSMdQhG8rylAGETSt9/view?usp=sharing)

---

## Authors
FantasticFour Team
