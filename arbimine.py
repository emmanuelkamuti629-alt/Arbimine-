import ccxt
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

print("🚀 ARBIMINE REALISTIC SCANNER STARTED")
print(f"⏰ Time: {datetime.now()}")
print("🌍 Scanning real USDT spot markets only\n")

# -----------------------------
# EXCHANGES (stable ones only)
# -----------------------------
exchange_ids = [
    'kucoin', 'okx', 'gateio', 'mexc', 'bitmart',
    'htx', 'bitfinex', 'bitstamp', 'phemex', 'coinex',
    'poloniex', 'lbank', 'ascendex', 'bitrue', 'whitebit'
]

# -----------------------------
# SETTINGS (REALISTIC)
# -----------------------------
MIN_PROFIT = 0.3
MAX_PROFIT = 10.0
MIN_VOLUME = 200000
MIN_PRICE = 0.00001
MAX_THREADS = 10

BAD_WORDS = ['UP/', 'DOWN/', 'BULL/', 'BEAR/', '3L/', '3S/']

EXCHANGE_FEES = {
    "kucoin": 0.20, "okx": 0.16, "gateio": 0.20, "mexc": 0.20,
    "bitmart": 0.25, "htx": 0.20, "bitfinex": 0.20, "bitstamp": 0.25,
    "phemex": 0.20, "coinex": 0.20, "poloniex": 0.25,
    "lbank": 0.20, "ascendex": 0.20, "bitrue": 0.20, "whitebit": 0.20
}

market_data = {}
results = []

# -----------------------------
# SCAN FUNCTION
# -----------------------------
def scan_exchange(ex_id):
    try:
        ex = getattr(ccxt, ex_id)({
            "enableRateLimit": True,
            "timeout": 30000,
            "options": {"defaultType": "spot"}
        })

        if not ex.has.get("fetchTickers"):
            return ex_id, {}, False

        markets = ex.load_markets()
        tickers = ex.fetch_tickers()

        data = {}

        for symbol, t in tickers.items():

            symbol = symbol.split(":")[0]

            if not symbol.endswith("/USDT"):
                continue

            if any(bad in symbol for bad in BAD_WORDS):
                continue

            if symbol not in markets:
                continue

            bid = t.get("bid")
            ask = t.get("ask")
            vol = t.get("quoteVolume") or t.get("baseVolume") or 0

            # -----------------------------
            # REAL DATA FILTERS
            # -----------------------------
            if not bid or not ask or bid <= 0 or ask <= 0:
                continue

            if ask < MIN_PRICE:
                continue

            if vol < MIN_VOLUME:
                continue

            data[symbol] = {
                "exchange": ex_id,
                "bid": bid,
                "ask": ask,
                "volume": vol
            }

        print(f"✓ {ex_id.upper()} | {len(data)} pairs")
        return ex_id, data, True

    except Exception as e:
        print(f"✗ {ex_id.upper()} failed")
        return ex_id, {}, False


# -----------------------------
# MULTI THREAD SCAN
# -----------------------------
with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    futures = [executor.submit(scan_exchange, e) for e in exchange_ids]

    for f in as_completed(futures):
        ex_id, data, ok = f.result()

        for sym, info in data.items():
            market_data.setdefault(sym, []).append(info)

# -----------------------------
# ANALYSIS ENGINE
# -----------------------------
print("\n🔍 ANALYZING REAL ARBITRAGE...\n")

for symbol, listings in market_data.items():

    if len(listings) < 2:
        continue

    for buy in listings:
        for sell in listings:

            if buy["exchange"] == sell["exchange"]:
                continue

            if buy["ask"] <= 0:
                continue

            gross = ((sell["bid"] - buy["ask"]) / buy["ask"]) * 100

            fee = EXCHANGE_FEES.get(buy["exchange"], 0.25) + \
                  EXCHANGE_FEES.get(sell["exchange"], 0.25)

            net = gross - fee

            # -----------------------------
            # STRICT REALISTIC FILTER
            # -----------------------------
            if (
                MIN_PROFIT <= net <= MAX_PROFIT and
                gross <= 10.0 and
                buy["volume"] > MIN_VOLUME and
                sell["volume"] > MIN_VOLUME
            ):
                results.append({
                    "symbol": symbol,
                    "buy": buy["exchange"],
                    "sell": sell["exchange"],
                    "buy_price": buy["ask"],
                    "sell_price": sell["bid"],
                    "profit": round(net, 2),
                    "volume": min(buy["volume"], sell["volume"])
                })

# -----------------------------
# SORT RESULTS
# -----------------------------
results.sort(key=lambda x: x["profit"], reverse=True)

# -----------------------------
# OUTPUT
# -----------------------------
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"🪙 Coins scanned: {len(market_data)}")
print(f"💎 Opportunities: {len(results)}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

if results:
    print("🔥 TOP REAL ARBITRAGE OPPORTUNITIES:\n")

    for i, r in enumerate(results[:50], 1):
        print(
            f"{i}. {r['symbol']} | "
            f"BUY {r['buy']} @ {r['buy_price']:.8f} | "
            f"SELL {r['sell']} @ {r['sell_price']:.8f} | "
            f"NET {r['profit']}% | "
            f"VOL {r['volume']:.0f}"
        )
else:
    print("❌ No real arbitrage opportunities found.")

print("\n🔥 ARBIMINE REALISTIC COMPLETE")