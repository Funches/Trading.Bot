# main.py
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volume import OnBalanceVolumeIndicator
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import requests
from polygon import RESTClient
from bs4 import BeautifulSoup
import time
import datetime

API_KEY = 'CJqpwB7cfkSNZppRiFIptFtZNM_Pj55F'
client = RESTClient(API_KEY)

STOCK = "SPY"
LOOKBACK_DAYS = 60
DISCORD_WEBHOOK = "YOUR_DISCORD_WEBHOOK"

def fetch_data():
    try:
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=2)

        aggs = client.get_aggs(
            ticker=STOCK,
            multiplier=1,
            timespan="minute",
            from_=start_date.strftime("%Y-%m-%d"),
            to=end_date.strftime("%Y-%m-%d"),
            limit=5000
        )

        df = pd.DataFrame([{
            "timestamp": datetime.datetime.fromtimestamp(bar.timestamp / 1000),
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume
        } for bar in aggs])
        
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)
        return df

    except Exception as e:
        print("Error fetching data from Polygon:", e)
        return None

def add_technical_indicators(df):
    df["rsi"] = RSIIndicator(close=df["close"]).rsi()
    df["macd"] = MACD(close=df["close"]).macd_diff()
    df["sma"] = SMAIndicator(close=df["close"], window=20).sma_indicator()
    df["obv"] = OnBalanceVolumeIndicator(close=df["close"], volume=df["volume"]).on_balance_volume()
    df.dropna(inplace=True)
    return df

def get_news_sentiment():
    url = f"https://www.google.com/search?q={STOCK}+stock+news&hl=en"
    headers = {"User-Agent": "Mozilla/5.0"}
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, "html.parser")
    headlines = soup.find_all("div", class_="BNeawe vvjwJb AP7Wnd")
    
    if not headlines:
        return 0

    sentiment = 0
    for h in headlines[:5]:
        text = h.get_text()
        if "drop" in text.lower() or "lawsuit" in text.lower() or "misses" in text.lower():
            sentiment -= 1
        elif "soars" in text.lower() or "beats" in text.lower() or "rally" in text.lower():
            sentiment += 1
    return sentiment

def train_ml_model(df):
    features = df[["rsi", "macd", "sma", "obv"]]
    target = (df["close"].shift(-1) > df["close"]).astype(int)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, target, test_size=0.2)
    clf = RandomForestClassifier(n_estimators=100)
    clf.fit(X_train, y_train)
    return clf, scaler

def make_prediction(model, scaler, df):
    latest = df.iloc[-1][["rsi", "macd", "sma", "obv"]].values.reshape(1, -1)
    scaled = scaler.transform(latest)
    return model.predict(scaled)[0]

def send_alert(message):
    if DISCORD_WEBHOOK != "YOUR_DISCORD_WEBHOOK":
        requests.post(DISCORD_WEBHOOK, json={"content": message})

def main():
    print(f"✅ [{datetime.datetime.now()}] Bot Started")
    while True:
        try:
            df = fetch_data()
            if df is None:
                continue
            
            df = add_technical_indicators(df)
            news_score = get_news_sentiment()
            model, scaler = train_ml_model(df)
            signal = make_prediction(model, scaler, df)

            action = "🟢 BUY" if signal == 1 and news_score >= 0 else "🔴 SELL"
            price = df.iloc[-1]["close"]
            print(f"[{datetime.datetime.now()}] Signal: {action} @ {price:.2f} | News score: {news_score}")
            send_alert(f"{action} {STOCK} @ {price:.2f} | News score: {news_score}")
        
        except Exception as e:
            print("⚠️ Error:", e)
        
        time.sleep(60)

if __name__ == "__main__":
    main()
