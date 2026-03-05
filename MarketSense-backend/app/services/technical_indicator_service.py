import logging
import pandas as pd
import ta
from typing import Dict

logger = logging.getLogger(__name__)


class TechnicalIndicatorService:
    """
    Computes technical indicators from OHLCV data using the `ta` library.
    Returns a flat dict of indicator_name -> value for the latest row.
    """

    @staticmethod
    def compute_all(df: pd.DataFrame) -> Dict[str, float]:
        """
        Compute all technical indicators on an OHLCV DataFrame.
        Expects columns: Open, High, Low, Close, Volume (capitalized).
        Returns a dict of feature_name -> value for the LAST row.
        """
        if df.empty or len(df) < 14:
            logger.warning("Insufficient data for indicator computation (%d rows)", len(df))
            return {}

        features = {}

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"].astype(float)

        # --- Momentum ---
        features["rsi_14"] = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]

        macd_ind = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
        features["macd_line"] = macd_ind.macd().iloc[-1]
        features["macd_signal"] = macd_ind.macd_signal().iloc[-1]
        features["macd_histogram"] = macd_ind.macd_diff().iloc[-1]

        stoch = ta.momentum.StochasticOscillator(high, low, close, window=14, smooth_window=3)
        features["stochastic_k"] = stoch.stoch().iloc[-1]
        features["stochastic_d"] = stoch.stoch_signal().iloc[-1]

        # --- Trend ---
        for period in [9, 21, 50, 200]:
            if len(df) >= period:
                features[f"ema_{period}"] = ta.trend.EMAIndicator(close, window=period).ema_indicator().iloc[-1]
            else:
                features[f"ema_{period}"] = None

        if len(df) >= 14:
            features["adx_14"] = ta.trend.ADXIndicator(high, low, close, window=14).adx().iloc[-1]

        # EMA crossovers (binary signals)
        if features.get("ema_9") is not None and features.get("ema_21") is not None:
            features["ema_9_21_crossover"] = 1.0 if features["ema_9"] > features["ema_21"] else 0.0
        if features.get("ema_50") is not None and features.get("ema_200") is not None:
            features["ema_50_200_crossover"] = 1.0 if features["ema_50"] > features["ema_200"] else 0.0

        # --- Volatility ---
        bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        bb_high = bb.bollinger_hband().iloc[-1]
        bb_low = bb.bollinger_lband().iloc[-1]
        features["bollinger_high"] = bb_high
        features["bollinger_low"] = bb_low
        # Bollinger position: 0 = at lower band, 1 = at upper band
        bb_range = bb_high - bb_low
        if bb_range > 0:
            features["bollinger_position"] = (close.iloc[-1] - bb_low) / bb_range
        else:
            features["bollinger_position"] = 0.5

        features["atr_14"] = ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range().iloc[-1]

        # --- Volume ---
        features["obv"] = ta.volume.OnBalanceVolumeIndicator(close, volume).on_balance_volume().iloc[-1]

        vol_20d_avg = volume.rolling(20).mean().iloc[-1]
        if vol_20d_avg > 0:
            features["volume_spike_ratio"] = float(volume.iloc[-1]) / vol_20d_avg
        else:
            features["volume_spike_ratio"] = 1.0

        # --- Derived ---
        high_52w = high.rolling(min(252, len(df))).max().iloc[-1]
        low_52w = low.rolling(min(252, len(df))).min().iloc[-1]
        range_52w = high_52w - low_52w
        if range_52w > 0:
            features["proximity_52w_high"] = (close.iloc[-1] - low_52w) / range_52w
        else:
            features["proximity_52w_high"] = 0.5

        # Gap up/down %
        if len(df) >= 2:
            prev_close = close.iloc[-2]
            today_open = df["Open"].iloc[-1]
            if prev_close > 0:
                features["gap_percent"] = ((today_open - prev_close) / prev_close) * 100
            else:
                features["gap_percent"] = 0.0
        else:
            features["gap_percent"] = 0.0

        # Current price for reference
        features["current_close"] = float(close.iloc[-1])

        # Sanitize: convert numpy types to native Python floats
        sanitized = {}
        for k, v in features.items():
            if v is None:
                sanitized[k] = None
            elif pd.isna(v):
                sanitized[k] = None
            else:
                sanitized[k] = float(v)

        return sanitized
