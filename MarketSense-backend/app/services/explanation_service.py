import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ExplanationService:
    """
    Translates raw feature values and model importance scores 
    into plain-English 'Key Drivers' and 'Bear Cases'.
    """

    @staticmethod
    def explain(features: Dict, top_features: Dict) -> List[str]:
        """
        Takes the current feature values and the model's global/local 
        feature importance to explain the 'Why' behind a prediction.
        """
        drivers = []
        
        # Sort by importance
        sorted_imp = sorted(top_features.items(), key=lambda x: x[1], reverse=True)
        top_keys = [k for k, v in sorted_imp if v > 0.05]  # Significant features
        
        # 1. Technical Indicators
        if "rsi_14" in top_keys:
            val = features.get("rsi_14")
            if val is not None:
                if val < 35: drivers.append("RSI shows oversold recovery potential")
                elif val > 75: drivers.append("RSI warns of overbought conditions")
                else: drivers.append("Momentum (RSI) is in neutral-positive territory")
        
        if "macd_histogram" in top_keys:
            val = features.get("macd_histogram")
            if val is not None:
                if val > 0: drivers.append("Positive MACD crossover (bullish trend)")
                else: drivers.append("MACD divergence suggests trend weakness")

        if "volume_spike_ratio" in top_keys:
            val = features.get("volume_spike_ratio")
            if val is not None and val > 1.2:
                drivers.append(f"Unusual volume spike ({round(val, 1)}x) suggests high accumulation")

        # 2. Market Context & Sentiment
        if "sentiment_sentiment_24h" in top_keys:
            val = features.get("sentiment_sentiment_24h")
            if val is not None and val > 0.3:
                drivers.append("News sentiment is exceptionally positive")
        
        if "nifty_trend_ema50" in top_keys:
            val = features.get("nifty_trend_ema50")
            if val == 1.0: drivers.append("Broad market (NIFTY 50) is in uptrend")
            else: drivers.append("Weak NIFTY 50 sentiment dragging sector prices")

        # Fail-safe drivers if indicators don't map cleanly
        if len(drivers) < 3:
            for k, _ in sorted_imp[:3]:
                if k not in ["rsi_14", "macd_histogram", "volume_spike_ratio"]:
                    drivers.append(f"Strong signal from {k.replace('_', ' ').capitalize()}")

        return drivers[:3]

    @staticmethod
    def generate_bear_case(features: Dict) -> str:
        """Analyze opposing signals to find potential risks."""
        risks = []
        
        # Technical risks
        if features.get("rsi_14", 0) > 70: risks.append("high RSI levels may trigger profit booking")
        if features.get("gap_percent", 0) > 3.0: risks.append("over-extended gap-up may face retracement")
        
        # Macro risks
        vix_change = features.get("india_vix_daily_change_pct", 0)
        if vix_change is not None and vix_change > 5.0:
            risks.append("rising India VIX suggests increasing market volatility")
            
        crude = features.get("brent_crude_daily_change_pct", 0)
        if crude is not None and crude > 2.0:
            risks.append("crude oil price spike may impact input costs")

        if not risks:
            return "Potential global market weakness or unexpected macro volatility could reverse the current trend."
            
        return "Potential risks include " + ", ".join(risks[:2]) + "."
