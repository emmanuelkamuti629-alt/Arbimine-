# ARBIMINE GITHUB FIXED - Replaces broken old scanner completely
# GitHub Actions Compatible | No Binance/Bybit/Woo/Crypto Errors

import ccxt
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Start timer
start_time = datetime.now()

print("🚀 ARBIMINE GITHUB FIXED STARTED")
print(f"⏰ Scan Time: {start_time}")
print("🌍 Scanning Compatible Exchanges | All USDT Spot Pairs\n")

# ONLY GitHub-friendly exchanges
exchange_ids = [
    'kucoin', 'okx', 'gateio', 'mexc', 'bitmart',
    'htx', 'bitfinex', 'bitstamp', 'phemex', 'coinex',
    'poloniex', 'lbank', 'ascendex', 'bitrue', 'whitebit'
]

# Settings
MIN_PROFIT = 0.5
TRADING_FEE = 0.25
WITHDRAWAL_BUFFER = 0.50
MIN_VOLUME = 50000
MAX_THREADS = 10

# Leveraged token blacklist
BAD_WORDS = ['UP/', 'DOWN/', 'BULL/', 'BEAR/', '3L/', '3S/']

# Storage
market_data = {}
exchange_success = 0
exchange_failed = 0


def scan_exchange(ex_id):
    results = {}

    try:
        # Check exchange support
        if not hasattr(ccxt, ex_id):
            print(f"✗ {ex_id.upper()} unsupported")
            return ex_id, {}, False

        exchange_class = getattr(ccxt, ex_id)

        exchange = exchange_class({
            "enableRateLimit": True,
            "timeout": 30000,
            "options": {"defaultType": "spot"}
        })

        # Load markets
        markets = exchange.load_markets()

        # Skip if no fetchTickers
        if not exchange.has.get("fetchTickers"):
            print(f"✗ {ex_id.upper()} fetchTickers unsupported")
            return ex_id, {}, False

        # Fetch tickers with fallback
        try:
            tickers = exchange.fetch_tickers()
        except:
            tickers = {}

            # Limited fallback for top symbols
            for symbol in list(markets.keys())[:200]:
                try:
                    tickers[symbol] = exchange.fetch_ticker(symbol)
                except:
                    continue

        # Process symbols
        for symbol, ticker in tickers.items():

            # USDT only
            if not symbol.endswith("/USDT"):
                continue

            # Skip leveraged tokens
            if any(word in symbol for word in BAD_WORDS):
                continue

            # Spot only
            if symbol not in markets:
                continue

            if not markets[symbol].get("spot", False):
                continue

            bid = ticker.get("bid")
            ask = ticker.get("ask")
            volume = ticker.get("baseVolume", 0)

            if bid and ask and ask > 0:
                if symbol not in results:
                    results[symbol] = {
                        "exchange": ex_id,
                        "bid": bid,
                        "ask": ask,
                        "baseVolume": volume
                    }

        print(f"✓ {ex_id.upper()} | {len(results)} pairs scanned")
        return ex_id, results, True

    except Exception as e:
        print(f"✗ {ex_id.upper()} failed: {str(e)[:100]}")
        return ex_id, {}, False


# Parallel scan
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

# Cross-exchange arbitrage
for symbol, listings in market_data.items():

    # Must be on 2+ exchanges
    if len(listings) < 2:
        continue

    # Lowest ask = buy
    lowest_ask = min(listings, key=lambda x: x["ask"])

    # Highest bid = sell
    highest_bid = max(listings, key=lambda x: x["bid"])

    # Ignore same exchange
    if lowest_ask["exchange"] == highest_bid["exchange"]:
        continue

    # Gross profit
    gross_profit = (
        (highest_bid["bid"] - lowest_ask["ask"]) / lowest_ask["ask"]
    ) * 100

    # Net profit
    net_profit = gross_profit - TRADING_FEE - WITHDRAWAL_BUFFER

    # Liquidity check
    min_volume = min(
        lowest_ask.get("baseVolume", 0),
        highest_bid.get("baseVolume", 0)
    )

    # Final validation
    if net_profit >= MIN_PROFIT and min_volume >= MIN_VOLUME:
        opportunities.append({
            "symbol": symbol,
            "buy_exchange": lowest_ask["exchange"].upper(),
            "buy_price": lowest_ask["ask"],
            "sell_exchange": highest_bid["exchange"].upper(),
            "sell_price": highest_bid["bid"],
            "profit": net_profit,
            "volume": min_volume
        })


# Sort
opportunities.sort(
    key=lambda x: (x["profit"], x["volume"]),
    reverse=True
)

# Summary
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"✅ Exchanges Successful: {exchange_success}")
print(f"❌ Exchanges Failed: {exchange_failed}")
print(f"🪙 Coins Scanned: {len(market_data)}")
print(f"💎 Opportunities Found: {len(opportunities)}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

# Results
if opportunities:
    print("🔥 TOP LIVE SPOT ARBITRAGE OPPORTUNITIES:\n")

    for i, opp in enumerate(opportunities[:100], 1):
        print(
            f"{i}. {opp['symbol']} | "
            f"BUY {opp['buy_exchange']} @ {opp['buy_price']:.8f} | "
            f"SELL {opp['sell_exchange']} @ {opp['sell_price']:.8f} | "
            f"NET {opp['profit']:.2f}% | "
            f"VOL {opp['volume']:.2f}"
        )

else:
    print("❌ No profitable arbitrage opportunities found.")


# CSV Export
try:
    with open("arbimine_opportunities.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "symbol",
                "buy_exchange",
                "buy_price",
                "sell_exchange",
                "sell_price",
                "profit",
                "volume"
            ]
        )

        writer.writeheader()
        writer.writerows(opportunities)

    print("\n📁 CSV Exported Successfully")

except Exception as e:
    print(f"\n✗ CSV Export Failed: {str(e)[:80]}")


# End
print(f"\n⚡ Scan Duration: {datetime.now() - start_time}")
print("🔥 ARBIMINE GITHUB FIXED COMPLETE")