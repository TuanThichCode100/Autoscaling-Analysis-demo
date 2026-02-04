"""
Model Inference Module
Load trained model và dự đoán residuals
"""

import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional

from feature_engineering import build_baseline, build_request_rate


class RequestRateForecaster:
    """
    Load trained model và perform inference
    """
    
    def __init__(self, model_path: str):
        """
        Initialize forecaster với trained model
        
        Args:
            model_path: Path to saved LightGBM model
        """
        self.model = joblib.load(model_path)
        # LightGBM uses feature_name() method, not feature_names_ attribute
        try:
            self.feature_names = self.model.feature_name()
        except:
            # Fallback if model doesn't have feature names
            self.feature_names = None
    
    def forecast_residuals(self, recent_logs: pd.DataFrame, window: str = "60S") -> Dict:
        """
        Dự đoán residuals cho tập logs gần đây
        
        Args:
            recent_logs: DataFrame với 'timestamp' column (30-60 phút logs gần đây)
            window: Resample window
        
        Returns:
            Dictionary với forecast results
        """
        # Build request rate
        rate_df = build_request_rate(recent_logs, window)
        
        if len(rate_df) < 10:
            return {"error": "Not enough data points"}
        
        # Build baseline
        df_with_baseline = build_baseline(rate_df)
        
        # Build features (last 5 records)
        df = df_with_baseline.copy()
        r = df["residual"]
        
        # Lag features
        for lag in [1, 2, 3, 5]:
            df[f"lag_{lag}"] = r.shift(lag)
        
        # Volatility & range
        for win in [3, 5]:
            df[f"roll_std_{win}"] = r.shift(1).rolling(win).std()
            df[f"roll_max_{win}"] = r.shift(1).rolling(win).max()
            df[f"roll_min_{win}"] = r.shift(1).rolling(win).min()
        
        # Burst dynamics
        df["diff_1"] = r.shift(1) - r.shift(2)
        df["diff_2"] = r.shift(1) - r.shift(3)
        df["acceleration"] = df["diff_1"] - df["diff_2"]
        df["abs_diff_1"] = df["diff_1"].abs()
        df["burst_strength"] = df["abs_diff_1"] / (df["roll_std_3"] + 1e-5)
        df["range_expand"] = df["roll_max_5"] - df["roll_min_5"]
        
        # Get last valid row
        df_valid = df.dropna()
        
        if len(df_valid) == 0:
            return {"error": "Not enough data to build features"}
        
        last_row = df_valid.iloc[-1]
        
        # Get features - exclude non-feature columns
        feature_cols = [col for col in df_valid.columns 
                       if col not in ['timestamp', 'request_rate', 'baseline', 'residual']]
        
        if self.feature_names is not None:
            X_last = last_row[self.feature_names].values.reshape(1, -1)
        else:
            X_last = last_row[feature_cols].values.reshape(1, -1)
        
        # Predict residual
        residual_pred = self.model.predict(X_last)[0]
        
        # Convert back to request rate
        baseline = last_row["baseline"]
        request_rate_pred = baseline + residual_pred
        
        return {
            "timestamp": last_row["timestamp"],
            "actual_rate": float(last_row["request_rate"]),
            "baseline": float(baseline),
            "predicted_residual": float(residual_pred),
            "predicted_rate": max(0, float(request_rate_pred)),  # RPS can't be negative
            "volatility": float(last_row["roll_std_5"]),
            "burst_strength": float(last_row["burst_strength"])
        }
    
    def batch_forecast(self, recent_logs: pd.DataFrame, window: str = "60S", steps: int = 5) -> List[Dict]:
        """
        Forecast multiple steps ahead (use previous predictions as input)
        
        Args:
            recent_logs: Historical logs
            window: Resample window
            steps: Number of steps to forecast
        
        Returns:
            List of forecast results
        """
        forecasts = []
        
        for _ in range(steps):
            forecast = self.forecast_residuals(recent_logs, window)
            
            if "error" in forecast:
                break
            
            forecasts.append(forecast)
        
        return forecasts


def get_forecaster(model_dir: Optional[str] = None) -> RequestRateForecaster:
    """
    Factory function để get RequestRateForecaster
    
    Args:
        model_dir: Path to models directory (default: ml_model/models)
    
    Returns:
        RequestRateForecaster instance
    """
    if model_dir is None:
        model_dir = str(Path(__file__).parent.parent / "models")
    
    model_path = str(Path(model_dir) / "lgb_model.pkl")
    return RequestRateForecaster(model_path)


# ========== Quick test ==========
if __name__ == "__main__":
    import sys
    
    base_dir = Path(__file__).parent.parent
    
    # Load test data
    df_test = pd.read_parquet(str(base_dir / "data" / "processed" / "test.parquet"))
    print(f"Loaded {len(df_test)} test records")
    
    # Initialize forecaster
    forecaster = get_forecaster()
    print("✅ Model loaded")
    
    # Get last 2 hours of logs
    last_2h = df_test.tail(500)
    
    # Forecast
    result = forecaster.forecast_residuals(last_2h)
    print("\n📊 Forecast result:")
    for key, val in result.items():
        print(f"  {key}: {val}")
