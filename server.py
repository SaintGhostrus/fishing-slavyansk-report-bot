# server.py - веб-сервер для Render
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "🎣 Бот работает!"

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"✅ Веб-сервер на порту {port}")
    app.run(host='0.0.0.0', port=port)