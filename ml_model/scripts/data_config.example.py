# ML Model Data Configuration
# Copy this file to data_config.py and update paths

# OPTION 1: Use absolute paths to your dataset location
DATA_PATHS = {
    "train": "D:/MyDatasets/autoscaler/train.parquet",  # ← Thay bằng path thật của bạn
    "test": "D:/MyDatasets/autoscaler/test.parquet",
    "raw_logs": "D:/MyDatasets/autoscaler/raw/",
}

# OPTION 2: Use relative paths (data in project folder)
# Uncomment if you want to use project-local data
# from pathlib import Path
# BASE_DIR = Path(__file__).parent.parent
# DATA_PATHS = {
#     "train": str(BASE_DIR / "data" / "processed" / "train.parquet"),
#     "test": str(BASE_DIR / "data" / "processed" / "test.parquet"),
#     "raw_logs": str(BASE_DIR / "data" / "raw"),
# }

# Model save path
MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_PATH = str(MODEL_DIR / "lgb_model.pkl")
