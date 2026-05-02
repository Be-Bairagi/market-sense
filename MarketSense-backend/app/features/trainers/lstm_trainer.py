import logging
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
from sqlmodel import Session, select
from torch.utils.data import DataLoader, TensorDataset

from app.constants import (
    BILSTM_SEQUENCE_LENGTH,
    DIRECTION_THRESHOLD_ADAPTIVE,
    DIRECTION_THRESHOLD_PCT,
    DIRECTION_THRESHOLD_PERCENTILE,
    LSTM_BATCH_SIZE,
    LSTM_DROPOUT,
    LSTM_HIDDEN_SIZE,
    LSTM_NUM_LAYERS,
    LSTM_PATIENCE,
    MAX_EPOCHS,
)
from app.models.feature_data import FeatureVector
from app.models.stock_data import StockPrice

logger = logging.getLogger(__name__)


class HybridStockModel(nn.Module):
    """
    BiLSTM + GRU Hybrid with Temporal Attention (Phase 4).
    
    This architecture combines the long-term memory of BiLSTM with the 
    efficiency of GRU, using an attention mechanism to focus on 
    critical temporal features.
    """
    def __init__(
        self,
        input_size: int,
        hidden_size: int = LSTM_HIDDEN_SIZE,
        num_layers: int = LSTM_NUM_LAYERS,
        num_classes: int = 3,
        dropout: float = LSTM_DROPOUT,
    ):
        super(HybridStockModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        rnn_dropout = dropout if num_layers > 1 else 0

        self.bilstm = nn.LSTM(
            input_size, 
            hidden_size, 
            num_layers,
            batch_first=True, 
            dropout=rnn_dropout, 
            bidirectional=True
        )
        
        self.gru = nn.GRU(
            input_size, 
            hidden_size, 
            num_layers,
            batch_first=True, 
            dropout=rnn_dropout
        )
        
        combined_size = hidden_size * 3
        self.attention = nn.Sequential(
            nn.Linear(combined_size, combined_size // 2),
            nn.Tanh(),
            nn.Linear(combined_size // 2, 1)
        )
        
        self.classifier = nn.Sequential(
            nn.Linear(combined_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        lstm_out, _ = self.bilstm(x)
        gru_out, _ = self.gru(x)
        combined = torch.cat([lstm_out, gru_out], dim=-1)
        weights = torch.softmax(self.attention(combined), dim=1)
        context = (weights * combined).sum(dim=1)
        return self.classifier(context)


def train_lstm_model(
    symbol: str,
    horizon_days: int = 5,
    seq_length: int = BILSTM_SEQUENCE_LENGTH,
    existing_model_path: Optional[str] = None,
) -> Tuple[Dict, Dict]:
    """
    Train a high-performance Hybrid LSTM+GRU model.
    
    This function implements Phase 4 of the Accuracy Booster Plan:
    1. Prepares sequential data for deep learning.
    2. Applies Adaptive Thresholding for balanced labeling.
    3. Trains a BiLSTM+GRU model with Temporal Attention.
    4. Uses Cosine Annealing and early stopping for optimal convergence.
    
    Args:
        symbol: The stock ticker (e.g., RELIANCE.NS).
        horizon_days: Prediction horizon in days.
        seq_length: Number of past days to look at for each prediction.
        existing_model_path: Optional path to load pre-trained weights.
        
    Returns:
        Tuple[Dict, Dict]: (Model Bundle, Performance Metrics)
    """
    from app.database import engine

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training Hybrid BiLSTM+GRU for {symbol} (batch={LSTM_BATCH_SIZE})...")

    with Session(engine) as db:
        fvs = db.exec(
            select(FeatureVector)
            .where(FeatureVector.symbol == symbol, FeatureVector.horizon == "short_term")
            .order_by(FeatureVector.date.asc())
        ).all()

        if len(fvs) < seq_length + 50:
            raise ValueError(f"Insufficient data for LSTM on {symbol}")

        data = []
        for fv in fvs:
            row = fv.features.copy()
            row["date"] = fv.date
            data.append(row)

        features_df = pd.DataFrame(data).set_index("date")
        features_df.index = pd.to_datetime(features_df.index)
        features_df = features_df[~features_df.index.duplicated(keep="last")]
        features_df = features_df.apply(pd.to_numeric, errors="coerce").fillna(0)

        prices = db.exec(
            select(StockPrice).where(StockPrice.symbol == symbol).order_by(StockPrice.date.asc())
        ).all()

    price_series = pd.Series({pd.to_datetime(p.date): p.close for p in prices})
    
    # Pre-calculate adaptive threshold
    returns_5d = []
    for i in range(len(price_series) - 5):
        returns_5d.append((price_series.iloc[i+5] - price_series.iloc[i]) / price_series.iloc[i])
    
    if DIRECTION_THRESHOLD_ADAPTIVE and returns_5d:
        threshold = float(np.percentile(np.abs(returns_5d), 100 - DIRECTION_THRESHOLD_PERCENTILE))
        threshold = max(threshold, 0.005)
    else:
        threshold = DIRECTION_THRESHOLD_PCT

    feature_dates = sorted(features_df.index.tolist())
    X_list, y_list = [], []
    valid_dates = []

    for i in range(seq_length, len(feature_dates)):
        current_date = feature_dates[i]
        try:
            curr_idx = price_series.index.get_loc(current_date)
            target_idx = curr_idx + horizon_days
            if target_idx < len(price_series):
                ret = (price_series.iloc[target_idx] - price_series.iloc[curr_idx]) / price_series.iloc[curr_idx]
                label = 1 # HOLD
                if ret > threshold: label = 2
                elif ret < -threshold: label = 0
                
                seq_feats = features_df.iloc[i - seq_length : i].values
                X_list.append(seq_feats)
                y_list.append(label)
                valid_dates.append(current_date)
        except (ValueError, IndexError):
            continue

    if not X_list:
        raise ValueError("Could not align sequences.")

    X, y = np.array(X_list), np.array(y_list)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    num_features = X.shape[2]
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train.reshape(-1, num_features)).reshape(X_train.shape)
    X_test_scaled = scaler.transform(X_test.reshape(-1, num_features)).reshape(X_test.shape)

    X_tr_t = torch.FloatTensor(X_train_scaled).to(device)
    y_tr_t = torch.LongTensor(y_train).to(device)
    X_te_t = torch.FloatTensor(X_test_scaled).to(device)
    y_te_t = torch.LongTensor(y_test).to(device)

    train_loader = DataLoader(TensorDataset(X_tr_t, y_tr_t), batch_size=LSTM_BATCH_SIZE, shuffle=False)

    model = HybridStockModel(input_size=num_features).to(device)
    class_counts = np.bincount(y_train, minlength=3)
    class_weights = torch.FloatTensor([len(y_train) / (3.0 * max(c, 1)) for c in class_counts]).to(device)

    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=MAX_EPOCHS)

    # Training Loop
    best_loss, counter, best_state = float('inf'), 0, None
    for epoch in range(MAX_EPOCHS):
        model.train()
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(batch_X), batch_y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

        scheduler.step()
        model.eval()
        with torch.no_grad():
            val_loss = criterion(model(X_te_t), y_te_t).item()
            if val_loss < best_loss:
                best_loss, best_state, counter = val_loss, model.state_dict(), 0
            else:
                counter += 1
                if counter >= LSTM_PATIENCE: break

    if best_state: model.load_state_dict(best_state)
    
    model.eval()
    with torch.no_grad():
        final_y_pred = torch.max(model(X_te_t), 1)[1].cpu().numpy()

    final_acc = accuracy_score(y_test, final_y_pred)
    metrics = {
        "accuracy": round(float(final_acc), 4),
        "directional_accuracy": round(float(accuracy_score(y_test[y_test!=1], final_y_pred[y_test!=1])), 4) if (y_test!=1).any() else final_acc,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "symbol": symbol,
        "horizon": f"{horizon_days}d",
    }

    bundle = {
        "model_state": {k: v.cpu() for k, v in model.state_dict().items()},
        "model_config": {"input_size": num_features, "hidden_size": LSTM_HIDDEN_SIZE, "num_layers": LSTM_NUM_LAYERS, "num_classes": 3},
        "scaler": scaler,
        "seq_length": seq_length,
        "features_in": list(features_df.columns),
        "metrics": metrics,
        "model_type": "Hybrid-LSTM-GRU-v4"
    }

    logger.info(f"LSTM Phase 4 Done. Acc={final_acc:.4f}")
    return bundle, metrics
