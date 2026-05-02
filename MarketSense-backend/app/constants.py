"""
Centralized constants for MarketSense High-Accuracy Pipeline.
"""

# --- Prediction Settings ---
PREDICTION_HORIZON_DAYS = 5
DIRECTION_THRESHOLD_PCT = 0.02  # 2% move for UP/DOWN labels
CONFIDENCE_GATE_THRESHOLD = 0.65  # Only signals > 65% are shown as BUY/SELL

# --- Sequence Lengths ---
BILSTM_SEQUENCE_LENGTH = 60
PROPHET_HISTORY_YEARS = 5

# --- Training Hyperparameters ---
# OPTUNA_TRIALS: Best possible is 100, but 60 is high-accuracy balanced
OPTUNA_TRIALS = 60  
SHAP_TOP_FEATURES = 20
METRIC_TOLERANCE = 0.01  # 1% improvement required to replace model

# Walk-Forward Validation (Best: 10, Prod: 8)
WALK_FORWARD_SPLITS = 8
WALK_FORWARD_GAP = 5

# Deep Learning (LSTM)
LSTM_HIDDEN_SIZE = 64
LSTM_NUM_LAYERS = 2
LSTM_BATCH_SIZE = 32
MAX_EPOCHS = 150 # Best: 200
LSTM_PATIENCE = 20
LSTM_DROPOUT = 0.3

# Adaptive Labeling (Phase 3 Booster)
DIRECTION_THRESHOLD_ADAPTIVE = True
DIRECTION_THRESHOLD_PERCENTILE = 40 # Target ~40% of samples as non-HOLD

# --- Meta-Learner (Stacking) Settings ---
META_LEARNER_N_ESTIMATORS = 300
META_LEARNER_MAX_DEPTH = 4
META_LEARNER_LEARNING_RATE = 0.03
META_LEARNER_SUBSAMPLE = 0.8
META_LEARNER_COL_BYTREE = 0.8

# --- Base Model Tuning Boundaries ---
XGB_N_ESTIMATORS_RANGE = (200, 1500)
XGB_MAX_DEPTH_RANGE = (3, 10)
XGB_LEARNING_RATE_RANGE = (0.005, 0.2)

# --- Feature Engineering ---
# Technical Indicators
VOLATILITY_WINDOWS = [10, 20, 30, 60]
EMA_WINDOWS = [9, 21, 50, 100, 200]
LAG_PERIODS = [1, 2, 3, 5, 10, 20]

RSI_WINDOW = 14
EMA_FAST = 12
EMA_SLOW = 26

# --- Ensemble Weights (Base - Used for fallback/averaging) ---
XGB_WEIGHT = 0.4
LSTM_WEIGHT = 0.4
PROPHET_WEIGHT = 0.2

# --- Indian Market Calendar ---
BUDGET_MONTH = 2
EXPIRY_DAY_OF_WEEK = 3  # Thursday
RESULTS_MONTHS = [1, 4, 7, 10]
