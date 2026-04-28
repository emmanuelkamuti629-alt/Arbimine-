import ccxt
from datetime import datetime

print("ArbiMine Scanner Running!")
print(f"Scanning at {datetime.now()}\n")

ex = ccxt.binance()
tickers = ex.fetch_tickers()

count = 0
for symbol, data in tickers.items():
    if symbol.endswith('/USDT') and data.get('bid') and data.get('ask'):
        profit = ((data['bid'] - data['ask']) / data['ask']) * 100
        if profit > 0.3:
            print(f"🎯 {symbol}: {profit:.2f}%")
            count += 1

print(f"\n✅ Found {count} opportunities!")