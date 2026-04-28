import ccxt
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

print("🚀 ARBIMINE PRO MAX STARTED")
print(f"⏰ Scan Time: {datetime.now()}")
print("🌍 Scanning Top 15 Exchanges | All USDT Spot Pairs\n")

# Top 15 global exchanges
exchange_ids = [
    'binance', 'bybit', 'okx', 'kucoin', 'gateio',
    'mexc', 'bitget', 'huobi', 'kraken', 'bitfinex',
    'bitstamp', 'crypto', 'phemex', 'woo', 'coinbase'
]

# Settings
MIN_PROFIT = 0.5      # Minimum net profit %
TRADING_FEE = 0.25    # Estimated total fees %
MAX_THREADS = 15

# Global market storage
market_data = {}
exchange_success = 0
exchange_failed = 0

def scan_exchange(ex_id):
    results = {}
    try:
        exchange_class = getattr(ccxt, ex_id)
        exchange = exchange_class({
            'enableRateLimit': True,
            'timeout': 20000,
            'options': {'defaultType': 'spot'}
        })
        markets = exchange.load_markets()
        tickers = exchange.fetch_tickers()
        
        for symbol, ticker in tickers.items():
            if not symbol.endswith('/USDT'):
                continue
            if symbol not in markets:
                continue
            if not markets[symbol].get('spot', False):
                continue
            
            bid = ticker.get('bid')
            ask = ticker.get('ask')
            
            if bid and ask and ask > 0:
                results[symbol] = {
                    'exchange': ex_id,
                    'bid': bid,
                    'ask': ask,
                    'baseVolume': ticker.get('baseVolume', 0)
                }
        
        print(f"✓ {ex_id.upper()} | {len(results)} USDT pairs")
        return ex_id, results, True
    except Exception as e:
        print(f"✗ {ex_id.upper()} failed")
        return ex_id, {}, False

# Multi-threaded scan
with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    futures = [executor.submit(scan_exchange, ex) for ex in exchange_ids]
    for future in as_completed(futures):
        ex_id, data, success = future.result()
        if success:
            exchange_success += 1
        else:
            exchange_failed += 1
        for symbol, info in data.items():
            if symbol not in market_data:
                market_data[symbol] = []
            market_data[symbol].append(info)

print("\n🔍 ANALYZING CROSS-EXCHANGE OPPORTUNITIES...\n")

opportunities = []

for symbol, listings in market_data.items():
    if len(listings) < 2:
        continue
    
    highest_bid = max(listings, key=lambda x: x['bid'])
    lowest_ask = min(listings, key=lambda x: x['ask'])
    
    if highest_bid['exchange'] == lowest_ask['exchange']:
        continue
    
    gross_profit = ((highest_bid['bid'] - lowest_ask['ask']) / lowest_ask['ask']) * 100
    net_profit = gross_profit - TRADING_FEE
    min_volume = min(highest_bid.get('baseVolume', 0), lowest_ask.get('baseVolume', 0))
    
    if net_profit >= MIN_PROFIT and min_volume > 0:
        opportunities.append({
            'symbol': symbol,
            'buy_exchange': lowest_ask['exchange'].upper(),
            'buy_price': lowest_ask['ask'],
            'sell_exchange': highest_bid['exchange'].upper(),
            'sell_price': highest_bid['bid'],
            'profit': net_profit,
            'volume': min_volume
        })

opportunities.sort(key=lambda x: x['profit'], reverse=True)

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"✅ Exchanges Successful: {exchange_success}")
print(f"❌ Exchanges Failed: {exchange_failed}")
print(f"🪙 Coins Scanned: {len(market_data)}")
print(f"💎 Opportunities Found: {len(opportunities)}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

if opportunities:
    print("🔥 TOP LIVE SPOT ARBITRAGE OPPORTUNITIES:\n")
    for i, opp in enumerate(opportunities[:20], 1):
        print(f"{i}. {opp['symbol']} | BUY {opp['buy_exchange']} @ {opp['buy_price']:.8f} | SELL {opp['sell_exchange']} @ {opp['sell_price']:.8f} | PROFIT {opp['profit']:.2f}% | VOL {opp['volume']:.2f}")
else:
    print("❌ No profitable arbitrage opportunities found.")

print("\n🔥 ARBIMINE PRO MAX COMPLETE")