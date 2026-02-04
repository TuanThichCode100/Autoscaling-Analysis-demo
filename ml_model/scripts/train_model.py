"""
Train LightGBM model for request rate forecasting
Dự đoán residual (deviation từ baseline)
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path

import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from feature_engineering import prepare_data


def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> lgb.LGBMRegressor:
    """
    Train LightGBM regressor với optimal hyperparameters
    
    Args:
        X_train: Training features
        y_train: Training target (residuals)
    
    Returns:
        Trained LightGBM model
    """
    model = lgb.LGBMRegressor(
        objective="regression",
        metric="mae",
        learning_rate=0.05,
        num_leaves=31,
        max_depth=6,
        min_data_in_leaf=150,
        feature_fraction=0.8,
        bagging_fraction=0.8,
        bagging_freq=1,
        lambda_l2=5,
        n_estimators=500,
        random_state=42,
        verbose=-1
    )
    
    model.fit(X_train, y_train)
    return model


def evaluate_model(model: lgb.LGBMRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """
    Evaluate model performance trên residuals
    
    Args:
        model: Trained model
        X_test: Test features
        y_test: Test target
    
    Returns:
        Dictionary với metrics
    """
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    
    metrics = {
        "mae": float(mae),
        "mse": float(mse),
        "rmse": float(rmse),
        "r2": float(r2)
    }
    
    return metrics


def save_model(model: lgb.LGBMRegressor, model_path: str):
    """Save model to disk"""
    joblib.dump(model, model_path)
    print(f"✅ Model saved to {model_path}")


def print_feature_importance(model: lgb.LGBMRegressor, top_n: int = 15):
    """Print top N important features"""
    feature_importance = pd.DataFrame({
        "feature": model.feature_name_,  # Fixed: feature_name_ not feature_names_
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)
    
    print(f"\n📊 Top {top_n} Important Features:")
    print(feature_importance.head(top_n).to_string(index=False))


if __name__ == "__main__":
    # Paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    models_dir = base_dir / "models"
    
    # Try to load custom data paths from config
    try:
        from data_config import DATA_PATHS, MODEL_PATH
        train_path = DATA_PATHS["train"]
        test_path = DATA_PATHS["test"]
        model_save_path = MODEL_PATH
        print("✅ Using custom data paths from data_config.py")
    except ImportError:
        # Fallback to default paths
        train_path = str(data_dir / "processed" / "train.parquet")
        test_path = str(data_dir / "processed" / "test.parquet")
        model_save_path = str(models_dir / "lgb_model.pkl")
        print("ℹ️  Using default data paths (create data_config.py for custom paths)")
    
    print("=" * 60)
    print("🚀 Training LightGBM Model for Request Rate Forecasting")
    print("=" * 60)
    
    # ========== Load data ==========
    print("\n📥 Loading data...")
    print(f"  - Train: {train_path}")
    print(f"  - Test:  {test_path}")
    
    df_train_raw = pd.read_parquet(train_path)
    df_test_raw = pd.read_parquet(test_path)
    print(f"  - Train records: {len(df_train_raw)}")
    print(f"  - Test records: {len(df_test_raw)}")
    
    # ========== Feature engineering ==========
    print("\n🔧 Building features...")
    X_train, y_train, df_train = prepare_data(df_train_raw)
    X_test, y_test, df_test = prepare_data(df_test_raw)
    print(f"  - Train samples: {len(X_train)}")
    print(f"  - Test samples: {len(X_test)}")
    print(f"  - Features: {X_train.shape[1]}")
    
    # ========== Train model ==========
    print("\n🤖 Training model...")
    model = train_model(X_train, y_train)
    print("  ✅ Training complete")
    
    # ========== Evaluate ==========
    print("\n📈 Evaluating on test set...")
    metrics = evaluate_model(model, X_test, y_test)
    print(f"  - MAE:  {metrics['mae']:.2f}")
    print(f"  - RMSE: {metrics['rmse']:.2f}")
    print(f"  - R²:   {metrics['r2']:.4f}")
    
    # ========== Save metrics to JSON ==========
    print("\n💾 Saving metrics...")
    from datetime import datetime
    import json
    
    metrics_with_metadata = {
        **metrics,
        "trained_at": datetime.now().isoformat(),
        "model_version": "1.0",
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "features": X_train.shape[1]
    }
    
    metrics_path = str(models_dir / "metrics.json")
    with open(metrics_path, 'w') as f:
        json.dump(metrics_with_metadata, f, indent=2)
    print(f"  ✅ Metrics saved to {metrics_path}")
    
    # ========== Feature importance ==========
    print_feature_importance(model, top_n=10)
    
    # ========== Save model ==========
    print("\n💾 Saving model...")
    print(f"  - Path: {model_save_path}")
    save_model(model, model_save_path)
    
    print("\n✅ Training pipeline complete!")

