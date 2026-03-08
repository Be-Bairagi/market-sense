import logging
from typing import Dict, Any, List

import pandas as pd
from sqlmodel import Session, select
from sqlalchemy import func

from app.database import engine
from app.models.market_data import InstitutionalActivity, MacroData
from app.models.stock_data import StockPrice, StockMeta

logger = logging.getLogger(__name__)

class MarketPulseService:
    """
    Aggregates macro market indicators for the 30-second snapshot dashboard.
    Returns:
    - Index performance (NIFTY 50, SENSEX)
    - India VIX gauge
    - FII/DII net flow
    - Sector Heatmap
    """

    @staticmethod
    def get_pulse_data() -> Dict[str, Any]:
        """Fetch and aggregate all market pulse data."""
        result = {
            "indices": [],
            "vix": {},
            "fii_dii": {},
            "sectors": []
        }

        with Session(engine) as db:
            # 1. Indices (^NSEI, ^BSESN)
            indices_map = {"^NSEI": "NIFTY 50", "^BSESN": "SENSEX"}
            for symbol, name in indices_map.items():
                prices = db.exec(
                    select(StockPrice)
                    .where(StockPrice.symbol == symbol)
                    .order_by(StockPrice.date.desc())
                    .limit(2)
                ).all()
                
                if len(prices) >= 2:
                    current = prices[0].close
                    prev = prices[1].close
                    change_pct = ((current - prev) / prev) * 100
                    
                    mood = "Sideways"
                    if change_pct > 0.5: mood = "Bullish"
                    elif change_pct < -0.5: mood = "Bearish"
                    
                    result["indices"].append({
                        "name": name,
                        "value": current,
                        "change_pct": change_pct,
                        "mood": mood
                    })

            # 2. VIX
            vix_data = db.exec(
                select(MacroData)
                .where(MacroData.indicator == "INDIA_VIX")
                .order_by(MacroData.date.desc())
                .limit(2)
            ).all()

            if len(vix_data) >= 2:
                current_vix = vix_data[0].value
                prev_vix = vix_data[1].value
                change_pct = ((current_vix - prev_vix) / prev_vix) * 100
                
                # Determine VIX bucket
                status = "Normal"
                if current_vix < 13: status = "Calm"
                elif current_vix > 25: status = "Fearful"
                elif current_vix > 18: status = "Elevated"

                result["vix"] = {
                    "value": current_vix,
                    "change_pct": change_pct,
                    "status": status
                }

            # 3. FII/DII Net Flow (Last 5 Days)
            flows = db.exec(
                select(InstitutionalActivity)
                .order_by(InstitutionalActivity.date.desc())
                .limit(5)
            ).all()

            if flows:
                fii_net_5d = sum([f.fii_net for f in flows])
                dii_net_5d = sum([f.dii_net for f in flows])
                result["fii_dii"] = {
                    "fii_net": fii_net_5d,
                    "dii_net": dii_net_5d,
                    "last_updated": str(flows[0].date)
                }

            # 4. Sector Heatmap
            # First, find the latest common date for stock prices
            latest_date_res = db.exec(
                select(func.max(StockPrice.date))
                .where(StockPrice.symbol != "^NSEI")
                .where(StockPrice.symbol != "^BSESN")
            ).first()

            if latest_date_res:
                # Query prices for the latest 2 days to calculate change
                # Doing this effectively requires querying the last 2 records for each stock.
                # Since sqlite lacks window functions in older versions, we fetch all active NIFTY 50 and do it in Pandas.
                
                tickers_res = db.exec(select(StockMeta).where(StockMeta.is_active == True)).all()
                active_symbols = [t.symbol for t in tickers_res]
                
                prices = db.exec(
                    select(StockPrice.symbol, StockPrice.date, StockPrice.close)
                    .where(StockPrice.symbol.in_(active_symbols))
                    .order_by(StockPrice.symbol, StockPrice.date.desc())
                ).all()

                if prices:
                    # Convert to dataframe
                    df = pd.DataFrame([{"symbol": p.symbol, "date": p.date, "close": p.close} for p in prices])
                    
                    # Sort and get top 2 per symbol
                    df = df.sort_values(["symbol", "date"], ascending=[True, False])
                    df = df.groupby("symbol").head(2)
                    
                    # Need at least 2 records to calculate change
                    valid_symbols = df.groupby("symbol").size()
                    valid_symbols = valid_symbols[valid_symbols == 2].index
                    
                    if not valid_symbols.empty:
                        df_valid = df[df["symbol"].isin(valid_symbols)].copy()
                        
                        # Pivot to get latest vs prev
                        df_pivot = df_valid.pivot(index="symbol", columns="date", values="close")
                        # Sort columns so earlier date is first
                        date_cols = sorted(df_pivot.columns)
                        if len(date_cols) == 2:
                            prev_dt, curr_dt = date_cols[0], date_cols[1]
                            df_pivot["change_pct"] = ((df_pivot[curr_dt] - df_pivot[prev_dt]) / df_pivot[prev_dt]) * 100
                            
                            # Join with sectors
                            meta_df = pd.DataFrame([{"symbol": t.symbol, "sector": t.sector or "Unknown"} for t in tickers_res])
                            df_merged = df_pivot.reset_index().merge(meta_df, on="symbol")
                            
                            # Group by sector
                            sector_group = df_merged.groupby("sector")["change_pct"].agg(["mean", "count"]).reset_index()
                            sector_group = sector_group.sort_values("mean", ascending=False)
                            
                            for _, row in sector_group.iterrows():
                                if row["sector"] != "Unknown":
                                    result["sectors"].append({
                                        "name": row["sector"],
                                        "change_pct": round(row["mean"], 2),
                                        "stock_count": int(row["count"])
                                    })
            
            return result
