import logging
import numpy as np
import pandas as pd
from typing import Tuple

logger = logging.getLogger(__name__)

class DataCleanerService:
    """
    Centralized service for cleaning and pre-processing stock market data.
    Ensures data is consistent, gap-free, and free of massive outliers before storage.
    """

    @staticmethod
    def clean_ohlcv(df: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
        """
        Cleans OHLCV data. Returns (cleaned_df, quality_score).
        Quality score is 1.0 (perfect) to 0.0 (bad).
        """
        if df.empty:
            return df, 0.0

        initial_rows = len(df)
        
        # 1. Standardize columns
        # yfinance 0.2.x can return MultiIndex columns. Flatten if necessary.
        new_columns = []
        for col in df.columns:
            # If multi-index (tuple), take the first level (e.g., 'Close' from ('Close', 'REL...'))
            actual_col = col[0] if isinstance(col, tuple) else col
            new_columns.append(str(actual_col).capitalize())
        df.columns = new_columns
        
        # 2. Handle missing values
        # Prices: Forward fill (carry over last known price)
        price_cols = ["Open", "High", "Low", "Close"]
        for col in price_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].ffill().bfill() # Forward fill, then backward fill for very start
        
        # Volume: Fill with 0
        if "Volume" in df.columns:
            df["Volume"] = pd.to_numeric(df["Volume"], errors='coerce').fillna(0).astype(int)

        # 3. Integrity Checks: High should be highest, Low lowest
        if all(col in df.columns for col in price_cols):
            # Ensure High is max of all prices
            df["High"] = df[price_cols].max(axis=1)
            # Ensure Low is min of all prices
            df["Low"] = df[price_cols].min(axis=1)

        # 4. Outlier Detection: Identify suspicious spikes (>20% move)
        # We calculate daily returns and clip moves beyond 20% if they look like anomalies
        # Note: In real world, this needs to be checked against volume/news.
        df["Returns"] = df["Close"].pct_change().fillna(0)
        outliers = (df["Returns"].abs() > 0.20)
        outlier_count = outliers.sum()
        
        if outlier_count > 0:
            logger.warning(f"Detected {outlier_count} potential price outliers (>20% move).")
            # For this MVP, we log them. Future versions could clip or flag for review.

        # 5. Calculate Quality Score
        # Lost rows, missing values, and outliers penalize the score
        missing_count = int(df[price_cols].isna().sum().sum())
        quality_score = max(0.0, 1.0 - (missing_count / (initial_rows * 4)) - (outlier_count / initial_rows))

        # Standardize types for DB (Native Python types)
        for col in price_cols:
            df[col] = df[col].astype(float)

        # Cleanup temp columns
        if "Returns" in df.columns:
            df.drop(columns=["Returns"], inplace=True)

        return df, float(round(quality_score, 2))

    @staticmethod
    def validate_integrity(df: pd.DataFrame) -> bool:
        """Quick check if OHLC requirements are met."""
        required = {"Date", "Open", "High", "Low", "Close"}
        if not required.issubset(set(df.columns)):
            return False
            
        # Check for any High < Low
        if (df["High"] < df["Low"]).any():
            return False
            
        return True
