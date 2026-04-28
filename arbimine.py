import ccxt
from datetime import datetime

print("🚀 ArbiMine Scanner Running!")
print(f"Scanning at {datetime.now()}\n")

exchanges = [
    ccxt.binance(),
    ccxt.kucoin(),
    ccxt.bybit(),
    ccxt.okx(),
    ccxt.gateio(),
    ccxt.mexc(),
    ccxt.bitmart(),
    ccxt.huobi(),
    ccxt.kraken(),
    ccxt.bitfinex(),
    ccxt.crypto(),
    ccxt.bitstamp(),
    ccxt.gemini(),
    ccxt.phemex(),
    ccxt.woo()
]

total_opportunities = 0

for ex in exchanges:
    try:
        name = str(ex).split('.')[1].upper()
        print(f"✓ {name} - Scanning...")
        tickers = ex.fetch_tickers()
        count = 0
        
        for symbol, data in tickers.items():
            if symbol.endswith('/USDT') and data.get('bid') and data.get('ask'):
                profit = ((data['bid'] - data['ask']) / data['ask']) * 100
                if profit > 0.3:
                    print(f"  🎯 BUY {name} SELL {name} | {symbol} | {profit:.2f}%")
                    count += 1
                    total_opportunities += 1
        
        print(f"  → Found {count} opportunities\n")
        
    except Exception as e:
        print(f"✗ {name} - Failed\n")

print(f"✅ TOTAL OPPORTUNITIES FOUND: {total_opportunities}")