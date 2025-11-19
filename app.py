from flask import Flask, request
import requests

app = Flask(__name__)

BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

@app.get("/")
def home():
    return "Server Alive", 200

@app.post("/webhook")
def webhook():
    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]

        # TEMP: bot replies with echo
        requests.post(TELEGRAM_URL, json={
            "chat_id": chat_id,
            "text": f"Received: {text}"
        })

    return "OK", 200

if __name__ == "__main__":
    app.run()
