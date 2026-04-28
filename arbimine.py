import ccxt
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

start_time = datetime.now()

print("🚀 ARBIMINE FINAL PRODUCTION SCANNER")
print(f"⏰ {start_time}")
print("📊 REAL ARBITRAGE ONLY (STABLE MODE)\n")

EXCHANGES = [
    'kucoin', 'okx', 'gateio', 'mexc', 'bitmart',
    'htx', 'bitfinex', 'bitstamp', 'phemex',
    'coinex', 'poloniex', 'lbank', 'ascendex',
    'bitrue', 'whitebit'
]

# =====================
# SETTINGS
# =====================
MIN_PROFIT = 0.3
MAX_PROFIT = 10.0
MIN_VOLUME = 50000
MAX_THREADS = 10
MAX_SPREAD = 2.5
MAX_AGE_SEC = 180

FEE = 0.25

BAD = set([
    'UP', 'DOWN', 'BULL', 'BEAR', '3L', '3S',
    'ELON','TROLL','MAGA','SHIB','DOGE','PEPE'
])

market = {}
results = []

# =====================
# SCAN EXCHANGE
# =====================
def scan(ex_id):
    try:
        ex = getattr(ccxt, ex_id)({
            "enableRateLimit": True,
            "timeout": 20000,
            "options": {"defaultType": "spot"}
        })

        if not ex.has.get("fetchTickers"):
            return ex_id, {}, False

        markets = ex.load_markets()
        tickers = ex.fetch_tickers()

        out = {}

        for sym, t in tickers.items():

            # normalize symbol
            symbol = sym.split(":")[0]

            if not symbol.endswith("/USDT"):
                continue

            if any(b in symbol.upper() for b in BAD):
                continue

            if sym not in markets:
                continue

            bid = t.get("bid")
            ask = t.get("ask")

            if not bid or not ask or bid <= 0 or ask <= 0:
                continue

            if ask <= bid:
                continue

            # spread filter (important)
            spread = ((ask - bid) / ask) * 100
            if spread > MAX_SPREAD:
                continue

            # volume filter
            vol = t.get("quoteVolume") or 0
            if vol < MIN_VOLUME:
                continue

            # timestamp validation (VERY IMPORTANT)
            ts = t.get("timestamp")
            if ts:
                age = (time.time() * 1000 - ts) / 1000
                if age > MAX_AGE_SEC:
                    continue

            # keep best snapshot
            out[symbol] = {
                "exchange": ex_id,
                "bid": bid,
                "ask": ask,
                "volume": vol
            }

        print(f"✓ {ex_id.upper()} | {len(out)} pairs")
        return ex_id, out, True

    except:
        return ex_id, {}, False


# =====================
# PARALLEL SCAN
# =====================
with ThreadPoolExecutor(max_workers=MAX_THREADS) as ex:
    futures = [ex.submit(scan, e) for e in EXCHANGES]

    for f in as_completed(futures):
        ex_id, data, ok = f.result()

        for s, info in data.items():
            market.setdefault(s, []).append(info)


# =====================
# ARBITRAGE ENGINE
# =====================
print("\n🔍 ANALYZING...\n")

for symbol, lst in market.items():

    if len(lst) < 2:
        continue

    for buy in lst:
        for sell in lst:

            if buy["exchange"] == sell["exchange"]:
                continue

            if sell["bid"] <= buy["ask"]:
                continue

            gross = ((sell["bid"] - buy["ask"]) / buy["ask"]) * 100
            net = gross - (FEE * 2)

            vol = min(buy["volume"], sell["volume"])

            if MIN_PROFIT <= net <= MAX_PROFIT and vol >= MIN_VOLUME:
                results.append({
                    "symbol": symbol,
                    "buy": buy["exchange"],
                    "sell": sell["exchange"],
                    "buy_price": buy["ask"],
                    "sell_price": sell["bid"],
                    "profit": round(net, 2),
                    "volume": int(vol)
                })


# =====================
# SORT + CLEAN
# =====================
results.sort(key=lambda x: x["profit"], reverse=True)

seen = set()
final = []

for r in results:
    key = (r["symbol"], r["buy"], r["sell"])
    if key not in seen:
        seen.add(key)
        final.append(r)


# =====================
# OUTPUT
# =====================
print("=" * 70)
print(f"🪙 Coins: {len(market)}")
print(f"💎 Opportunities: {len(final)}")
print("=" * 70)

if final:
    print("\n🔥 REAL ARBITRAGE OPPORTUNITIES:\n")
    for i, r in enumerate(final[:50], 1):
        print(
            f"{i}. {r['symbol']} | "
            f"BUY {r['buy']} @ {r['buy_price']:.6f} | "
            f"SELL {r['sell']} @ {r['sell_price']:.6f} | "
            f"NET {r['profit']}% | "
            f"VOL {r['volume']:,}"
        )
else:
    print("❌ No realistic arbitrage right now")

# =====================
# SAVE CSV
# =====================
try:
    with open("arbimine_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["symbol","buy","sell","buy_price","sell_price","profit","volume"]
        )
        writer.writeheader()
        writer.writerows(final)

    print("\n📁 Saved: arbimine_results.csv")

except Exception as e:
    print(f"CSV error: {e}")

print(f"\n⚡ Done in {datetime.now() - start_time}")
print("🔥 ARBIMINE COMPLETE")