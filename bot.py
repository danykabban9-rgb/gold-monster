"""
GOLD-MONSTER V2 - Full Gold Trading System
Symbol: XAUUSD / GC=F
Strategy: MA Crossover + RSI Filter + ATR Risk Management
"""
import yfinance as yf
import pandas as pd
import numpy as np

SYMBOL = "GC=F" # Gold
PERIOD = "6mo"
CAPITAL = 10000
RISK_PER_TRADE = 0.02 # 2%

def get_data():
    print(f"📈 Downloading {SYMBOL}...")
    df = yf.download(SYMBOL, period=PERIOD, interval="1d", auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def add_indicators(df):
    # Moving Averages
    df['MA9'] = df['Close'].rolling(9).mean()
    df['MA21'] = df['Close'].rolling(21).mean()
    df['MA50'] = df['Close'].rolling(50).mean()

    # RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # ATR for Stop Loss
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L','H-PC','L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(14).mean()

    return df.dropna()

def generate_signals(df):
    df['Signal'] = 0
    # BUY: MA9 crosses above MA21 AND RSI > 50 AND price above MA50 (trend filter)
    buy_cond = (df['MA9'] > df['MA21']) & (df['MA9'].shift(1) <= df['MA21'].shift(1)) & (df['RSI'] > 50) & (df['Close'] > df['MA50'])
    # SELL: MA9 crosses below MA21
    sell_cond = (df['MA9'] < df['MA21']) & (df['MA9'].shift(1) >= df['MA21'].shift(1))

    df.loc[buy_cond, 'Signal'] = 1
    df.loc[sell_cond, 'Signal'] = -1
    return df

def backtest(df):
    balance = CAPITAL
    position = 0
    entry_price = 0
    trades = []

    for i in range(1, len(df)):
        price = float(df['Close'].iloc[i])
        atr = float(df['ATR'].iloc[i])

        # Entry
        if df['Signal'].iloc[i] == 1 and position == 0:
            stop_loss = price - (atr * 1.5)
            qty = (balance * RISK_PER_TRADE) / (price - stop_loss)
            position = qty
            entry_price = price
            balance -= qty * price
            trades.append(f"BUY {price:.2f} | SL: {stop_loss:.2f}")

        # Exit
        elif df['Signal'].iloc[i] == -1 and position > 0:
            balance += position * price
            pnl = (price - entry_price) * position
            trades.append(f"SELL {price:.2f} | PnL: ${pnl:.2f}")
            position = 0

    # Final value
    final_price = float(df['Close'].iloc[-1])
    final_value = balance + (position * final_price)
    profit = final_value - CAPITAL
    print(f"\n--- BACKTEST RESULT ---")
    print(f"Initial: ${CAPITAL} -> Final: ${final_value:.2f}")
    print(f"Profit: ${profit:.2f} ({profit/CAPITAL*100:.2f}%)")
    print(f"Trades: {len(trades)}")
    for t in trades[-5:]:
        print(t)
    return final_value

# --- RUN ---
df = get_data()
df = add_indicators(df)
df = generate_signals(df)

last = df.iloc[-1]
print("\n--- LIVE SIGNAL ---")
print(f"Price: ${float(last['Close']):.2f}")
print(f"MA9: {float(last['MA9']):.2f} | MA21: {float(last['MA21']):.2f} | MA50: {float(last['MA50']):.2f}")
print(f"RSI: {float(last['RSI']):.2f} | ATR: {float(last['ATR']):.2f}")

if last['Signal'] == 1:
    print("🚀 GOLD-MONSTER SAYS: BUY - Strong uptrend confirmed!")
    print(f" Suggested Stop Loss: ${float(last['Close'] - last['ATR']*1.5):.2f}")
elif last['Signal'] == -1:
    print("🔻 GOLD-MONSTER SAYS: SELL - Trend weakening!")
else:
    print("⏳ GOLD-MONSTER SAYS: HOLD - No new signal")

backtest(df)
