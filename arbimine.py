import ccxt
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

start_time = datetime.now()

print("🚀 ARBIMINE ULTIMATE PRO STARTED")
print(f"⏰ Scan Time: {start_time}")
print("🌍 Cross-Exchange Spot Arbitrage Scanner (GitHub Safe)\n")

# Stable exchanges (GitHub-friendly)
exchange_ids = [
    'kucoin', 'okx', 'gateio', 'mexc', 'bitmart',
    'htx', 'bitfinex', 'bitstamp', 'phemex', 'coinex',
    'poloniex', 'lbank', 'ascendex', 'bitrue', 'whitebit'
]

# Settings
MIN_PROFIT = 0.5
MAX_PROFIT = 25
WITHDRAWAL_BUFFER = 0.50
SLIPPAGE_BUFFER = 0.20
MIN_VOLUME = 50000
STALE_SECONDS = 300
MAX_THREADS = min(20, len(exchange_ids))

BAD_WORDS = ['UP/', 'DOWN/', 'BULL/', 'BEAR/', '3L/', '3S/']

EXCHANGE_FEES = {
    "kucoin": 0.20, "okx": 0.16, "gateio": 0.20, "mexc": 0.20,
    "bitmart": 0.25, "htx": 0.20, "bitfinex": 0.20, "bitstamp": 0.25,
    "phemex": 0.20, "coinex": 0.20, "poloniex": 0.25,
    "lbank": 0.20, "ascendex": 0.20, "bitrue": 0.20, "whitebit": 0.20
}

market_data = {}
exchange_success = 0
exchange_failed = 0


def scan_exchange(ex_id):
    results = {}

    try:
        if not hasattr(ccxt, ex_id):
            return ex_id, {}, False

        exchange = getattr(ccxt, ex_id)({
            "enableRateLimit": True,
            "timeout": 30000,
            "options": {"defaultType": "spot"}
        })

        markets = exchange.load_markets()

        if not exchange.has.get("fetchTickers"):
            return ex_id, {}, False

        try:
            tickers = exchange.fetch_tickers()
        except:
            tickers = {}
            priority = sorted(
                [s for s in markets if "USDT" in s and markets[s].get("active", True)],
                key=lambda x: markets[x].get("spot", False),
                reverse=True
            )[:300]

            for symbol in priority:
                try:
                    tickers[symbol] = exchange.fetch_ticker(symbol)
                except:
                    continue

        for raw_symbol, ticker in tickers.items():

            symbol = raw_symbol.split(":")[0]

            if not symbol.endswith("/USDT"):
                continue

            if any(x in symbol for x in BAD_WORDS):
                continue

            if raw_symbol not in markets:
                continue

            if not markets[raw_symbol].get("spot", False):
                continue

            bid = ticker.get("bid")
            ask = ticker.get("ask")

            if not bid or not ask or ask <= 0 or bid <= 0:
                continue

            # spread filter
            spread = ((ask - bid) / ask) * 100
            if spread > 5:
                continue

            # timestamp safety
            timestamp = ticker.get("timestamp")
            if timestamp:
                if timestamp < 10**12:
                    timestamp *= 1000
                age = (datetime.now().timestamp() * 1000 - timestamp) / 1000
                if age > STALE_SECONDS:
                    continue

            volume = ticker.get("quoteVolume") or ticker.get("baseVolume") or 0

            # overwrite protection (keep best liquidity)
            if symbol not in results or volume > results[symbol]["baseVolume"]:
                results[symbol] = {
                    "exchange": ex_id,
                    "bid": bid,
                    "ask": ask,
                    "baseVolume": volume
                }

        print(f"✓ {ex_id.upper()} | {len(results)} pairs")
        return ex_id, results, True

    except Exception as e:
        print(f"✗ {ex_id.upper()} failed: {str(e)[:120]}")
        return ex_id, {}, False


# Scan exchanges in parallel
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


print("\n🔍 ANALYZING CROSS-EXCHANGE ARBITRAGE...\n")

opportunities = []

for symbol, listings in market_data.items():

    if len(listings) < 2:
        continue

    for buy in listings:
        for sell in listings:

            if buy["exchange"] == sell["exchange"]:
                continue

            gross = ((sell["bid"] - buy["ask"]) / buy["ask"]) * 100

            buy_fee = EXCHANGE_FEES.get(buy["exchange"], 0.25)
            sell_fee = EXCHANGE_FEES.get(sell["exchange"], 0.25)

            net = gross - buy_fee - sell_fee - WITHDRAWAL_BUFFER - SLIPPAGE_BUFFER

            if net > MAX_PROFIT:
                continue

            min_vol = min(buy.get("baseVolume", 0), sell.get("baseVolume", 0))

            if net >= MIN_PROFIT and min_vol >= MIN_VOLUME:
                opportunities.append({
                    "symbol": symbol,
                    "buy_exchange": buy["exchange"].upper(),
                    "buy_price": buy["ask"],
                    "sell_exchange": sell["exchange"].upper(),
                    "sell_price": sell["bid"],
                    "profit": net,
                    "volume": min_vol
                })


# Sort best first
opportunities.sort(key=lambda x: (x["profit"], x["volume"]), reverse=True)

# Remove duplicates
seen = set()
unique = []

for opp in opportunities:
    key = (opp["symbol"], opp["buy_exchange"], opp["sell_exchange"])
    if key not in seen:
        seen.add(key)
        unique.append(opp)


# Summary
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"✅ Exchanges OK: {exchange_success}")
print(f"❌ Exchanges Failed: {exchange_failed}")
print(f"🪙 Coins Scanned: {len(market_data)}")
print(f"💎 Opportunities: {len(unique)}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

# Results
if unique:
    print("🔥 TOP ARBITRAGE OPPORTUNITIES:\n")
    for i, o in enumerate(unique[:100], 1):
        print(
            f"{i}. {o['symbol']} | BUY {o['buy_exchange']} @ {o['buy_price']:.8f} "
            f"| SELL {o['sell_exchange']} @ {o['sell_price']:.8f} "
            f"| NET {o['profit']:.2f}% | VOL {o['volume']:.2f}"
        )
else:
    print("❌ No profitable opportunities found.")


# CSV export
with open("arbimine_results.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["symbol","buy_exchange","buy_price","sell_exchange","sell_price","profit","volume"]
    )
    writer.writeheader()
    writer.writerows(unique)


print(f"\n⚡ Duration: {datetime.now() - start_time}")
print("🔥 ARBIMINE COMPLETE")