from flask import Flask, render_template_string
import ccxt
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

EXCHANGES = ['kucoin', 'okx', 'gateio', 'mexc', 'bitmart', 'htx', 'bitfinex', 'bitstamp', 'phemex']
MIN_PROFIT = 0.3
MAX_PROFIT = 10.0
MIN_VOLUME = 50000
FEE = 0.25
BAD = {'ELON', 'TROLL', 'SHIB', 'DOGE'}

opportunities = []

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ArbiMine - Live Arbitrage Scanner</title>
    <meta http-equiv="refresh" content="30">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background:#0a0a0a; color:#00ff88; font-family:Arial; padding:20px; }
        h1 { text-align:center; }
        table { width:100%; border-collapse:collapse; }
        th, td { padding:10px; border-bottom:1px solid #333; text-align:left; }
        .profit-high { color:#00ff88; }
        .profit-mid { color:#ffcc00; }
        .profit-low { color:#ff8800; }
        .stats { display:flex; gap:20px; justify-content:center; margin-bottom:20px; }
        .stat-card { background:#1a1a2e; padding:15px; border-radius:10px; text-align:center; }
    </style>
</head>
<body>
    <h1>🚀 ArbiMine Live Scanner</h1>
    <div class="stats">
        <div class="stat-card">💎 Opportunities: {{ opportunities|length }}</div>
        <div class="stat-card">🔄 Auto-refresh: 30s</div>
    </div>
    <div style="overflow-x:auto;">
        <table>
            <tr><th>#</th><th>Coin</th><th>Buy</th><th>Sell</th><th>Profit%</th><th>Volume</th></tr>
            {% for opp in opportunities[:50] %}
            <tr>
                <td>{{ loop.index }}</td>
                <td><strong>{{ opp.symbol }}</strong></td>
                <td style="color:#ff6666">{{ opp.buy }}</td>
                <td style="color:#66ff66">{{ opp.sell }}</td>
                <td class="profit-{{ 'high' if opp.profit > 5 else 'mid' if opp.profit > 2 else 'low' }}">{{ opp.profit }}%</td>
                <td>${{ "{:,}".format(opp.volume) }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

def scan_exchange(ex_id):
    try:
        ex = getattr(ccxt, ex_id)({"enableRateLimit": True, "timeout": 20000})
        tickers = ex.fetch_tickers()
        out = {}
        for sym, t in tickers.items():
            symbol = sym.split(":")[0]
            if not symbol.endswith("/USDT"):
                continue
            if any(b in symbol.upper() for b in BAD):
                continue
            bid = t.get("bid")
            ask = t.get("ask")
            if not bid or not ask:
                continue
            vol = t.get("quoteVolume") or 0
            if vol < MIN_VOLUME:
                continue
            out[symbol] = {"exchange": ex_id, "bid": bid, "ask": ask, "volume": vol}
        return ex_id, out, True
    except:
        return ex_id, {}, False

def scan():
    global opportunities
    market_data = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(scan_exchange, e) for e in EXCHANGES]
        for f in as_completed(futures):
            ex_id, data, ok = f.result()
            for sym, info in data.items():
                market_data.setdefault(sym, []).append(info)
    
    results = []
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
                net = gross - (FEE * 2)
                vol = min(buy["volume"], sell["volume"])
                if MIN_PROFIT <= net <= MAX_PROFIT and vol >= MIN_VOLUME:
                    results.append({
                        "symbol": symbol, "buy": buy["exchange"], "sell": sell["exchange"],
                        "profit": round(net, 2), "volume": int(vol)
                    })
    results.sort(key=lambda x: x["profit"], reverse=True)
    seen = set()
    opportunities = []
    for r in results:
        key = (r["symbol"], r["buy"], r["sell"])
        if key not in seen:
            seen.add(key)
            opportunities.append(r)

@app.route("/")
def home():
    return render_template_string(HTML, opportunities=opportunities)

if __name__ == "__main__":
    scan()
    app.run(host="0.0.0.0", port=5000)
