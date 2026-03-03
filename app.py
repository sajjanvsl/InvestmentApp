import yfinance as yf
import pandas as pd
import ta

# Nifty sample (you can extend to full 50)
nifty50 = [
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "INFY.NS",
    "ICICIBANK.NS",
]

def clean_dataframe(df):
    """
    Fix for yfinance MultiIndex and 2D column issue
    """

    # If MultiIndex columns, flatten them
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Ensure required columns exist
    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    df = df[required_cols]

    # Force each column to pure 1D Series
    for col in required_cols:
        df[col] = pd.Series(df[col].values.flatten(), index=df.index)

    return df


def scan():
    results = []

    for stock in nifty50:

        df = yf.download(
            stock,
            period="6mo",
            auto_adjust=True,
            progress=False,
            group_by="column"
        )

        if df.empty:
            continue

        df = clean_dataframe(df)

        # Indicators
        df["EMA20"] = ta.trend.ema_indicator(close=df["Close"], window=20)
        df["EMA50"] = ta.trend.ema_indicator(close=df["Close"], window=50)
        df["RSI"] = ta.momentum.rsi(close=df["Close"], window=14)
        df["ATR"] = ta.volatility.average_true_range(
            df["High"], df["Low"], df["Close"], window=14
        )
        df["AvgVol"] = df["Volume"].rolling(20).mean()

        df.dropna(inplace=True)

        if df.empty:
            continue

        latest = df.iloc[-1]

        score = 0

        if latest["EMA20"] > latest["EMA50"]:
            score += 25

        if 45 < latest["RSI"] < 65:
            score += 20

        if latest["Volume"] > 1.2 * latest["AvgVol"]:
            score += 20

        if latest["Close"] > df["High"].rolling(20).max().iloc[-2]:
            score += 15

        if latest["ATR"] > df["ATR"].mean():
            score += 10

        score += 10  # Relative strength placeholder

        results.append((stock, score))

    return sorted(results, key=lambda x: x[1], reverse=True)


# For testing standalone
if __name__ == "__main__":
    print(scan())
