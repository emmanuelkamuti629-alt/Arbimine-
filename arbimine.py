import ccxt
import threading
import time
from datetime import datetime
from flask import Flask, jsonify, render_template_string

# =========================
# CONFIG
# =========================

EXCHANGES = [
    'kucoin', 'okx', 'gateio', 'mexc', 'bitmart',
    'htx', 'bitfinex', 'bitstamp', 'phemex',
    'coinex', 'poloniex', 'lbank', 'ascendex',
    'bitrue', 'whitebit'
]

MIN_PROFIT = 1.0        # realistic minimum
MAX_PROFIT = 10.0       # cap unrealistic spikes
MIN_VOLUME = 50000
MAX_SYMBOLS = 400

FEE = 0.25              # avg trading fee %
WITHDRAWAL_COST = 0.30  # network + withdrawal estimate
SLIPPAGE = 0.40

BAD_WORDS = [
    'UP/', 'DOWN/', 'BULL', 'BEAR', '3L', '3S',
    'ELON', 'MAGA', 'DOGE', 'SHIB', 'PEPE'
]

# =========================
# GLOBAL STORAGE
# =========================

market_data = {}
opportunities = []

# =========================
# EXCHANGE SCANNER
# =========================

def scan_exchange(name):
    try:
        if not hasattr(ccxt, name):
            return

        ex = getattr(ccxt, name)({
            "enableRateLimit": True,
            "timeout": 20000
        })

        markets = ex.load_markets()
        tickers = ex.fetch_tickers()

        results = {}

        for symbol, t in tickers.items():
            if not symbol.endswith("/USDT"):
                continue

            if any(b in symbol.upper() for b in BAD_WORDS):
                continue

            if symbol not in markets:
                continue

            bid = t.get("bid")
            ask = t.get("ask")
            vol = t.get("quoteVolume") or 0

            if not bid or not ask or ask <= 0:
                continue

            if vol < 10000:
                continue

            results[symbol] = {
                "exchange": name,
                "bid": bid,
                "ask": ask,
                "volume": vol
            }

        market_data[name] = results
        print(f"✓ {name} loaded {len(results)} pairs")

    except Exception as e:
        print(f"✗ {name} error")


# =========================
# ANALYSIS ENGINE (REALISTIC)
# =========================

def analyze():
    global opportunities
    opportunities = []

    all_symbols = {}

    # merge all exchange data
    for ex, data in market_data.items():
        for sym, val in data.items():
            all_symbols.setdefault(sym, []).append(val)

    for sym, listings in all_symbols.items():
        if len(listings) < 2:
            continue

        for buy in listings:
            for sell in listings:

                if buy["exchange"] == sell["exchange"]:
                    continue

                buy_price = buy["ask"]
                sell_price = sell["bid"]

                if buy_price <= 0:
                    continue

                gross = ((sell_price - buy_price) / buy_price) * 100

                net = gross - FEE - FEE - WITHDRAWAL_COST - SLIPPAGE

                if net < MIN_PROFIT or net > MAX_PROFIT:
                    continue

                volume = min(buy["volume"], sell["volume"])

                if volume < MIN_VOLUME:
                    continue

                # AI-like scoring (simple realism model)
                score = net * (volume / 100000)

                opportunities.append({
                    "symbol": sym,
                    "buy": buy["exchange"],
                    "sell": sell["exchange"],
                    "buy_price": round(buy_price, 8),
                    "sell_price": round(sell_price, 8),
                    "profit": round(net, 2),
                    "volume": round(volume, 0),
                    "score": round(score, 2)
                })

    opportunities.sort(key=lambda x: x["score"], reverse=True)


# =========================
# BACKGROUND LOOP
# =========================

def worker():
    while True:
        print("\n🚀 Scanning market...")

        threads = []
        for ex in EXCHANGES:
            t = threading.Thread(target=scan_exchange, args=(ex,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        print("🔍 Analyzing opportunities...")
        analyze()

        print(f"💎 Found: {len(opportunities)} opportunities")

        time.sleep(15)  # refresh every 15 sec


# =========================
# FLASK DASHBOARD
# =========================

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ArbiMine Pro Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: Arial; background:#0f172a; color:white; padding:20px; }
        table { width:100%; border-collapse: collapse; }
        th, td { padding:10px; border-bottom:1px solid #333; }
        th { background:#1e293b; }
        .good { color:#00ff88; }
    </style>
</head>
<body>
    <h2>🚀 ARBIMINE PRO LIVE DASHBOARD</h2>
    <p>Real-time Arbitrage Scanner (Max 10% Profit Filter)</p>

    <table>
        <tr>
            <th>Symbol</th>
            <th>Buy</th>
            <th>Sell</th>
            <th>Profit %</th>
            <th>Volume</th>
            <th>Score</th>
        </tr>

        {% for o in data %}
        <tr>
            <td>{{o.symbol}}</td>
            <td>{{o.buy}} @ {{o.buy_price}}</td>
            <td>{{o.sell}} @ {{o.sell_price}}</td>
            <td class="good">{{o.profit}}%</td>
            <td>{{o.volume}}</td>
            <td>{{o.score}}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML, data=opportunities[:50])


@app.route("/api")
def api():
    return jsonify(opportunities[:50])


# =========================
# START SYSTEM
# =========================

if __name__ == "__main__":
    print("🚀 ARBIMINE PRO v3 STARTING...")
    threading.Thread(target=worker, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)