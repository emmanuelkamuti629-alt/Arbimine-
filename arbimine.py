# ARBIMINE PRO MAX - Top 15 Exchanges + All Coins Cross-Exchange Spot Arbitrage Scanner
# GitHub Ready | Full Market Scan

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
            'options': {
                'defaultType': 'spot'
            }
        })

        # Load markets first
        markets = exchange.load_markets()

        # Fetch all tickers
        tickers = exchange.fetch_tickers()

        for symbol, ticker in tickers.items():

            # Strictly USDT spot only
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

        print(f"✓ {ex_id.upper()} | {len(results)} USDT pairs scanned")
        return ex_id, results, True

    except Exception as e:
        print(f"✗ {ex_id.upper()} failed: {str(e)[:100]}")
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

# Analyze every coin across all exchanges
for symbol, listings in market_data.items():

    # Must exist on at least 2 exchanges
    if len(listings) < 2:
        continue

    # Highest buyer
    highest_bid = max(listings, key=lambda x: x['bid'])

    # Lowest seller
    lowest_ask = min(listings, key=lambda x: x['ask'])

    # Skip same exchange
    if highest_bid['exchange'] == lowest_ask['exchange']:
        continue

    # Profit %
    gross_profit = ((highest_bid['bid'] - lowest_ask['ask']) / lowest_ask['ask']) * 100

    # Net after fees
    net_profit = gross_profit - TRADING_FEE

    # Liquidity check
    min_volume = min(highest_bid.get('baseVolume', 0), lowest_ask.get('baseVolume', 0))

    if net_profit >= MIN_PROFIT and min_volume > 0:
        opportunities.append({
            'symbol': symbol,
            'buy_exchange': lowest_ask['exchange'],
            'buy_price': lowest_ask['ask'],
            'sell_exchange': highest_bid['exchange'],
            'sell_price': highest_bid['bid'],
            'profit': net_profit,
            'volume': min_volume
        })

# Sort by profit descending
opportunities.sort(key=lambda x: x['profit'], reverse=True)

# Final output
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"✅ Exchanges Successful: {exchange_success}")
print(f"❌ Exchanges Failed: {exchange_failed}")
print(f"🪙 Coins Scanned: {len(market_data)}")
print(f"💎 Opportunities Found: {len(opportunities)}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

if opportunities:

    print("🔥 TOP LIVE SPOT ARBITRAGE OPPORTUNITIES:\n")

    for i, opp in enumerate(opportunities[:100], 1):  # Top 100
        print(
            f"{i}. {opp['symbol']} | "
            f"BUY {opp['buy_exchange'].upper()} @ {opp['buy_price']:.8f} | "
            f"SELL {opp['sell_exchange'].upper()} @ {opp['sell_price']:.8f} | "
            f"PROFIT {opp['profit']:.2f}% | "
            f"VOL {opp['volume']:.2f}"
        )

else:
    print("❌ No profitable arbitrage opportunities found.")

print("\n🔥 ARBIMINE PRO MAX COMPLETE")