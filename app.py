# app.py - веб-сервер для Render
from flask import Flask
import os
import threading
import asyncio
import sys

app = Flask(__name__)

@app.route('/')
def home():
    return "🎣 Бот отчётов работает!"

@app.route('/health')
def health():
    return "OK", 200

# Импортируем и запускаем бота в фоне
def run_bot():
    try:
        # Добавляем путь к модулям
        sys.path.append(os.path.dirname(__file__))
        
        # Импортируем и запускаем бота
        from fishing_slavyansk_report_bot import main
        
        # Запускаем бота
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Ошибка бота: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)