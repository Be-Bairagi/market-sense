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
        open_price = df["Open"]
        volume = df["Volume"].astype(float)

        # --- Momentum ---
        features["rsi_14"] = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]

        macd_ind = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
        features["macd_diff_ratio"] = (macd_ind.macd().iloc[-1] - macd_ind.macd_signal().iloc[-1]) / close.iloc[-1] * 100

        # --- Trend (Stationary: Price vs EMA Ratios) ---
        for period in [9, 21, 50, 200]:
            if len(df) >= period:
                ema = ta.trend.EMAIndicator(close, window=period).ema_indicator().iloc[-1]
                features[f"price_vs_ema_{period}"] = (close.iloc[-1] - ema) / ema * 100
            else:
                features[f"price_vs_ema_{period}"] = None

        if len(df) >= 14:
            features["adx_14"] = ta.trend.ADXIndicator(high, low, close, window=14).adx().iloc[-1]

        # --- Volatility ---
        bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        bb_high = bb.bollinger_hband().iloc[-1]
        bb_low = bb.bollinger_lband().iloc[-1]
        bb_range = bb_high - bb_low
        if bb_range > 0:
            features["bollinger_position"] = (close.iloc[-1] - bb_low) / bb_range
        else:
            features["bollinger_position"] = 0.5

        features["atr_14_ratio"] = ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range().iloc[-1] / close.iloc[-1] * 100

        for win in [5, 10, 20]:
            features[f"volatility_{win}d"] = close.pct_change().rolling(win).std().iloc[-1] * 100

        # --- Volume ---
        vol_20d_avg = volume.rolling(20).mean().iloc[-1]
        features["volume_spike_ratio"] = float(volume.iloc[-1]) / vol_20d_avg if vol_20d_avg > 0 else 1.0

        # --- Candle Patterns (Stationary Shadows/Body) ---
        body = abs(close - open_price)
        avg_body = body.rolling(10).mean().iloc[-1]
        features["body_ratio"] = body.iloc[-1] / avg_body if avg_body > 0 else 1.0
        
        upper_sh = high - df[["Open", "Close"]].max(axis=1)
        lower_sh = df[["Open", "Close"]].min(axis=1) - low
        features["upper_shadow_ratio"] = upper_sh.iloc[-1] / close.iloc[-1] * 100
        features["lower_shadow_ratio"] = lower_sh.iloc[-1] / close.iloc[-1] * 100

        # --- Returns (Lags) ---
        for lag in [1, 5, 20]:
            features[f"return_{lag}d"] = close.pct_change(lag).iloc[-1] * 100

        # Current price (STILL NEEDED for target calculation/UI, but not used as a model feature)
        features["current_close"] = float(close.iloc[-1])

        # Sanitize
        sanitized = {}
        for k, v in features.items():
            if v is None or pd.isna(v):
                sanitized[k] = 0.0
            else:
                sanitized[k] = float(v)

        return sanitized

    @staticmethod
    def compute_all_history(df: pd.DataFrame) -> pd.DataFrame:
        """
        Efficiently compute technical indicators for an entire history.
        Returns a DataFrame where each row contains features for that date.
        """
        if df.empty or len(df) < 14:
            return pd.DataFrame()

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        open_price = df["Open"]
        volume = df["Volume"].astype(float)

        hist_df = pd.DataFrame(index=df.index)

        # 1. Momentum
        hist_df["rsi_14"] = ta.momentum.RSIIndicator(close, window=14).rsi()
        macd_ind = ta.trend.MACD(close)
        hist_df["macd_diff_ratio"] = (macd_ind.macd() - macd_ind.macd_signal()) / close * 100

        # 2. Stationary Trends (Ratios)
        for period in [9, 21, 50, 200]:
            ema = ta.trend.EMAIndicator(close, window=period).ema_indicator()
            hist_df[f"price_vs_ema_{period}"] = (close - ema) / ema * 100

        hist_df["adx_14"] = ta.trend.ADXIndicator(high, low, close).adx()

        # 3. Volatility
        bb = ta.volatility.BollingerBands(close)
        bb_h, bb_l = bb.bollinger_hband(), bb.bollinger_lband()
        hist_df["bollinger_position"] = (close - bb_l) / (bb_h - bb_l).replace(0, 1)
        hist_df["atr_14_ratio"] = ta.volatility.AverageTrueRange(high, low, close).average_true_range() / close * 100
        
        for win in [5, 10, 20]:
            hist_df[f"volatility_{win}d"] = close.pct_change().rolling(win).std() * 100

        # 4. Volume
        vol_avg = volume.rolling(20).mean()
        hist_df["volume_spike_ratio"] = volume / vol_avg.replace(0, 1)

        # 5. Shadows & Body
        body = abs(close - open_price)
        hist_df["body_ratio"] = body / body.rolling(10).mean().replace(0, 1)
        upper_sh = high - df[["Open", "Close"]].max(axis=1)
        lower_sh = df[["Open", "Close"]].min(axis=1) - low
        hist_df["upper_shadow_ratio"] = upper_sh / close * 100
        hist_df["lower_shadow_ratio"] = lower_sh / close * 100

        # 6. Returns
        for lag in [1, 5, 10, 20]:
            hist_df[f"return_{lag}d"] = close.pct_change(lag) * 100

        # 7. Price position (Stationary relative to year)
        high_52w = high.rolling(252, min_periods=1).max()
        low_52w = low.rolling(252, min_periods=1).min()
        hist_df["dist_52w_high"] = (close - high_52w) / high_52w * 100
        hist_df["dist_52w_low"] = (close - low_52w) / low_52w * 100

        hist_df["current_close"] = close

        return hist_df.fillna(0)
