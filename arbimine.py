import ccxt
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

start_time = datetime.now()

print("🚀 ARBIMINE ULTIMATE - PRODUCTION REALISTIC SCANNER")
print(f"⏰ Scan Time: {start_time}")
print("📊 REAL market arbitrage only (no fake spikes)\n")

exchange_ids = [
    'kucoin', 'okx', 'gateio', 'mexc', 'bitmart',
    'htx', 'bitfinex', 'bitstamp', 'phemex', 'coinex',
    'poloniex', 'lbank', 'ascendex', 'bitrue', 'whitebit'
]

# =========================
# REALISTIC SETTINGS
# =========================
MIN_PROFIT = 0.3
MAX_PROFIT = 10.0
MIN_VOLUME = 50000
MAX_THREADS = 10
MAX_SPREAD = 3.0

BAD_WORDS = [
    'UP/', 'DOWN/', 'BULL/', 'BEAR/', '3L/', '3S/',
    'ELON','TROLL','MAGA','BOBO','HOLD','MOG','DOG','SHIB'
]

EXCHANGE_FEES = {
    "kucoin": 0.20, "okx": 0.16, "gateio": 0.20, "mexc": 0.20,
    "bitmart": 0.25, "htx": 0.20, "bitfinex": 0.20, "bitstamp": 0.25,
    "phemex": 0.20, "coinex": 0.20, "poloniex": 0.25,
    "lbank": 0.20, "ascendex": 0.20, "bitrue": 0.20, "whitebit": 0.20
}

market_data = {}
results = []

# =========================
# SCAN EXCHANGE
# =========================
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

        output = {}

        for symbol, t in tickers.items():

            # FIX: no split() corruption
            symbol = symbol.replace(":USDT", "")

            if not symbol.endswith("/USDT"):
                continue

            if any(b in symbol.upper() for b in BAD_WORDS):
                continue

            if symbol not in markets:
                continue

            bid = t.get("bid")
            ask = t.get("ask")
            vol = t.get("quoteVolume") or 0

            # REAL MARKET VALIDATION
            if not bid or not ask:
                continue

            if bid <= 0 or ask <= 0:
                continue

            if ask <= bid:
                continue

            spread = ((ask - bid) / ask) * 100
            if spread > MAX_SPREAD:
                continue

            if vol < MIN_VOLUME:
                continue

            output[symbol] = {
                "exchange": ex_id,
                "bid": bid,
                "ask": ask,
                "volume": vol
            }

        print(f"✓ {ex_id.upper()} | {len(output)} pairs")
        return ex_id, output, True

    except:
        return ex_id, {}, False


# =========================
# PARALLEL SCAN
# =========================
with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    futures = [executor.submit(scan_exchange, e) for e in exchange_ids]

    for f in as_completed(futures):
        ex_id, data, ok = f.result()

        for sym, info in data.items():
            market_data.setdefault(sym, []).append(info)


# =========================
# ARBITRAGE ENGINE
# =========================
print("\n🔍 ANALYZING REAL ARBITRAGE...\n")

for symbol, listings in market_data.items():

    if len(listings) < 2:
        continue

    for buy in listings:
        for sell in listings:

            if buy["exchange"] == sell["exchange"]:
                continue

            if sell["bid"] <= buy["ask"]:
                continue

            gross = ((sell["bid"] - buy["ask"]) / buy["ask"]) * 100

            fee = (
                EXCHANGE_FEES.get(buy["exchange"], 0.25) +
                EXCHANGE_FEES.get(sell["exchange"], 0.25)
            )

            net = gross - fee

            volume = min(buy["volume"], sell["volume"])

            if (
                MIN_PROFIT <= net <= MAX_PROFIT and
                volume >= MIN_VOLUME
            ):
                results.append({
                    "symbol": symbol,
                    "buy": buy["exchange"],
                    "sell": sell["exchange"],
                    "buy_price": buy["ask"],
                    "sell_price": sell["bid"],
                    "profit": round(net, 2),
                    "volume": int(volume)
                })


# =========================
# SORT + CLEAN
# =========================
results.sort(key=lambda x: x["profit"], reverse=True)

unique = []
seen = set()

for r in results:
    key = (r["symbol"], r["buy"], r["sell"])
    if key not in seen:
        seen.add(key)
        unique.append(r)


# =========================
# OUTPUT
# =========================
print("=" * 70)
print(f"🪙 Coins scanned: {len(market_data)}")
print(f"💎 Real opportunities: {len(unique)}")
print("=" * 70)

if unique:
    print("\n🔥 REAL ARBITRAGE OPPORTUNITIES:\n")

    for i, r in enumerate(unique[:50], 1):
        print(
            f"{i}. {r['symbol']} | "
            f"BUY {r['buy']} @ {r['buy_price']:.6f} | "
            f"SELL {r['sell']} @ {r['sell_price']:.6f} | "
            f"NET {r['profit']}% | "
            f"VOL {r['volume']:,}"
        )
else:
    print("❌ No real arbitrage opportunities right now")

# =========================
# CSV EXPORT
# =========================
try:
    with open("arbimine_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["symbol","buy","buy_price","sell","sell_price","profit","volume"]
        )
        writer.writeheader()
        writer.writerows(unique)

    print("\n📁 Saved: arbimine_results.csv")

except Exception as e:
    print(f"\n❌ CSV error: {e}")

print(f"\n⚡ Finished in: {datetime.now() - start_time}")
print("🔥 ARBIMINE PRODUCTION COMPLETE")