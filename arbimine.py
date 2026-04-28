import ccxt
import threading
import time
from datetime import datetime
from flask import Flask, render_template_string
from concurrent.futures import ThreadPoolExecutor, as_completed

# =========================
# CONFIG
# =========================

exchange_ids = [
    'kucoin', 'okx', 'gateio', 'mexc', 'bitmart',
    'htx', 'bitfinex', 'bitstamp', 'phemex', 'coinex',
    'poloniex', 'lbank', 'ascendex', 'bitrue', 'whitebit'
]

MIN_PROFIT = 0.30
MAX_PROFIT = 10.0   # ✅ FINAL LIMIT
MIN_VOLUME = 200000
SLIPPAGE = 0.20
WITHDRAWAL = 0.30
MAX_THREADS = 10

BAD_WORDS = ['UP/', 'DOWN/', 'BULL/', 'BEAR/', '3L/', '3S/', 'ELON', 'TROLL']

EXCHANGE_FEES = {
    "kucoin": 0.20, "okx": 0.16, "gateio": 0.20, "mexc": 0.20,
    "bitmart": 0.25, "htx": 0.20, "bitfinex": 0.20, "bitstamp": 0.25,
    "phemex": 0.20, "coinex": 0.20, "poloniex": 0.25,
    "lbank": 0.20, "ascendex": 0.20, "bitrue": 0.20, "whitebit": 0.20
}

market_data = {}
results_final = []

# =========================
# AI SCORING ENGINE
# =========================

def ai_score(r):
    score = 0

    # profit logic (REALISTIC)
    if 0.3 <= r["profit"] <= 1.0:
        score += 45
    elif 1.0 < r["profit"] <= 3.0:
        score += 30
    elif 3.0 < r["profit"] <= 6.0:
        score += 15
    else:
        score += 5

    # liquidity
    if r["volume"] > 1_000_000:
        score += 30
    elif r["volume"] > 300_000:
        score += 20
    else:
        score += 5

    # trusted exchanges boost
    safe = ["BINANCE", "OKX", "KUCOIN", "GATEIO", "KRAKEN"]
    if r["buy"].upper() in safe:
        score += 10
    if r["sell"].upper() in safe:
        score += 10

    # penalty for micro coins
    if r["buy_price"] < 0.00001:
        score -= 30

    return max(0, min(100, score))


# =========================
# SCANNER
# =========================

def scan_exchange(ex_id):
    try:
        ex = getattr(ccxt, ex_id)({
            "enableRateLimit": True,
            "timeout": 30000,
            "options": {"defaultType": "spot"}
        })

        markets = ex.load_markets()

        if not ex.has.get("fetchTickers"):
            return ex_id, {}, False

        tickers = ex.fetch_tickers()
        results = {}

        for sym, t in tickers.items():

            symbol = sym.split(":")[0]

            if not symbol.endswith("/USDT"):
                continue

            if any(x in symbol for x in BAD_WORDS):
                continue

            if sym not in markets:
                continue

            bid = t.get("bid")
            ask = t.get("ask")

            if not bid or not ask or ask <= 0:
                continue

            spread = ((ask - bid) / ask) * 100

            # remove fake spreads
            if spread > 3:
                continue

            volume = t.get("quoteVolume") or t.get("baseVolume") or 0

            if symbol not in results or volume > results[symbol]["volume"]:
                results[symbol] = {
                    "exchange": ex_id,
                    "bid": bid,
                    "ask": ask,
                    "volume": volume
                }

        return ex_id, results, True

    except:
        return ex_id, {}, False


# =========================
# BACKGROUND SCANNER
# =========================

def run_scanner():
    global results_final, market_data

    while True:

        market_data = {}
        temp = []

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(scan_exchange, e) for e in exchange_ids]

            for f in as_completed(futures):
                ex_id, data, _ = f.result()

                for sym, info in data.items():
                    market_data.setdefault(sym, []).append(info)

        # ANALYSIS
        for symbol, listings in market_data.items():

            if len(listings) < 2:
                continue

            for buy in listings:
                for sell in listings:

                    if buy["exchange"] == sell["exchange"]:
                        continue

                    gross = ((sell["bid"] - buy["ask"]) / buy["ask"]) * 100

                    fee = EXCHANGE_FEES.get(buy["exchange"], 0.25) + \
                          EXCHANGE_FEES.get(sell["exchange"], 0.25)

                    net = gross - fee - SLIPPAGE - WITHDRAWAL

                    vol = min(buy["volume"], sell["volume"])

                    if (
                        MIN_PROFIT <= net <= MAX_PROFIT and
                        vol >= MIN_VOLUME
                    ):
                        temp.append({
                            "symbol": symbol,
                            "buy": buy["exchange"],
                            "sell": sell["exchange"],
                            "buy_price": buy["ask"],
                            "sell_price": sell["bid"],
                            "profit": round(net, 2),
                            "volume": vol
                        })

        # AI scoring
        for r in temp:
            r["ai"] = ai_score(r)

        temp.sort(key=lambda x: (x["ai"], x["profit"]), reverse=True)

        results_final = temp[:50]

        time.sleep(10)


# =========================
# DASHBOARD
# =========================

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>ArbiMine AI Dashboard</title>
<meta http-equiv="refresh" content="5">
<style>
body {background:#0f0f0f;color:#00ff99;font-family:Arial}
table {width:100%;border-collapse:collapse}
th,td {padding:10px;border-bottom:1px solid #333;text-align:center}
th {color:white}
</style>
</head>
<body>

<h2>🚀 ARBIMINE AI LIVE DASHBOARD</h2>

<table>
<tr>
<th>Symbol</th>
<th>Buy</th>
<th>Sell</th>
<th>Profit %</th>
<th>AI Score</th>
<th>Volume</th>
</tr>

{% for r in data %}
<tr>
<td>{{r.symbol}}</td>
<td>{{r.buy}}</td>
<td>{{r.sell}}</td>
<td>{{r.profit}}%</td>
<td>{{r.ai}}</td>
<td>{{r.volume}}</td>
</tr>
{% endfor %}

</table>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML, data=results_final)


# =========================
# RUN SYSTEM
# =========================

if __name__ == "__main__":

    t = threading.Thread(target=run_scanner)
    t.daemon = True
    t.start()

    app.run(host="0.0.0.0", port=5000, debug=True)