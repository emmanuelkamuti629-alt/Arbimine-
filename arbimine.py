#!/usr/bin/env python3
import asyncio
import ccxt.async_support as ccxt_async
from datetime import datetime

print("🚀 ArbiMine Scanner Running!")

async def main():
    exchanges = ['binance', 'kucoin', 'bybit', 'okx']
    print(f"Scanning at {datetime.now()}\n")
    
    for ex_id in exchanges:
        try:
            ex = getattr(ccxt_async, ex_id)({'enableRateLimit': True})
            tickers = await ex.fetch_tickers()
            count = 0
            for symbol, data in tickers.items():
                if symbol.endswith('/USDT') and data.get('bid') and data.get('ask'):
                    profit = ((data['bid'] - data['ask']) / data['ask']) * 100
                    if profit > 0.3:
                        print(f"✓ {symbol}: {profit:.2f}% on {ex_id}")
                        count += 1
            await ex.close()
        except:
            print(f"✗ {ex_id} failed")
    
    print("\n✅ Scan complete!")

asyncio.run(main())
