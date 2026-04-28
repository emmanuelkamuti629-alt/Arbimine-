import ccxt
from datetime import datetime

print("🚀 ArbiMine Scanner Running!")
print(f"Scanning at {datetime.now()}\n")

# Top 15 exchanges
exchange_ids = [
    'binance', 'kucoin', 'bybit', 'okx', 'gateio',
    'mexc', 'bitmart', 'huobi', 'kraken', 'bitfinex',
    'crypto', 'bitstamp', 'gemini', 'phemex', 'woo'
]

total_opportunities = 0

for ex_id in exchange_ids:
    try:
        print(f"✓ {ex_id.upper()} - Scanning...")
        
        # Create exchange instance
        exchange_class = getattr(ccxt, ex_id)
        ex = exchange_class()
        
        # Fetch tickers
        tickers = ex.fetch_tickers()
        count = 0
        
        for symbol, data in tickers.items():
            if symbol.endswith('/USDT') and data.get('bid') and data.get('ask'):
                profit = ((data['bid'] - data['ask']) / data['ask']) * 100
                if profit > 0.3:
                    print(f"  🎯 {symbol}: {profit:.2f}% on {ex_id.upper()}")
                    count += 1
                    total_opportunities += 1
        
        print(f"  → Found {count} opportunities\n")
        
    except Exception as e:
        print(f"✗ {ex_id.upper()} - Failed: {str(e)[:50]}\n")

print(f"✅ TOTAL OPPORTUNITIES: {total_opportunities}")